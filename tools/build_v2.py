"""Builds the v2 customer pages (Aricee + Harlur) from tools/customer.template.html."""
import pathlib
root = pathlib.Path(__file__).resolve().parent.parent
t = (root / 'tools/customer.template.html').read_text()
def make(path, outlet, name, add, extras):
    s = (t.replace('__OUTLET_NAME__', name).replace('__OUTLET__', outlet)
          .replace('__PRICE_ADD__', str(add)).replace('__EXTRAS_SRC__', extras))
    p = root / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s)
make('v2/index.html', 'Aricee', 'Aricee - The Indian Kitchen', 0, 'menu-extras.js')
make('v2/harlur/index.html', 'Harlur', 'Aricee - Harlur', 10, '../menu-extras.js')
