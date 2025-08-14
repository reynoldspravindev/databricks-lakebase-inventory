-- Database Setup Script for Databricks Lakebase with OAuth
-- This script must be run by a database administrator with superuser privileges

-- Replace 'd33ef0ea-36ec-496a-ac61-30a0b262d5fc' with the actual OAuth user ID
-- (You can find this in the app logs when it starts up)

-- Step 1: Create the schema
CREATE SCHEMA IF NOT EXISTS inventory_app;

-- Step 2: Grant schema permissions to the OAuth user
-- Replace the user ID below with the actual OAuth user from your app logs
GRANT USAGE ON SCHEMA inventory_app TO "d33ef0ea-36ec-496a-ac61-30a0b262d5fc";
GRANT CREATE ON SCHEMA inventory_app TO "d33ef0ea-36ec-496a-ac61-30a0b262d5fc";

-- Step 3: Create the table (or let the app create it)
CREATE TABLE IF NOT EXISTS inventory_app.inventory_items (
	id serial4 NOT NULL,
	item_name varchar(100) NOT NULL,
	description text NULL,
	category varchar(50) NOT NULL,
	quantity int4 NOT NULL,
	unit_price float8 NOT NULL,
	supplier varchar(100) NULL,
	"location" varchar(100) NULL,
	minimum_stock int4 NULL,
	date_added timestamp DEFAULT CURRENT_TIMESTAMP,
	last_updated timestamp DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT inventory_items_pkey PRIMARY KEY (id)
);

-- Step 4: Grant table permissions to the OAuth user
GRANT ALL PRIVILEGES ON TABLE inventory_app.inventory_items TO "d33ef0ea-36ec-496a-ac61-30a0b262d5fc";
GRANT USAGE, SELECT ON SEQUENCE inventory_app.inventory_items_id_seq TO "d33ef0ea-36ec-496a-ac61-30a0b262d5fc";

-- Step 5: Verify permissions
-- Check that the user can access the schema
SELECT has_schema_privilege('d33ef0ea-36ec-496a-ac61-30a0b262d5fc', 'inventory_app', 'USAGE');
SELECT has_schema_privilege('d33ef0ea-36ec-496a-ac61-30a0b262d5fc', 'inventory_app', 'CREATE');

-- Check that the user can access the table
SELECT has_table_privilege('d33ef0ea-36ec-496a-ac61-30a0b262d5fc', 'inventory_app.inventory_items', 'SELECT');
SELECT has_table_privilege('d33ef0ea-36ec-496a-ac61-30a0b262d5fc', 'inventory_app.inventory_items', 'INSERT');
SELECT has_table_privilege('d33ef0ea-36ec-496a-ac61-30a0b262d5fc', 'inventory_app.inventory_items', 'UPDATE');
SELECT has_table_privilege('d33ef0ea-36ec-496a-ac61-30a0b262d5fc', 'inventory_app.inventory_items', 'DELETE');

-- Optional: Create a more permissive setup for testing
-- This grants permissions to any OAuth user (less secure but easier for testing)
-- GRANT USAGE ON SCHEMA inventory_app TO PUBLIC;
-- GRANT CREATE ON SCHEMA inventory_app TO PUBLIC;
-- GRANT ALL PRIVILEGES ON TABLE inventory_app.inventory_items TO PUBLIC;
-- GRANT USAGE, SELECT ON SEQUENCE inventory_app.inventory_items_id_seq TO PUBLIC;
