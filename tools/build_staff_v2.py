"""Builds the v2 staff pages (Aricee + Harlur) from the current staff.html / harlur/staff.html.
Usage:  python3 tools/build_staff_v2.py          -> test build in v2/ (separate local storage)
        python3 tools/build_staff_v2.py live      -> go-live build written over staff.html / harlur/staff.html
"""
import pathlib, re, sys
root = pathlib.Path(__file__).resolve().parent.parent
LIVE = len(sys.argv) > 1 and sys.argv[1] == 'live'

PRE = r"""
/* ---------- customisation data (must exist before the menu loads) ---------- */
const X = window.MENU_EXTRAS || { groups: {}, itemGroups: {}, info: {}, newItems: [] };
const OUTLET_BRAND = '__BRAND__', OUTLET_ADD = __ADD__;
function withNewItems(list) {
  const have = new Set(list.map(m => m.id));
  const add = (X.newItems || []).filter(n => !have.has(n.id))
    .map(n => ({ id: n.id, category: n.category, name: n.name, price: Number(n.price) + OUTLET_ADD, brand: OUTLET_BRAND }));
  return list.concat(add);
}
"""

CSS = """
  /* ---- item customisation popup ---- */
  .cz-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.55); z-index: 90; display: flex; align-items: flex-end; justify-content: center; }
  .cz-sheet { background: var(--surface); width: 100%; max-width: 560px; max-height: 92vh; border-radius: 18px 18px 0 0; display: flex; flex-direction: column; overflow: hidden; }
  .cz-head { padding: 16px 16px 8px; display: flex; gap: 10px; align-items: flex-start; }
  .cz-head h3 { margin: 0; font-size: 16.5px; font-weight: 800; line-height: 1.3; }
  .cz-head button { margin-left: auto; border: none; background: var(--surface-2); width: 30px; height: 30px; border-radius: 50%; font-size: 16px; cursor: pointer; color: var(--text); }
  .cz-body { overflow-y: auto; padding: 0 16px 10px; flex: 1; }
  .cz-group { border: 1px solid var(--line); border-radius: 12px; padding: 12px; margin-bottom: 10px; }
  .cz-group h4 { margin: 0 0 2px; font-size: 14px; font-weight: 800; }
  .cz-hint { font-size: 11.5px; color: var(--text-soft); margin-bottom: 6px; }
  .cz-hint b { color: #B23A2E; }
  .cz-opt { display: flex; align-items: center; gap: 10px; padding: 9px 0; border-top: 1px solid var(--line); font-size: 14px; cursor: pointer; }
  .cz-opt input { width: 18px; height: 18px; flex: none; accent-color: var(--orange); }
  .cz-opt .p { margin-left: auto; color: var(--text-soft); font-weight: 600; font-size: 13px; }
  .cz-err { color: #B23A2E; font-size: 12.5px; font-weight: 600; padding: 0 16px 6px; }
  .cz-foot { padding: 10px 16px 14px; border-top: 1px solid var(--line); display: flex; gap: 10px; align-items: center; }
  .cz-qty { display: flex; align-items: center; border: 1px solid var(--line); border-radius: 10px; height: 44px; }
  .cz-qty button { border: none; background: none; width: 36px; font-size: 19px; font-weight: 700; height: 42px; cursor: pointer; color: var(--text); }
  .cz-qty span { min-width: 20px; text-align: center; font-weight: 800; }
  .cz-add { flex: 1; height: 44px; border: none; border-radius: 10px; background: var(--orange); color: #fff; font-weight: 800; font-size: 14.5px; display: flex; justify-content: space-between; align-items: center; padding: 0 14px; cursor: pointer; font-family: inherit; }
"""

