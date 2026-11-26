// Shared helpers for the payment functions (CORS, signatures, Razorpay calls).
export const CORS: Record<string, string> = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, apikey, content-type, x-client-info',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};
export function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { ...CORS, 'Content-Type': 'application/json' } });
}

/* ---------- signatures ---------- */
const enc = new TextEncoder();
export async function hmacHex(secret: string, message: string): Promise<string> {
  const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = new Uint8Array(await crypto.subtle.sign('HMAC', key, enc.encode(message)));
  return Array.from(sig).map((b) => b.toString(16).padStart(2, '0')).join('');
}
export function safeEqual(a: string, b: string): boolean {   // constant-time comparison
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let r = 0; for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}

/* ---------- Razorpay REST (secret key only ever lives in Supabase secrets) ---------- */
export async function razorpay(path: string, body: unknown): Promise<any> {
  const id = Deno.env.get('RAZORPAY_KEY_ID'), secret = Deno.env.get('RAZORPAY_KEY_SECRET');
  if (!id || !secret) throw new Error('Payments are not set up yet');
  const res = await fetch('https://api.razorpay.com/v1' + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: 'Basic ' + btoa(id + ':' + secret) },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error('Razorpay: ' + (data?.error?.description || res.status));
  return data;
}
