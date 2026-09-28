-- SCD2: every product event is a full snapshot, valid until the next one.
with snapshots as (
  select
    tenant_id,
    sku,
    product_id,
    name,
    brand,
    category_id,
    unit,
    size,
    status,
    occurred_at as valid_from,
    lead(occurred_at) over (
      partition by tenant_id, sku
      order by occurred_at, event_id
    ) as valid_to
  from {{ ref('stg_tps__product_events') }}
)

select
  tenant_id,
  sku,
  product_id,
  name,
  brand,
  category_id,
  unit,
  size,
  status,
  valid_from,
  valid_to,
  valid_to is null as is_current
from snapshots
