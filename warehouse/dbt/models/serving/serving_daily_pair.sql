select
  tenant_id,
  day,
  segment,
  sku_a,
  sku_b,
  n_orders
from {{ ref('agg_daily_pair') }}
where tenant_id = {{ current_tenant() }}
