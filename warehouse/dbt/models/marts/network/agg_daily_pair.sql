{{ config(indexes=[
  {'columns': ['tenant_id', 'day']},
  {'columns': ['tenant_id', 'sku_a']},
  {'columns': ['tenant_id', 'sku_b']},
]) }}

-- Paid orders containing both products, per local day and segment. sku_a < sku_b compares
-- bytes (collate "C"), so pair order doesn't depend on the database's locale.
select
  a.tenant_id,
  a.order_day as day,
  a.segment,
  a.sku as sku_a,
  b.sku as sku_b,
  count(*)::int as n_orders
from {{ ref('fct_order_items') }} as a
inner join {{ ref('fct_order_items') }} as b
  on
    a.tenant_id = b.tenant_id
    and a.order_id = b.order_id
    and a.sku < b.sku collate "C"
group by a.tenant_id, a.order_day, a.segment, a.sku, b.sku
