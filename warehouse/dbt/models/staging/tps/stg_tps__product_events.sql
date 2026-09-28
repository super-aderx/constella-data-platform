select
  tenant_id,
  event_id,
  event_type,
  occurred_at,
  (payload ->> 'product_id')::uuid as product_id,
  payload ->> 'sku' as sku,
  payload ->> 'name' as name,
  payload ->> 'brand' as brand,
  (payload ->> 'category_id')::uuid as category_id,
  payload ->> 'unit' as unit,
  payload ->> 'size' as size,
  payload ->> 'status' as status
from {{ ref('stg_tps__events') }}
where
  event_type in ('ProductCreated', 'ProductUpdated')
  and schema_version = 1
