# Lakebase Inventory Management System

This is a simple brickbuilder app built using Flask for inventory operations leveraging the full power of the Databricks Lakehouse Platform, including **Databricks Lakehouse Apps**, **Unity Catalog**, and the new **Databricks Lakebase (Managed Postgres)**.

This app demonstrates the power of the Databricks platform by enabling you to build and host a web application that uses Lakebase as its underlying storage and hosting it as an app—all within Databricks itself. By leveraging Databricks' managed infrastructure, the solution eliminates the complexity and overhead typically associated with deploying and maintaining such applications using traditional methods.

## Key Highlights

- **Databricks Lakehouse & Lakebase Integration**: This system is architected to take advantage of the Databricks Lakehouse, unifying analytics, governance, and AI on a single platform. With **Lakebase (Managed Postgres)**, your transactional inventory data is stored in a fully managed, highly available PostgreSQL database, natively integrated with the Lakehouse where storage and compute are separated. This enables seamless analytics, real-time reporting, and direct SQL access to operational data, all governed by Databricks security and compliance controls. Once the transactional data is available in the Postgres table, it gets synced back to the Databricks workspace as a foreign table at near-real-time latency. This allows for analytics to be performed at NRT for transactional data. And this is bi-directional!! Existing data in UC can also be synced to the postgres instance for any OLTP usage for the web app.

- **Lakehouse Apps & Embedded Analytics**: The application leverages Databricks Lakehouse Apps to deliver a seamless user experience, embedding live Databricks dashboards and analytics directly within the inventory management interface. Users can interact with up-to-date analytics powered by Lakebase and Delta Lake, without leaving the app.

- **Unity Catalog Security & Governance**: All inventory and analytics data is managed through **Unity Catalog**, providing fine-grained access control, centralized governance, and full data lineage. This ensures that sensitive inventory information is protected, access is auditable, and compliance requirements are met across both Lakebase and analytical layers.

- **Enterprise-Grade Security**: The system utilizes Databricks' advanced security features, including OAuth-based authentication, secure token management, and proxying for dashboard embedding. With Unity Catalog, you get row- and column-level security, dynamic data masking, and robust audit trails, ensuring your inventory data is always protected.

- **Lakehouse Data Sharing**: Effortlessly share inventory datasets with internal teams or external partners using Databricks' secure data sharing capabilities, powered by Delta Sharing and Unity Catalog, while maintaining strict governance and access controls.

- **Scalable & Extensible**: Designed for both local development (SQLite) and production (Databricks Lakebase/PostgreSQL), the system can scale from small teams to large enterprises. The modular architecture allows for easy integration with additional Databricks features, such as MLflow for predictive analytics or Databricks Workflows for automation.

- **Modern User Experience**: Enjoy a responsive, intuitive web interface with bulk CSV upload, real-time validation, and analytics at your fingertips. The app supports template downloads, progress tracking, and detailed error feedback for seamless data onboarding.

## Security & Compliance

- **Unity Catalog**: Centralized governance for all inventory data, with audit trails and access policies spanning Lakebase and analytical data.
- **OAuth & Token Management**: Secure authentication flows for dashboard embedding and API access.
- **Row- and Column-Level Security**: Enforce granular permissions on inventory records via Unity Catalog, even within Lakebase tables.
- **Auditability**: All user actions and data changes are logged for compliance and traceability.

## Built for the Databricks Lakehouse Era

This project exemplifies the next generation of data-driven applications, harnessing the Databricks Lakehouse, Lakebase (Managed Postgres), Unity Catalog, and secure app embedding to deliver actionable insights and operational excellence for inventory management.

For a deep dive into the Databricks dashboard integration, Lakebase setup, and security architecture, see `DASHBOARD_INTEGRATION_SUMMARY.md` and `DASHBOARD_SETUP.md`.

## Quick Start

### Prerequisites
- **Python 3.9+** (recommended: 3.10 or newer)
- **Databricks Workspace** Unity Catalog enabled.
- **Databricks Apps (Compute)** That has permissions granted to the Lakebase instance and to the secret scope.
- **Lakebase (Managed Postgres) instance** 
- **Required Python packages** (see `requirements.txt`)
- **Databricks dashboard** (Optional. For embedded analytics; see `DASHBOARD_SETUP.md`)
- **Databricks Secret Scope** For the Flask key. 

### For Local Development (Recommended):
```bash
# Activate your virtual environment
source venv/bin/activate

# Run the local version with CSV upload
python app_local.py
```

### For Production (PostgreSQL):
```bash
# Set your environment variables first:
# PGDATABASE, PGUSER, PGHOST, PGPORT, etc.

# Run the PostgreSQL version with CSV upload
python app.py
```

## 🚀 Databricks App Deployment

### Step 1: Set Up Lakebase Database Resource

When creating your Databricks App, you need to add your Lakebase database as an App resource:

1. **Create/Edit your Databricks App**
2. **Add Database Resource:**
   - Go to **App Resources** section
   - Click **Add Resource**
   - Select **Database** type
   - **Resource Name**: Use your database name (e.g., `databricks_postgres`)
   - **Resource Key**: Set this to the same as your database name (e.g., `databricks_postgres`)
   - **Permission**: Select **"Can Connect"**
   - **Database**: Select your Lakebase instance from the dropdown

### Step 2: Set Up Flask Secret Key

