select
  tenant_id,
  day,
  segment,
  sku,
  n_orders,
  qty,
  revenue_cents
from {{ ref('agg_daily_product') }}
where tenant_id = {{ current_tenant() }}
