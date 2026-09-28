-- The only model that reads bronze: one row per event, keeping the first copy delivered.
with ranked as (
  select
    tenant_id,
    event_id,
    event_type,
    schema_version,
    occurred_at,
    aggregate_id,
    trace_id,
    payload,
    loaded_at,
    row_number() over (
      partition by tenant_id, event_id
      order by loaded_at, kafka_offset
    ) as copy_number
  from {{ source('bronze', 'tps_events') }}
)

select
  tenant_id,
  event_id,
  event_type,
  schema_version,
  occurred_at,
  aggregate_id,
  trace_id,
  payload,
  loaded_at
from ranked
where copy_number = 1
