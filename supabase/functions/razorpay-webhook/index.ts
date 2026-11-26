import { hmacHex, safeEqual } from '../_shared/net.ts';
import { admin } from '../_shared/db.ts';

// Razorpay calls this by itself when a payment succeeds. Only requests signed with the webhook secret are accepted.
Deno.serve(async (req) => {
  if (req.method !== 'POST') return new Response('Method not allowed', { status: 405 });
  const secret = Deno.env.get('RAZORPAY_WEBHOOK_SECRET');
  if (!secret) return new Response('Not configured', { status: 500 });
  const raw = await req.text();
  const sig = req.headers.get('x-razorpay-signature') || '';
  if (!safeEqual(await hmacHex(secret, raw), sig)) return new Response('Invalid signature', { status: 401 });

  try {
    const evt = JSON.parse(raw);
    if (evt.event === 'payment.captured' || evt.event === 'order.paid') {
      const pay = evt.payload?.payment?.entity;
      if (pay?.order_id && pay.status === 'captured') {
        const db = admin();
        const { data: order } = await db.from('orders').select('id, total, status').eq('razorpay_order_id', pay.order_id).maybeSingle();
        // only confirm when the paid amount matches what the server priced
        if (order && order.status === 'awaiting_payment' && pay.currency === 'INR' && Number(pay.amount) === Math.round(Number(order.total) * 100)) {
          await db.from('orders').update({
            status: 'pending', payment_status: 'paid', razorpay_payment_id: pay.id, paid_at: new Date().toISOString(),
          }).eq('id', order.id).eq('status', 'awaiting_payment');
        }
      }
    }
  } catch (_e) { /* a bad body must not make Razorpay retry forever */ }
  return new Response('ok');
});
