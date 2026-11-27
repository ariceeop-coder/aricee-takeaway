"""Builds the customer pages (Aricee + Harlur) from tools/customer.template.html."""
import pathlib
root = pathlib.Path(__file__).resolve().parent.parent
t = (root / 'tools/customer.template.html').read_text()
def make(path, outlet, name, place, add, extras, policy):
    s = (t.replace('__OUTLET_NAME__', name).replace('__LOCATION__', place).replace('__OUTLET__', outlet)
          .replace('__PRICE_ADD__', str(add)).replace('__EXTRAS_SRC__', extras).replace('__POLICY_HREF__', policy))
    p = root / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s)
make('index.html', 'Aricee', 'Aricee - The Indian Kitchen', 'Electronic City Phase 1', 0, 'menu-extras.js', 'policies.html')
make('harlur/index.html', 'Harlur', 'Aricee - The Indian Kitchen', 'Harlur', 10, '../menu-extras.js', '../policies.html')
