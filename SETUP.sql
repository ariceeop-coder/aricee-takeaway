-- Aricee takeaway: complete Supabase setup (safe to run more than once)

create table if not exists menu_items (
  id text primary key, category text, name text, price numeric, sort_order integer default 0
);
alter table menu_items add column if not exists brand text not null default 'Aricee';

create table if not exists orders (
  id uuid primary key default gen_random_uuid(),
  order_no bigserial,
  created_at timestamptz default now(),
  brand text, items jsonb, subtotal numeric, discount_amt numeric, total numeric,
  status text default 'pending', customer_note text
);

create table if not exists bills (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz default now(),
  order_no text, brand text, bill_date text, bill_time text,
  items jsonb default '[]'::jsonb,
  subtotal numeric default 0, discount_amt numeric default 0,
  cgst_amt numeric default 0, sgst_amt numeric default 0, total numeric default 0,
  created_by uuid default auth.uid()
);

alter table menu_items enable row level security;
alter table orders enable row level security;
alter table bills enable row level security;

drop policy if exists "anyone can read menu" on menu_items;
create policy "anyone can read menu" on menu_items for select to public using (true);
drop policy if exists "staff manage menu" on menu_items;
create policy "staff manage menu" on menu_items for all to authenticated using (true) with check (true);

drop policy if exists "staff can read orders" on orders;
create policy "staff can read orders" on orders for select to authenticated using (true);
drop policy if exists "staff can update orders" on orders;
create policy "staff can update orders" on orders for update to authenticated using (true) with check (true);
drop policy if exists "staff can insert orders" on orders;
create policy "staff can insert orders" on orders for insert to authenticated with check (true);

drop policy if exists "staff manage bills" on bills;
create policy "staff manage bills" on bills for all to authenticated using (true) with check (true);

-- customers (not logged in) place and track orders only through these two functions
create or replace function place_order(p_brand text, p_items jsonb, p_subtotal numeric, p_discount_amt numeric, p_total numeric)
returns table(id uuid, order_no bigint) language plpgsql security definer set search_path to 'public' as $$
begin
  return query
  insert into orders (brand, items, subtotal, discount_amt, total, status)
  values (p_brand, p_items, p_subtotal, p_discount_amt, p_total, 'pending')
  returning orders.id, orders.order_no;
end; $$;

create or replace function get_order_status(p_id uuid)
returns text language sql security definer set search_path to 'public' as $$
  select status from orders where id = p_id;
$$;

grant execute on function place_order(text, jsonb, numeric, numeric, numeric) to anon, authenticated;
grant execute on function get_order_status(uuid) to anon, authenticated;

-- live new-order alerts for staff
do $$ begin
  begin alter publication supabase_realtime add table orders; exception when duplicate_object then null; end;
  begin alter publication supabase_realtime add table bills;  exception when duplicate_object then null; end;
end $$;

-- Then: Authentication -> Users -> Add user (email + password) for each staff member.
