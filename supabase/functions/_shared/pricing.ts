// Opening hours, happy hour and server-side price calculation.
import { X } from './extras.ts';

/* ---------- India time: opening hours and happy hour ---------- */
export function istHour(now: Date = new Date()): number {
  return Number(new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Kolkata', hour: '2-digit', hourCycle: 'h23' }).format(now));
}
export function isOpen(now: Date = new Date()): boolean {
  const h = istHour(now);
  return h >= X.hours.open && h < X.hours.close;
}
const HH_CATEGORIES = ['Lite Bites', 'Indus Wraps'];
const HH_TAG = ' (Happy Hour -50%)';
export function happyHourOn(now: Date = new Date()): boolean { const h = istHour(now); return h >= 16 && h < 19; }

/* ---------- price calculation (the server never trusts prices sent by the phone) ---------- */
export const OUTLETS: Record<string, number> = { Aricee: 0, Harlur: 10 };   // Harlur charges Rs 10 more per item

export type MenuRow = { id: string; category: string; name: string; price: number };
export type Line = { id: string; qty: number; mods?: string[] };

export function priceOrder(brand: string, lines: Line[], menuRows: MenuRow[], now: Date = new Date()) {
  if (!(brand in OUTLETS)) throw new Error('Unknown outlet');
  const add = OUTLETS[brand];
  if (!Array.isArray(lines) || lines.length === 0 || lines.length > 40) throw new Error('Your cart is empty or too large');
  const byId = new Map<string, MenuRow>();
  menuRows.forEach((m) => byId.set(m.id, { ...m, price: Number(m.price) }));
  (X.newItems || []).forEach((n: any) => { if (!byId.has(n.id)) byId.set(n.id, { id: n.id, category: n.category, name: n.name, price: Number(n.price) }); });
  const hh = happyHourOn(now);
  let total = 0; let totalQty = 0;
  const items = lines.map((l) => {
    const item = byId.get(String(l.id));
    if (!item || !(item.price > 0)) throw new Error('An item in your cart is no longer available');
    const qty = Number(l.qty);
    if (!Number.isInteger(qty) || qty < 1 || qty > 20) throw new Error('Invalid quantity');
    totalQty += qty; if (totalQty > 60) throw new Error('Too many items in one order');
    const groupKeys: string[] = (X.itemGroups[item.id] || []).filter((k: string) => X.groups[k]);
    const chosen = Array.isArray(l.mods) ? l.mods.map(String) : [];
    if (new Set(chosen).size !== chosen.length) throw new Error('Invalid options');
    const modLabels: string[] = []; let extra = 0; const used = new Set<string>();
    for (const key of groupKeys) {
      const g = X.groups[key];
      const picks = g.options.filter((o: any) => chosen.includes(o.id));
      if (g.type !== 'multi' && picks.length > 1) throw new Error('Please choose only one option for ' + g.title);
      if (g.required && picks.length === 0) throw new Error('Please choose: ' + g.title.replace(/^Choose your /, ''));
      for (const o of picks) {
        used.add(o.id);
        const p = Number(o.price) || 0; extra += p;
        const gname = g.title.replace(/^Choose your /, '').replace(/^./, (c: string) => c.toUpperCase());
        modLabels.push(gname + ': ' + o.name + (p ? ' (+' + p + ')' : ''));
      }
    }
    if (chosen.some((id) => !used.has(id))) throw new Error('Invalid options');
    const base = item.price + add;
    const onHH = hh && HH_CATEGORIES.includes(item.category);
    const unit = Math.round(((onHH ? Math.round(base * 50) / 100 : base) + extra) * 100) / 100;
    total += unit * qty;
    return { name: item.name + (onHH ? HH_TAG : ''), price: unit, qty, mods: modLabels };
  });
  total = Math.round(total * 100) / 100;
  return { items, total, paise: Math.round(total * 100) };
}

