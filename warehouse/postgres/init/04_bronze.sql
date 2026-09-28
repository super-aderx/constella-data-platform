-- Raw events, one row per Kafka message, append-only. The only permanent copy of history:
-- nothing but the dev generator's --reset ever deletes from it.
create table bronze.tps_events (
  tenant_id uuid not null,
  event_id uuid not null,            -- envelope; UUIDv7
  event_type text not null,          -- e.g. OrderPlaced
  schema_version int not null,
  occurred_at timestamptz not null,  -- business time
  aggregate_id text not null,        -- order_id, sku, customer_id …
  trace_id text,
  payload jsonb not null,
  topic text not null,
  kafka_partition int not null,
  kafka_offset bigint not null,
  loaded_at timestamptz not null default now(),
  unique (topic, kafka_partition, kafka_offset)
);
create index on bronze.tps_events (tenant_id, event_type);
create index on bronze.tps_events (loaded_at);

-- Behavioral events (views, searches, cart, recommendation impressions). aggregate_id holds
-- session_id. Loaded and kept from day one; not read by dbt yet.
create table bronze.tps_behavioral_events (like bronze.tps_events including all);
