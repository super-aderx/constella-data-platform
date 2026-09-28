-- Current state of each category: its latest event (Created and Updated carry full state).
select distinct on (tenant_id, category_id)
  tenant_id,
  category_id,
  parent_id,
  name,
  slug,
  occurred_at as updated_at
from {{ ref('stg_tps__category_events') }}
order by tenant_id, category_id, occurred_at desc, event_id desc