JS = r"""
/* ---------- item customisation (chutney, sundal, dal, gravy, extras, salads) ---------- */
function groupsFor(item) { return (X.itemGroups[item.id] || []).map(k => ({ key: k, ...X.groups[k] })).filter(g => g.options); }
function modStr(m) { return m.raw || (m.g + ': ' + m.n + (m.p ? ' (+' + m.p + ')' : '')); }
function lineKeyOf(c) { return c.key || c.itemId; }
const cz = { item: null, sel: {}, qty: 1, error: '' };
function czMods() {
  const out = [];
  groupsFor(cz.item).forEach(g => (cz.sel[g.key] || []).forEach(id => {
    const o = g.options.find(o => o.id === id);
    if (o) out.push({ g: g.title.replace(/^Choose your /, '').replace(/^./, c => c.toUpperCase()), n: o.name, p: Number(o.price) || 0, id });
  }));
  return out;
}
function openCustomize(item) {
  cz.item = item; cz.qty = 1; cz.error = ''; cz.sel = {};
  groupsFor(item).forEach(g => { cz.sel[g.key] = g.default ? [g.default] : []; });
  drawCustomize();
}
function closeCustomize() { cz.item = null; const r = document.getElementById('cz-root'); if (r) r.innerHTML = ''; }
function drawCustomize() {
  let root = document.getElementById('cz-root');
  if (!root) { root = document.createElement('div'); root.id = 'cz-root'; document.body.appendChild(root); }
  const body0 = root.querySelector('.cz-body'); const scroll = body0 ? body0.scrollTop : 0;
  const item = cz.item, groups = groupsFor(item);
  const unit = effectivePrice(item) + czMods().reduce((s, m) => s + m.p, 0);
  root.innerHTML = `
    <div class="cz-overlay" id="cz-ov"><div class="cz-sheet">
      <div class="cz-head"><h3>${escapeHtml(item.name)}</h3><button id="cz-x">✕</button></div>
      <div class="cz-body">
        ${groups.map(g => `
          <div class="cz-group" data-g="${g.key}">
            <h4>${escapeHtml(g.title)}</h4>
            <div class="cz-hint">${g.required ? '<b>Required</b> · ' : 'Optional · '}${g.type === 'multi' ? 'Select any' : 'Select 1'}</div>
            ${g.options.map(o => `
              <label class="cz-opt"><input type="${g.type === 'multi' ? 'checkbox' : 'radio'}" name="cz-${g.key}" value="${escapeHtml(o.id)}" ${(cz.sel[g.key] || []).includes(o.id) ? 'checked' : ''}>
              <span>${escapeHtml(o.name)}</span><span class="p">${o.price ? '+Rs.' + o.price : ''}</span></label>`).join('')}
          </div>`).join('')}
      </div>
      ${cz.error ? `<div class="cz-err">${escapeHtml(cz.error)}</div>` : ''}
      <div class="cz-foot">
        <div class="cz-qty"><button id="cz-m">−</button><span>${cz.qty}</span><button id="cz-p">+</button></div>
        <button class="cz-add" id="cz-add"><span>Add to order</span><span>Rs.${(unit * cz.qty).toFixed(2)}</span></button>
      </div>
    </div></div>`;
  const nb = root.querySelector('.cz-body'); if (nb) nb.scrollTop = scroll;
  document.getElementById('cz-ov').onclick = e => { if (e.target.id === 'cz-ov') closeCustomize(); };
  document.getElementById('cz-x').onclick = closeCustomize;
  document.getElementById('cz-m').onclick = () => { if (cz.qty > 1) { cz.qty--; drawCustomize(); } };
  document.getElementById('cz-p').onclick = () => { cz.qty++; drawCustomize(); };
  root.querySelectorAll('.cz-group input').forEach(inp => inp.onchange = () => {
    const key = inp.closest('.cz-group').dataset.g;
    if (X.groups[key].type === 'multi') {
      const cur = new Set(cz.sel[key] || []); inp.checked ? cur.add(inp.value) : cur.delete(inp.value); cz.sel[key] = [...cur];
    } else cz.sel[key] = [inp.value];
    cz.error = ''; drawCustomize();
  });
  document.getElementById('cz-add').onclick = () => {
    const miss = groups.find(g => g.required && (cz.sel[g.key] || []).length === 0);
    if (miss) { cz.error = 'Please choose: ' + miss.title.replace(/^Choose your /, ''); drawCustomize(); return; }
    const it = cz.item, mods = czMods(), q = cz.qty;
    closeCustomize(); addToCart(it, mods, q);
  };
}

/* ---------- cart ops ---------- */
function addToCart(item, mods, qty) {
  mods = mods || []; qty = qty || 1;
  const key = item.id + '|' + mods.map(m => m.id).sort().join(',');
  const extra = mods.reduce((s, m) => s + (m.p || 0), 0);
  const existing = state.cart.find(c => lineKeyOf(c) === key);
  if (existing) existing.qty += qty;
  else {
    const base = effectivePrice(item);
    state.cart.push({ key, itemId: item.id, name: item.name, price: base + extra, originalPrice: item.price + extra, happyHour: base < item.price, mods, qty });
  }
  persist();
  render();
}
function changeQty(key, delta) {
  const line = state.cart.find(c => lineKeyOf(c) === key);
  if (!line) return;
  line.qty += delta;
  if (line.qty <= 0) state.cart = state.cart.filter(c => lineKeyOf(c) !== key);
  persist();
  render();
}
"""

def sub1(s, old, new, count=1):
    assert s.count(old) == count, (old[:70], s.count(old))
    return s.replace(old, new)

