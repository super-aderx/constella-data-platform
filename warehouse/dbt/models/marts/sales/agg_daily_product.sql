{{ config(indexes=[{'columns': ['tenant_id', 'day']}]) }}

-- Paid orders containing each product, per local day and segment. Revenue is gross line value:
-- a coupon discount can't be split across products.
select
  tenant_id,
  order_day as day,
  segment,
  sku,
  count(*)::int as n_orders,
  sum(qty)::int as qty,
  sum(line_total_cents)::bigint as revenue_cents
from {{ ref('fct_order_items') }}
group by tenant_id, order_day, segment, sku
