# Deployment Guide

## Environment Variables

### IS_FRESH_DEPLOYMENT

This environment variable controls whether the application should create a fresh database schema and tables.

**Values:**
- `"true"` - Fresh deployment mode
  - Creates a new schema based on `POSTGRES_SCHEMA` value
  - Creates all necessary tables (products, customers, orders, order_items, pickup_slots)
  - Inserts sample data for demonstration
  - Creates performance indexes

- `"false"` - Existing deployment mode (default)
  - Uses existing schema and tables
  - Only ensures the schema exists

### POSTGRES_SCHEMA

This environment variable specifies the name of the PostgreSQL schema to use.

**Default:** `"inventory_app"`

## Usage Examples

### Fresh Deployment
```yaml
env:
  - name: 'IS_FRESH_DEPLOYMENT'
    value: 'true'
  - name: 'POSTGRES_SCHEMA'
    value: 'my_new_inventory_schema'
```

### Existing Deployment
```yaml
env:
  - name: 'IS_FRESH_DEPLOYMENT'
    value: 'false'
  - name: 'POSTGRES_SCHEMA'
    value: 'existing_inventory_schema'
```

## SQL Scripts

The application uses two SQL scripts located in the `sql/` directory:

1. **`sql/create_schema.sql`** - Creates the schema and all tables with indexes
2. **`sql/insert_sample_data.sql`** - Inserts sample products for demonstration

These scripts use `{schema_name}` as a placeholder that gets replaced with the actual schema name from the `POSTGRES_SCHEMA` environment variable.

## Database Schema

The application creates the following tables in the specified schema:

- **products** - Product catalog with inventory tracking
- **customers** - Customer information
- **orders** - Order records with status tracking
- **order_items** - Individual items within orders
- **pickup_slots** - Available pickup time slots

All tables include proper foreign key relationships and indexes for optimal performance.
