-- Not tenant-scoped: the same segments for every tenant.
select
  segment,
  label,
  description,
  sort_order
from {{ ref('dim_segments') }}
