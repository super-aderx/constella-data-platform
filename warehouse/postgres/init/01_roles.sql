-- Dev passwords only; they match .env.example. Real deployments set them from a secret store.
create role loader login password 'loader_dev';
create role dbt_runner login password 'dbt_runner_dev';
create role api_reader login password 'api_reader_dev';
