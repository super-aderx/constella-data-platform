select
  tenant_id,
  day,
  segment,
  n_orders,
  n_lines,
  n_items,
  subtotal_cents,
  discount_cents,
  revenue_cents
from {{ ref('agg_daily_orders') }}
where tenant_id = {{ current_tenant() }}
