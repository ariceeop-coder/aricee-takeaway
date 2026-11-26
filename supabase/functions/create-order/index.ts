import { CORS, json, razorpay } from '../_shared/net.ts';
import { isOpen, priceOrder, OUTLETS } from '../_shared/pricing.ts';
import { admin } from '../_shared/db.ts';

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS });
  if (req.method !== 'POST') return json({ error: 'Method not allowed' }, 405);
  try {
    const body = await req.json();
    const brand = String(body.brand || ''); const method = body.method === 'online' ? 'online' : 'counter';
    if (!(brand in OUTLETS)) return json({ error: 'Unknown outlet' }, 400);
    if (!isOpen()) return json({ error: 'We are closed right now. Orders open daily from 11 AM to 11 PM.' }, 403);

    const db = admin();
    // simple abuse guard: too many unpaid online orders created in the last 5 minutes
    const since = new Date(Date.now() - 5 * 60 * 1000).toISOString();
    const { count } = await db.from('orders').select('id', { count: 'exact', head: true }).eq('status', 'awaiting_payment').gte('created_at', since);
    if ((count ?? 0) > 80) return json({ error: 'Too many requests right now, please try again in a minute.' }, 429);

    const { data: menu, error: me } = await db.from('menu_items').select('id, category, name, price, brand');
    if (me) throw new Error('Menu unavailable');
    const rows = (menu || []).filter((m: any) => (m.brand || 'Aricee') === 'Aricee');
    const priced = priceOrder(brand, body.items, rows as any);
    if (priced.paise < 100) return json({ error: 'Order total is too small' }, 400);

    const note = typeof body.note === 'string' ? body.note.slice(0, 200) : null;
    const { data: order, error: oe } = await db.from('orders').insert({
      brand, items: priced.items, subtotal: priced.total, discount_amt: 0, total: priced.total,
      status: method === 'online' ? 'awaiting_payment' : 'pending',
      payment_method: method, payment_status: 'unpaid', customer_note: note,
    }).select('id, order_no').single();
    if (oe || !order) throw new Error('Could not save your order');

    if (method === 'counter') return json({ order_id: order.id, order_no: order.order_no, method, total: priced.total });

    try {
      const rp = await razorpay('/orders', {
        amount: priced.paise, currency: 'INR', receipt: order.id,
        notes: { outlet: brand, order_id: order.id },
      });
      await db.from('orders').update({ razorpay_order_id: rp.id }).eq('id', order.id);
      return json({
        order_id: order.id, method, total: priced.total, amount: priced.paise,
        razorpay_order_id: rp.id, key_id: Deno.env.get('RAZORPAY_KEY_ID'),
      });
    } catch (e) {
      await db.from('orders').delete().eq('id', order.id);   // never leave a half-created order behind
      throw e;
    }
  } catch (e) {
    return json({ error: (e as Error).message || 'Something went wrong' }, 400);
  }
});