def build(src, dest, brand, add, extras_src):
    s = (root / src).read_text()
    s = sub1(s, "\n<script>\n/* ---------- supabase ---------- */", '\n<script src="%s"></script>\n<script>\n/* ---------- supabase ---------- */' % extras_src)
    s = sub1(s, "</style>\n</head>", CSS + "</style>\n</head>")
    s = sub1(s, "function loadMenu() {", PRE.replace('__BRAND__', brand).replace('__ADD__', str(add)) + "function loadMenu() {")
    # replace the old cart ops (addToCart + changeQty) with the customisation-aware ones
    a = s.index("/* ---------- cart ops ---------- */"); b = s.index("function clearCart()")
    s = s[:a] + JS + s[b:]
    # item tap opens the popup for customisable items
    s = sub1(s, "    if (item) addToCart(item);\n  });", "    if (item) { if (groupsFor(item).length) openCustomize(item); else addToCart(item); }\n  });")
    # cart lines: key + options
    s = sub1(s, 'data-qty="${c.itemId}:-1"', 'data-qty="${lineKeyOf(c)}:-1"')
    s = sub1(s, 'data-qty="${c.itemId}:1"', 'data-qty="${lineKeyOf(c)}:1"')
    s = sub1(s, '<div class="cprice">Rs.${c.price.toFixed(2)} each</div>',
             '${(c.mods || []).length ? `<div class="cprice">${escapeHtml(c.mods.map(modStr).join(", "))}</div>` : ""}<div class="cprice">Rs.${c.price.toFixed(2)} each</div>')
    s = sub1(s, "const inCart = state.cart.find(c => c.itemId === item.id);",
             "const inCartQty = state.cart.filter(c => c.itemId === item.id).reduce((t, c) => t + c.qty, 0); const inCart = inCartQty ? { qty: inCartQty } : null;")
    # options travel with the order (KOT, bill, history)
    s = sub1(s, "qty: c.qty, price: c.price }))", "qty: c.qty, price: c.price, mods: (c.mods || []).map(modStr) }))", 2)
    s = sub1(s, "      if (idx === 0) push(textToBytes(padLine(ln, '', w - 5) + '  x' + it.qty + '\\n'));\n      else push(textToBytes(ln + '\\n'));\n    });\n  });",
             "      if (idx === 0) push(textToBytes(padLine(ln, '', w - 5) + '  x' + it.qty + '\\n'));\n      else push(textToBytes(ln + '\\n'));\n    });\n    (it.mods || []).forEach(m => wrapText('  + ' + m, w).forEach(ln => push(textToBytes(ln + '\\n'))));\n  });")
    s = sub1(s, "      if (idx === lines.length - 1) push(textToBytes(padLine(ln, 'Rs.' + lineTotal, w) + '\\n'));\n      else push(textToBytes(ln + '\\n'));\n    });\n  });",
             "      if (idx === lines.length - 1) push(textToBytes(padLine(ln, 'Rs.' + lineTotal, w) + '\\n'));\n      else push(textToBytes(ln + '\\n'));\n    });\n    (it.mods || []).forEach(m => wrapText('  + ' + m, w).forEach(ln => push(textToBytes(ln + '\\n'))));\n  });")
    # online orders: show and keep the customer's choices
    s = sub1(s, '<span class="mname" style="font-size:13px;">${escapeHtml(it.name)}</span>',
             '<span class="mname" style="font-size:13px;">${escapeHtml(it.name)}${(it.mods || []).length ? `<br><span style="font-weight:400;color:var(--text-soft);font-size:12px;">${escapeHtml(it.mods.join(" · "))}</span>` : ""}</span>')
    s = sub1(s, "itemId: 'online-' + Math.random(),", "itemId: 'online-' + Math.random(), mods: (it.mods || []).map(m => ({ raw: m })),")
    s = sub1(s, "Accept & Print KOT", "Accept & Print Bill")
    # new menu items (Duet, Vegan) appear even before they are in the server menu
    s, n = re.subn(r"(function loadMenu\(\) \{\n  const storedVersion = DB\.load\('[a-z_]+', 0\);\n  if \(storedVersion < MENU_VERSION\) return )DEFAULT_MENU;\n  return (DB\.load\('[a-z_]+', DEFAULT_MENU\));\n\}",
                   r"\1withNewItems(DEFAULT_MENU);\n  return withNewItems(\2);\n}", s)
    assert n == 1, 'loadMenu patch'
    a = s.index("async function loadMenuFromSupabase()"); b = s.index("  persist();\n  render();\n}", a)
    s = s[:b] + "  state.menu = withNewItems(state.menu);\n" + s[b:]
    if not LIVE:   # test build keeps its own local storage so it never touches the live pages' data
        s = re.sub(r"'((?:harlur_)?)billing_", r"'\1v2_billing_", s)
    (root / dest).parent.mkdir(parents=True, exist_ok=True)
    (root / dest).write_text(s)

if LIVE:
    build('staff.html', 'staff.html', 'Aricee', 0, 'menu-extras.js')
    build('harlur/staff.html', 'harlur/staff.html', 'Harlur', 10, '../menu-extras.js')
else:
    build('staff.html', 'v2/staff.html', 'Aricee', 0, 'menu-extras.js')
    build('harlur/staff.html', 'v2/harlur/staff.html', 'Harlur', 10, '../menu-extras.js')
print('built', 'LIVE' if LIVE else 'v2 test')
