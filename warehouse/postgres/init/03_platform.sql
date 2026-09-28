-- The tenant registry. One tenant = one StarMart (TPS) deployment.
create table platform.tenants (
  tenant_id uuid primary key,
  tenant_key text unique not null,  -- topic prefix and API header value, e.g. harbor-street
  name text not null,
  timezone text not null,           -- IANA; defines a tenant's "day"
  currency char(3) not null,
  created_at timestamptz not null default now()
);
