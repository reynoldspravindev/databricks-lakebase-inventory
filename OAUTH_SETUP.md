# OAuth Setup Guide for Databricks Lakebase

This guide explains how to resolve the "permission denied for schema inventory_app" error when using OAuth authentication with Databricks Lakebase.

## Problem

When using OAuth authentication, the application connects to PostgreSQL with an OAuth user ID (like `d33ef0ea-36ec-496a-ac61-30a0b262d5fc`) instead of a traditional username. This OAuth user doesn't have permissions to create schemas or access the `inventory_app` schema.

## Solution

The database administrator must manually create the schema and grant appropriate permissions to the OAuth user.

## Steps

### 1. Identify the OAuth User ID

Deploy your app and check the logs. You'll see output like:
```
Current user: d33ef0ea-36ec-496a-ac61-30a0b262d5fc
Session user: d33ef0ea-36ec-496a-ac61-30a0b262d5fc
```

The long alphanumeric string is your OAuth user ID.

### 2. Run Database Setup

Connect to your Lakebase instance as a database administrator and run:

```sql
-- Replace 'YOUR_OAUTH_USER_ID' with the actual ID from step 1
CREATE SCHEMA IF NOT EXISTS inventory_app;
GRANT USAGE ON SCHEMA inventory_app TO "YOUR_OAUTH_USER_ID";
GRANT CREATE ON SCHEMA inventory_app TO "YOUR_OAUTH_USER_ID";
```

### 3. Create Table and Grant Permissions

```sql
-- Create the table
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

-- Grant table permissions
GRANT ALL PRIVILEGES ON TABLE inventory_app.inventory_items TO "YOUR_OAUTH_USER_ID";
GRANT USAGE, SELECT ON SEQUENCE inventory_app.inventory_items_id_seq TO "YOUR_OAUTH_USER_ID";
```

### 4. Verify Permissions

```sql
-- Check schema permissions
SELECT has_schema_privilege('YOUR_OAUTH_USER_ID', 'inventory_app', 'USAGE');
SELECT has_schema_privilege('YOUR_OAUTH_USER_ID', 'inventory_app', 'CREATE');

-- Check table permissions  
SELECT has_table_privilege('YOUR_OAUTH_USER_ID', 'inventory_app.inventory_items', 'SELECT');
SELECT has_table_privilege('YOUR_OAUTH_USER_ID', 'inventory_app.inventory_items', 'INSERT');
```

All queries should return `t` (true).

### 5. Restart Your App

After the database administrator has set up the permissions, restart your Databricks app. The initialization should now succeed.

## Alternative: Public Permissions (Testing Only)

For testing environments, you can grant permissions to PUBLIC (less secure):

```sql
GRANT USAGE ON SCHEMA inventory_app TO PUBLIC;
GRANT CREATE ON SCHEMA inventory_app TO PUBLIC;
GRANT ALL PRIVILEGES ON TABLE inventory_app.inventory_items TO PUBLIC;
GRANT USAGE, SELECT ON SEQUENCE inventory_app.inventory_items_id_seq TO PUBLIC;
```

## Troubleshooting

### Check Current User
Use the debug endpoint to see the current OAuth user:
```
GET /api/debug-oauth
```

### Manual Permission Fix
Try the permission fix endpoint (may not work in OAuth environments):
```
GET /api/fix-permissions
```

### View App Logs
Check your Databricks app logs for detailed error messages and the exact OAuth user ID.

## Files

- `setup_database_permissions.sql` - Complete SQL script for database setup
- This guide provides step-by-step instructions
- The app includes diagnostic endpoints to help troubleshoot issues