1. **Generate a secure Flask secret key:**
   ```python
   import secrets
   print(secrets.token_hex(32))
   # Example output: 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6'
   ```

2. **Create Databricks Secret Scope:**
   ```bash
   # Using Databricks CLI
   databricks secrets create-scope app-secrets
   
   # Add the Flask secret key
   databricks secrets put-secret app-secrets SECRET_KEY
   # When prompted, paste your generated secret key
   ```

3. **Add Secret Scope as App Resource:**
   - Go to **App Resources** section
   - Click **Add Resource**
   - Select **Secret Scope** type
   - **Resource Name**: `app-secrets`
   - **Resource Key**: `app-secrets`
   - **Permission**: Select **"Can Read"**
   - **Secret Scope**: Select `app-secrets` from the dropdown

### Step 3: Configure Your app.yaml

Create an `app.yaml` file with the following configuration:

```yaml
name: inventory-management-app
description: Databricks Lakebase Inventory Management System

# Database configuration
env:
  - name: PGDATABASE
    value: "your_database_name"
  - name: PGUSER (only for local testing)
    value: "your_username@domain.com"
  - name: PGHOST (only for local testing)
    value: "your-lakebase-host.database.azuredatabricks.net"
  - name: PGPASSWORD (only for local testing)
    value: "your PGUSER password or OAUTH token"
  - name: PGPORT
    value: "5432"
  - name: PGSSLMODE
    value: "require"
  - name: PGAPPNAME
    value: "inventory_app"
  
  # Schema and table configuration
  - name: POSTGRES_SCHEMA
    value: "inventory_app"
  - name: POSTGRES_TABLE
    value: "inventory_items"
  
  # App configuration
  - name: PORT
    value: "8080"
  
  # Databricks configuration (optional - for dashboard integration)
  - name: DATABRICKS_HOST
    value: "https://your-workspace.cloud.databricks.com"
  - name: DASHBOARD_ID
    value: "your-dashboard-uuid"  # Optional

# Resources
resources:
  # Lakebase database resource
  - name: databricks_postgres
    key: databricks_postgres
    permission: CAN_CONNECT
  
  # Secret scope for Flask key
  - name: app-secrets
    key: app-secrets
    permission: CAN_READ
```

### Step 4: Deploy Your App

```bash
# Using Databricks CLI
# Optional Continuous Sync
databricks sync --watch . <your app deployment workspace path for source code>

# Deploy the app
databricks apps deploy <app name> --source-code-path <your app deployment workspace path for source code>

# Or using the Databricks UI
# Upload your code and app.yaml through the Apps interface
```

### Step 5: Verify App Resources

After deployment, verify that your app has access to:

1. **Database Connection**: The app should be able to connect to your Lakebase instance
2. **Secret Access**: The app should be able to read the Flask secret key from the secret scope
3. **Table Creation**: The app will automatically create the `inventory_app.inventory_items` table on first run

## 📊 CSV Upload Features

- **Bulk Upload**: Add multiple items at once via CSV
- **Data Validation**: Comprehensive validation with detailed error reporting
- **Template Download**: Get the correct CSV format
- **Progress Tracking**: Visual upload progress and results
- **Error Handling**: Skip invalid rows, process valid ones
- **File Size Limit**: 16MB maximum file size

### 📋 CSV Format Requirements:

#### Required Columns:
- `item_name` (max 100 characters)
- `category` (max 50 characters) 
- `quantity` (integer ≥ 0)
- `unit_price` (decimal ≥ 0)

#### Optional Columns:
- `description`
- `supplier` (max 100 characters)
- `location` (max 100 characters)
- `minimum_stock` (integer ≥ 0)

## 📄 Sample Data

Use the included `sample_inventory.csv` for testing:
- 10 different equipment items
- Various categories (Electronics, Furniture, Safety Equipment, Office Supplies)
- Mix of high and low-value items
- Some items with low stock alerts

## 🔧 Switching Between Versions

To change which app version you're using:

1. **For YAML/Docker deployments**: Update your configuration to point to the desired Python file
2. **For local development**: Simply run the appropriate Python file
3. **All versions share the same templates**, so no additional setup needed

## ⚠️ Important Notes

- **CSV uploads only ADD new items** - they don't update or delete existing items
- **Data validation is strict** - invalid rows are skipped with detailed error messages
- **File encoding should be UTF-8** for best compatibility
- **Templates are automatically generated** with the latest format requirements
- **App Resources are required** for Databricks App deployment - ensure both database and secret scope resources are properly configured

## 🛠️ Troubleshooting

### Common Issues:

1. **Database Connection Errors**: 
   - Verify the database resource is added with "Can Connect" permission
   - Check that your PGUSER has proper OAuth identity mapping in the database

2. **Secret Key Errors**:
   - Ensure the secret scope resource is added with "Can Read" permission
   - Verify the SECRET_KEY exists in the secret scope

3. **Table Creation Issues**:
   - The app automatically creates the schema and table on first run
   - Ensure your database user has CREATE privileges

### OAuth Identity Mapping:

If you encounter OAuth identity mismatch errors, run this SQL in your Lakebase instance:

```sql
-- Replace with your actual email and service principal ID
ALTER ROLE "your_username@domain.com" 
SET databricks.oauth.identity = 'your-app-service-principal-id';
```
