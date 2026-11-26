import { CORS, json, hmacHex, safeEqual } from '../_shared/net.ts';
import { admin } from '../_shared/db.ts';

// Called by the customer's phone right after Razorpay says "paid". The webhook does the same job
// independently, so an order is confirmed even if the customer closes the page.
Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS });
  if (req.method !== 'POST') return json({ error: 'Method not allowed' }, 405);
  try {
    const { order_id, razorpay_payment_id, razorpay_signature } = await req.json();
    const secret = Deno.env.get('RAZORPAY_KEY_SECRET');
    if (!secret) throw new Error('Payments are not set up yet');
    const db = admin();
    const { data: order } = await db.from('orders').select('id, status, razorpay_order_id, payment_status').eq('id', String(order_id)).maybeSingle();
    if (!order || !order.razorpay_order_id) return json({ error: 'Order not found' }, 404);
    const expected = await hmacHex(secret, order.razorpay_order_id + '|' + String(razorpay_payment_id));
    if (!safeEqual(expected, String(razorpay_signature))) return json({ error: 'Payment could not be verified' }, 400);
    if (order.status === 'awaiting_payment') {
      await db.from('orders').update({
        status: 'pending', payment_status: 'paid', razorpay_payment_id: String(razorpay_payment_id), paid_at: new Date().toISOString(),
      }).eq('id', order.id).eq('status', 'awaiting_payment');
    }
    return json({ ok: true });
  } catch (e) {
    return json({ error: (e as Error).message || 'Something went wrong' }, 400);
  }
});
