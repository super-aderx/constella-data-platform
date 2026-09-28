select
  tenant_id,
  product_id,
  sku,
  name,
  brand,
  category_id,
  top_category_id,
  unit,
  size,
  status,
  price_cents,
  currency::char(3) as currency
from {{ ref('dim_products') }}
where tenant_id = {{ current_tenant() }}
