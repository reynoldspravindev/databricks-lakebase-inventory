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
- **Deployment steps for Databricks Apps** follow directions as per the official [documentation for Apps CLI](https://docs.databricks.com/en/dev-tools/cli/commands/apps.html) or follow the instructions on the UI for Databricks Apps.

## 🛠️ Configuration

### YAML Configuration Example:
Refer: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-runtime
```yaml
command: ["python", "app.py"]
env:
  - name: 'DATABRICKS_HOST'
    value: <Databricks Workspace URL>
  - name: 'DASHBOARD_ID'
    value: <Optional Dashboard Id for Integration>
  - name: 'POSTGRES_SCHEMA'
    value: 'inventory_app'
  - name: 'POSTGRES_TABLE'
    value: 'inventory_items'
```