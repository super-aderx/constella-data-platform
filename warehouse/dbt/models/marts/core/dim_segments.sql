select
  segment,
  label,
  description,
  sort_order
from {{ ref('segments') }}
