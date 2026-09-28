-- SCD2 of each SKU's price, by the payload's valid_from. If two events share a valid_from,
-- the later event wins.
with prices as (
  select distinct on (tenant_id, sku, valid_from)
    tenant_id,
    sku,
    valid_from,
    amount_cents,
    currency
  from {{ ref('stg_tps__price_events') }}
  order by tenant_id, sku, valid_from, occurred_at desc, event_id desc
)

select
  tenant_id,
  sku,
  valid_from,
  lead(valid_from) over (partition by tenant_id, sku order by valid_from) as valid_to,
  amount_cents,
  currency
from prices
