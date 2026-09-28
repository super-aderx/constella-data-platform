select
  tenant_id,
  category_id,
  parent_id,
  name,
  slug,
  top_category_id
from {{ ref('dim_categories') }}
where tenant_id = {{ current_tenant() }}
