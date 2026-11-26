import { CORS, json, razorpay } from '../_shared/net.ts';
import { admin } from '../_shared/db.ts';

// Staff only: refunds a paid online order in full, after the staff member chooses to.
Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS });
  if (req.method !== 'POST') return json({ error: 'Method not allowed' }, 405);
  try {
    const token = (req.headers.get('authorization') || '').replace(/^Bearer\s+/i, '');
    const db = admin();
    const { data: u, error: ue } = await db.auth.getUser(token);   // the anon key is not a logged-in user, so it is refused here
    if (ue || !u?.user) return json({ error: 'Staff login required' }, 401);

    const { order_id } = await req.json();
    const { data: order } = await db.from('orders').select('id, total, payment_status, razorpay_payment_id, order_no, brand').eq('id', String(order_id)).maybeSingle();
    if (!order) return json({ error: 'Order not found' }, 404);
    const { data: prof } = await db.from('profiles').select('role, outlet').eq('id', u.user.id).maybeSingle();
    const allowed = prof && (prof.role === 'owner' || prof.outlet === (order.brand || 'Aricee'));
    if (!allowed) return json({ error: 'Not allowed to refund this outlet' }, 403);
    if (!['paid', 'needs_refund'].includes(order.payment_status) || !order.razorpay_payment_id) return json({ error: 'This order has no payment to refund' }, 400);

    // claim the refund first so a double tap cannot refund twice
    const { data: claimed } = await db.from('orders').update({ payment_status: 'refunding' }).eq('id', order.id).eq('payment_status', order.payment_status).select('id');
    if (!claimed || claimed.length === 0) return json({ error: 'Refund already in progress' }, 409);
    try {
      const r = await razorpay('/payments/' + order.razorpay_payment_id + '/refund', {
        amount: Math.round(Number(order.total) * 100), speed: 'normal',
        notes: { outlet: order.brand, order_no: String(order.order_no), refunded_by: u.user.email || '' },
      });
      await db.from('orders').update({ payment_status: 'refunded', refund_id: r.id, refunded_at: new Date().toISOString() }).eq('id', order.id);
      return json({ ok: true, refund_id: r.id });
    } catch (e) {
      await db.from('orders').update({ payment_status: order.payment_status }).eq('id', order.id);   // let staff try again
      throw e;
    }
  } catch (e) {
    return json({ error: (e as Error).message || 'Something went wrong' }, 400);
  }
});
