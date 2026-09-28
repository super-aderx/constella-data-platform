-- Each product's current state and current price.
with products as (
  select
    tenant_id,
    product_id,
    sku,
    name,
    brand,
    category_id,
    unit,
    size,
    status
  from {{ ref('int_products_history') }}
  where is_current
),

prices as (
  select
    tenant_id,
    sku,
    amount_cents,
    currency
  from {{ ref('int_prices_history') }}
  where valid_to is null
)

select
  p.tenant_id,
  p.product_id,
  p.sku,
  p.name,
  p.brand,
  p.category_id,
  c.top_category_id,
  p.unit,
  p.size,
  p.status,
  pr.amount_cents as price_cents,
  pr.currency
from products as p
left join {{ ref('dim_categories') }} as c
  on p.tenant_id = c.tenant_id and p.category_id = c.category_id
left join prices as pr
  on p.tenant_id = pr.tenant_id and p.sku = pr.sku
