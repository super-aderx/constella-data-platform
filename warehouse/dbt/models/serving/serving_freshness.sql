select
  tenant_id,
  first_day,
  last_event_at,
  last_complete_day,
  refreshed_at
from {{ ref('tenant_freshness') }}
where tenant_id = {{ current_tenant() }}
