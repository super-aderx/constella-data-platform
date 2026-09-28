{{ config(indexes=[{'columns': ['tenant_id', 'day']}]) }}

-- Paid orders per local day and segment. Revenue is net of discounts.
select
  tenant_id,
  order_day as day,
  segment,
  count(*)::int as n_orders,
  sum(n_lines)::int as n_lines,
  sum(n_items)::int as n_items,
  sum(subtotal_cents)::bigint as subtotal_cents,
  sum(discount_cents)::bigint as discount_cents,
  sum(total_cents)::bigint as revenue_cents
from {{ ref('fct_orders') }}
where status = 'paid'
group by tenant_id, order_day, segment
