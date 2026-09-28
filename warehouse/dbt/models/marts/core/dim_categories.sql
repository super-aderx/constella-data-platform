select
  tenant_id,
  category_id,
  parent_id,
  name,
  slug,
  coalesce(parent_id, category_id) as top_category_id,
  case when parent_id is null then 1 else 2 end as depth
from {{ ref('int_categories') }}
