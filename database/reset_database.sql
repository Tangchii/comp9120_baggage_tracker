-- Reset a demo database back to a completely empty state.
-- Run this BEFORE re-running 01_schema.sql and 02_sample_data.sql, e.g.:
--   psql "$DATABASE_URL" -f database/reset_database.sql
--   psql "$DATABASE_URL" -f database/01_schema.sql
--   psql "$DATABASE_URL" -f database/02_sample_data.sql
-- This drops every table in the public schema. Only use it on the demo
-- database (local baggage_demo or the Neon demo project), never on data
-- you need to keep.
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
