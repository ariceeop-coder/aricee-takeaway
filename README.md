# Aricee takeaway ordering + billing

- `index.html` – customer ordering page (QR code points here). No login.
- `staff.html` – staff portal: online order queue, accept/KOT/bill printing (RawBT or Bluetooth), menu editing, history. Staff login via Supabase.
- `SETUP.sql` – the whole Supabase database setup.

Host both files on GitHub Pages (Settings -> Pages -> main branch). Put your Supabase URL and anon key near the top of both files.

## Razorpay online payments (test mode first)
Edge functions in `supabase/functions` (create-order, verify-payment, razorpay-webhook, refund-order). Prices are always recalculated on the server.
1. Razorpay dashboard (Test mode) -> Settings -> API Keys -> generate keys.
2. Supabase -> Edge Functions -> Secrets: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` (never share these in chat or commit them).
3. Razorpay -> Webhooks -> URL `https://dgaurjpzgwyhwilhjowq.supabase.co/functions/v1/razorpay-webhook`, events `payment.captured` + `order.paid`, secret = RAZORPAY_WEBHOOK_SECRET. Keep auto-capture on.
4. In `menu-extras.js` set `"payments": { "online": true }`, commit, and test with Razorpay test UPI/cards.
5. For live: swap in Live keys and a Live webhook; then revoke anon execute on `place_order`.
