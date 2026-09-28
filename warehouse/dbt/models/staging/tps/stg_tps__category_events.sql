select
  tenant_id,
  event_id,
  event_type,
  occurred_at,
  (payload ->> 'category_id')::uuid as category_id,
  (payload ->> 'parent_id')::uuid as parent_id,
  payload ->> 'name' as name,
  payload ->> 'slug' as slug
from {{ ref('stg_tps__events') }}
where
  event_type in ('CategoryCreated', 'CategoryUpdated')
  and schema_version = 1
