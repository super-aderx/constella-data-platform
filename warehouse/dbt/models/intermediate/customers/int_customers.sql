-- Current state of each customer; registered_at from their first event.
with ordered as (
  select
    tenant_id,
    customer_id,
    status,
    occurred_at,
    first_value(registered_at) over (
      partition by tenant_id, customer_id
      order by occurred_at, event_id
    ) as first_registered_at,
    row_number() over (
      partition by tenant_id, customer_id
      order by occurred_at desc, event_id desc
    ) as recency_rank
  from {{ ref('stg_tps__customer_events') }}
)

select
  tenant_id,
  customer_id,
  status,
  first_registered_at as registered_at,
  occurred_at as updated_at
from ordered
where recency_rank = 1
