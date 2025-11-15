# Lakebase Inventory Management System

This is a simple brickbuilder app built using Flask for inventory operations leveraging the full power of the Databricks Lakehouse Platform, including **Databricks Lakehouse Apps**, **Unity Catalog**, and the new **Databricks Lakebase (Managed Postgres)**.

This app demonstrates the power of the Databricks platform by enabling you to build and host a web application that uses Lakebase as its underlying storage and hosting it as an app—all within Databricks itself. By leveraging Databricks' managed infrastructure, the solution eliminates the complexity and overhead typically associated with deploying and maintaining such applications using traditional methods.

## Key Highlights

- **Databricks Lakehouse & Lakebase Integration**: This system is architected to take advantage of the Databricks Lakehouse, unifying analytics, governance, and AI on a single platform. With **Lakebase (Managed Postgres)**, your transactional inventory data is stored in a fully managed, highly available PostgreSQL database, natively integrated with the Lakehouse where storage and compute are separated. This enables seamless analytics, real-time reporting, and direct SQL access to operational data, all governed by Databricks security and compliance controls. Once the transactional data is available in the Postgres table, it gets synced back to the Databricks workspace as a foreign table at near-real-time latency. 

This allows for analytics to be performed at NRT for transactional data. And this is bi-directional!! Existing data in UC can also be synced to the postgres instance for any OLTP usage for the web app as a reverse-ETL process using the 'Sync Table' feature on the Catalog Explorer page or, of course, programatically (SDK, Python, SQL, REST) and through CLI.

- **Lakehouse Apps & Embedded Analytics**: The application leverages Databricks Lakehouse Apps to deliver a seamless user experience, embedding live Databricks dashboards and analytics directly within the inventory management interface. Users can interact with up-to-date analytics powered by Lakebase and Delta Lake, without leaving the app.

- **Unity Catalog Security & Governance**: All inventory and analytics data is managed through **Unity Catalog**, providing fine-grained access control, centralized governance, and full data lineage. This ensures that sensitive inventory information is protected, access is auditable, and compliance requirements are met across both Lakebase and analytical layers.

- **Enterprise-Grade Security**: The system utilizes Databricks' advanced security features, including OAuth-based authentication, secure token management, and proxying for dashboard embedding. With Unity Catalog, you get row- and column-level security, dynamic data masking, and robust audit trails, ensuring your inventory data is always protected.

- **Lakehouse Data Sharing**: Effortlessly share inventory datasets with internal teams or external partners using Databricks' secure data sharing capabilities, powered by Delta Sharing and Unity Catalog, while maintaining strict governance and access controls.

- **Scalable & Extensible**: Designed for both local development (SQLite) and production (Databricks Lakebase/PostgreSQL), the system can scale from small teams to large enterprises. The modular architecture allows for easy integration with additional Databricks features, such as MLflow for predictive analytics or Databricks Workflows for automation.

- **Modern User Experience**: Enjoy a responsive, intuitive web interface with bulk CSV upload, real-time validation, and analytics at your fingertips. The app supports template downloads, progress tracking, and detailed error feedback for seamless data onboarding.

- **AI-Powered Demand Forecasting**: Leverage Databricks Model Serving with XGBoost models to predict inventory needs for the next 90 days. The system intelligently recommends optimal stock levels based on warehouse location, product category, and historical sales patterns, with automatic safety stock calculations and fallback logic for continuous operation.

## Technology Stack

- **Backend**: Python 3.9+ with Flask web framework
- **Database**: Databricks Lakebase (Managed PostgreSQL)
- **Database Driver**: psycopg3 with connection pooling
- **SDK**: Databricks SDK for Python
- **AI/ML**: Databricks Model Serving with XGBoost
- **Data Processing**: pandas for data manipulation
- **Frontend**: HTML5, CSS3, JavaScript with responsive design
- **Configuration**: YAML-based configuration with environment variable override
- **Authentication**: OAuth 2.0 with automatic token refresh
- **Analytics**: Embedded Databricks AI/BI Dashboards

## Security & Compliance

- **Unity Catalog**: Centralized governance for all inventory data, with audit trails and access policies spanning Lakebase and analytical data.
- **OAuth & Token Management**: Secure authentication flows for dashboard embedding and API access with automatic token refresh.
- **Row- and Column-Level Security**: Enforce granular permissions on inventory records via Unity Catalog, even within Lakebase tables.
- **Auditability**: All user actions and data changes are logged for compliance and traceability.
- **Secure Configuration**: Sensitive credentials stored in Databricks Secret Scope, never in code or config files.

## Quick Start

### Prerequisites

#### Required:
- **Python 3.9+** (recommended: 3.10 or newer)
- **Databricks Workspace** with Unity Catalog enabled
- **Databricks Apps (Compute)** with permissions granted to:
  - Lakebase instance (Can Connect)
  - Secret scope (Can Read)
- **Lakebase (Managed Postgres) instance** for transactional data storage
- **Required Python packages** (see `requirements.txt`):
  - Flask 2.3.0+
  - psycopg 3.1.0+ (with binary and pool support)
  - databricks-sdk 0.18.0+
  - requests 2.31.0+
  - pandas 2.0.0+
  - PyYAML 6.0+
- **Databricks Secret Scope** for storing the Flask secret key

#### Steps:
- Set the config variables in "/notebooks/0 - SETUP/0 - Setup.ipynb"
- Start running the notebooks under the "/notebooks/1 - DEPLOY ASSETS/" and the "/notebooks/1 - DEMAND FORECASTING/" folders in the respective order.
- These notebooks are self explanatory.  



## Core Features

### Inventory Management
- **Add/Edit/Delete Items**: Full CRUD operations for inventory items
- **Category Management**: Organize inventory with custom categories
- **Warehouse Management**: Track items across multiple warehouse locations with geographic coordinates
- **Supplier Management**: Maintain supplier information including contact details and geographic data
- **Low Stock Alerts**: Automatically identify items below minimum stock levels
- **Bulk CSV Upload**: Add multiple items at once with comprehensive validation
- **Search & Filter**: Quickly find items across your inventory

### AI-Powered Demand Forecasting
- **Real-Time Predictions**: Get AI-powered demand forecasts for the next 90 days
- **Smart Inventory Suggestions**: Receive intelligent recommendations on optimal stock levels
- **Model Serving Integration**: Connects to Databricks Model Serving endpoints for predictions
- **Safety Stock Calculation**: Automatically calculates safety stock (10% buffer) based on forecasts
- **Fallback Logic**: Uses minimum stock thresholds when model endpoint is unavailable
- **Interactive Feedback**: Real-time suggestions during item creation and editing

### Dashboard & Analytics
- **Embedded Dashboards**: View live Databricks AI/BI dashboards directly in the app
- **Real-Time Metrics**: Monitor inventory value, stock levels, and trends
- **Visual Analytics**: Interactive charts and graphs for better decision-making

### Data Management
- **Sample Data Loading**: Automatically populate with realistic sample data
- **Data Reset API**: Programmatically reset data while preserving forecast history
- **Foreign Table Sync**: Bi-directional sync between Lakebase and Unity Catalog
- **Comprehensive SQL Scripts**: Pre-built scripts for categories, warehouses, suppliers, and items

## CSV Upload Features

- **Bulk Upload**: Add multiple items at once via CSV
- **Data Validation**: Comprehensive validation with detailed error reporting
- **Template Download**: Get the correct CSV format
- **Progress Tracking**: Visual upload progress and results
- **Error Handling**: Skip invalid rows, process valid ones
- **File Size Limit**: 16MB maximum file size

### CSV Format Requirements:

#### Required Columns:
- `item_name` (max 100 characters)
- `category_id` (integer, must exist in categories table) 
- `quantity` (integer ≥ 0)
- `unit_price` (decimal ≥ 0)

#### Optional Columns:
- `description`
- `supplier_id` (integer, must exist in suppliers table)
- `warehouse_id` (integer, must exist in warehouses table)
- `minimum_stock` (integer ≥ 0)

## API Endpoints

The application provides RESTful API endpoints for programmatic access:

- **`GET /api/items`**: Retrieve all inventory items as JSON
- **`GET /api/token-status`**: Check OAuth token validity
- **`GET /api/dashboard-config`**: Get dashboard configuration status
- **`GET /api/demand-forecast`**: Get AI-powered demand forecast suggestions
  - Query parameters: `warehouse_id`, `category_id`, `item_name`, `current_quantity`, `minimum_stock`, `new_quantity`
- **`POST /api/reset-data`**: Reset all data and identity sequences (preserves demand forecast table)

## Notebooks

The repository includes Databricks notebooks for setup and advanced features:

### Setup Notebooks
- **`0 - Setup.ipynb`**: Initial setup and configuration
- **`1 - Deploy Assets.ipynb`**: Deploy database assets and configure resources

### Demand Forecasting Notebooks
- **`2.1 - Generate Synthetic Sales Data.ipynb`**: Generate realistic sales data for model training
- **`2.2 - Demand Forecasting.ipynb`**: Train and deploy demand forecasting model to Model Serving endpoint

## Data Management

### Environment Variables for Data Control

The application supports several environment variables for flexible data management:

- **`FORCE_DATA_RESET`**: Set to `"true"` to delete all data and reset identity sequences on startup (excludes demand forecast table)
- **`LOAD_SAMPLE_DATA`**: Set to `"false"` to disable automatic sample data loading (default: `"true"`)
- **`DEBUG_SQL`**: Set to `"true"` to show SQL content being executed for debugging (default: `"false"`)
- **`POSTGRES_CATEGORY_TABLE`**: Customize category table name (default: `inventory_category`)
- **`POSTGRES_WAREHOUSE_TABLE`**: Customize warehouse table name (default: `inventory_warehouse`)
- **`POSTGRES_SUPPLIER_TABLE`**: Customize supplier table name (default: `inventory_supplier`)
- **`MODEL_ENDPOINT_NAME`**: Databricks Model Serving endpoint name for demand forecasting (optional)

### Data Reset Options

1. **Automatic Reset on Startup**: Set `FORCE_DATA_RESET=true` to clear all data when the app starts
2. **Manual Reset via API**: Send POST request to `/api/reset-data` to reset data programmatically
3. **Standalone Reset Function**: Call `reset_all_data()` function in your code

**Note**: 
- All reset operations preserve the demand forecast table to maintain historical forecast data and analytics continuity
- After any reset operation, sample data is automatically loaded (unless `LOAD_SAMPLE_DATA=false`)
- On first-time setup, sample data is automatically loaded if tables are empty

### Sample Data Scripts

The repository includes SQL scripts for populating tables with realistic data in the `data/` folder:

- **`data/category_data.sql`**: 40+ realistic product categories across various industries
- **`data/warehouse_data.sql`**: 26 strategically located warehouses across North America
- **`data/supplier_data.sql`**: 30+ suppliers with geographic coordinates for map visualization
- **`data/inventory_items_data.sql`**: 100+ realistic retail inventory items across all categories

### Data Folder Structure

```
data/
├── category_data.sql          # Product categories (TPCDS-aligned)
├── warehouse_data.sql         # Warehouse locations with coordinates
├── supplier_data.sql          # Supplier information with geographic data
├── inventory_items_data.sql   # Complete inventory items dataset
└── load_all_data.sql          # Master script to load all data
```

### Loading Sample Data

#### Option 1: Load All Data at Once (Recommended)
```sql
-- Load all sample data in the correct order
\i data/load_all_data.sql
```

#### Option 2: Load Data Individually
```sql
-- 1. Load categories first (no dependencies)
\i data/category_data.sql

-- 2. Load warehouses (no dependencies)
\i data/warehouse_data.sql

-- 3. Load suppliers (no dependencies)
\i data/supplier_data.sql

-- 4. Load inventory items (depends on categories, warehouses, suppliers)
\i data/inventory_items_data.sql
```

### Using Sample Data

The application automatically loads comprehensive sample data on first startup (when tables are empty):
- 40+ realistic product categories across various industries
- 26 strategically located warehouses across North America with geographic coordinates
- 30+ suppliers with complete contact information and location data
- 100+ inventory items with realistic pricing and stock levels

All sample data is TPCDS-aligned for industry-standard analytics and testing.

## Setting Up Demand Forecasting

The demand forecasting feature uses Databricks Model Serving to provide AI-powered inventory recommendations. To enable this feature:

### Step 1: Generate Training Data

Use the provided notebook to generate synthetic sales data:
- Navigate to `notebooks/2 - DEMAND FORECASTING/2.1 - Generate Synthetic Sales Data.ipynb`
- Run all cells to create historical sales data in your catalog
- This creates the foundation for training the forecasting model

### Step 2: Train and Deploy the Model

Train and deploy the demand forecasting model:
- Open `notebooks/2 - DEMAND FORECASTING/2.2 - Demand Forecasting.ipynb`
- Run all cells to train the XGBoost forecasting model
- The notebook automatically deploys the model to a Databricks Model Serving endpoint
- Note the endpoint name (e.g., `demand-forecast-endpoint`)

### Step 3: Configure the Application

Add the model endpoint to your app.yaml or environment variables:

```yaml
env:
  - name: MODEL_ENDPOINT_NAME
    value: "demand-forecast-endpoint"
```

Or set as an environment variable:

```bash
export MODEL_ENDPOINT_NAME="demand-forecast-endpoint"
```

### How It Works

When enabled, the demand forecasting feature:
- Predicts demand for the next 90 days (3 months) based on historical sales patterns
- Calculates safety stock as 10% of forecasted demand
- Provides intelligent recommendations when adding or editing inventory items
- Falls back to minimum stock logic if the model endpoint is unavailable or not configured
- Displays reasoning for all suggestions to help you make informed decisions

The forecasts consider:
- Warehouse location patterns
- Product category trends
- Seasonal variations
- Historical sales velocity

## Database Schema

The application uses a relational schema with the following tables:

### Core Tables
- **`inventory_items`**: Main inventory items table with foreign keys to categories, warehouses, and suppliers
- **`inventory_category`**: Product categories for organizing items
- **`inventory_warehouse`**: Warehouse locations with geographic data
- **`inventory_supplier`**: Supplier information for procurement tracking

### Relationships
- Each inventory item belongs to one category (required)
- Each inventory item can be assigned to one warehouse (optional)
- Each inventory item can be linked to one supplier (optional)
- Demand forecasts are linked to warehouses and categories for prediction accuracy

### Foreign Table Sync
All tables are synced from Lakebase to Unity Catalog as foreign tables at near-real-time latency, enabling:
- Analytics on transactional data
- Integration with Databricks workflows
- AI/BI dashboard connectivity
- Delta Lake integration

## Entity Management

The application provides comprehensive management interfaces for all inventory entities:

### Categories Management
- Create, edit, and delete product categories
- Organize inventory items by category for better reporting
- View item counts per category
- Categories cannot be deleted if they have associated items

### Warehouses Management
- Manage multiple warehouse locations
- Track geographic data including:
  - Address, city, state, country, county, zip code
  - Latitude and longitude coordinates for mapping
  - Contact person, phone, and email
- Associate inventory items with specific warehouses
- Visualize warehouse locations on maps (via embedded dashboards)

### Suppliers Management
- Maintain supplier database with complete information:
  - Contact person, email, phone
  - Full address with geographic coordinates
  - Website URL
  - Tax ID and payment terms
- Link inventory items to suppliers for procurement tracking
- Suppliers with associated items require confirmation before deletion

## Important Notes

- **CSV uploads only ADD new items** - they don't update or delete existing items
- **Data validation is strict** - invalid rows are skipped with detailed error messages
- **File encoding should be UTF-8** for best compatibility
- **Templates are automatically generated** with the latest format requirements
- **App Resources are required** for Databricks App deployment - ensure both database and secret scope resources are properly configured
- **Demand forecasting is optional** - the app works with or without a configured model endpoint
- **Geographic coordinates are optional** but enable map-based visualizations in dashboards

## Troubleshooting

### Common Issues:

1. **Database Connection Errors**: 
   - Verify the database resource is added with "Can Connect" permission
   - Check that your PGUSER has proper OAuth identity mapping in the database
   - Ensure the Lakebase instance is running and accessible

2. **Secret Key Errors**:
   - Ensure the secret scope resource is added with "Can Read" permission
   - Verify the SECRET_KEY exists in the secret scope
   - Check that the secret scope name matches the one in app resources

3. **Table Creation Issues**:
   - The app automatically creates the schema and tables on first run
   - Ensure your database user has CREATE privileges
   - Check that the schema name doesn't conflict with existing schemas

4. **Dashboard Not Loading**:
   - Verify DATABRICKS_HOST and DASHBOARD_ID are correctly set
   - Ensure the dashboard exists and is accessible
   - Check OAuth token validity using `/api/token-status` endpoint
   - Verify the app has permissions to access the dashboard

5. **Demand Forecasting Not Working**:
   - Check that MODEL_ENDPOINT_NAME is set correctly
   - Verify the Model Serving endpoint is deployed and running
   - Ensure the app's OAuth token has permissions to call the endpoint
   - Review the endpoint URL format in logs
   - The app will fall back to minimum stock logic if the endpoint is unavailable

6. **Sample Data Not Loading**:
   - Ensure LOAD_SAMPLE_DATA is set to "true" (or not set, as true is default)
   - Check that tables are empty when the app starts
   - Verify SQL script files exist in the data/ directory
   - Review logs for SQL execution errors

### OAuth Identity Mapping:

If you encounter OAuth identity mismatch errors, run this SQL in your Lakebase instance:

```sql
-- Replace with your actual email and service principal ID
ALTER ROLE "your_username@domain.com" 
SET databricks.oauth.identity = 'your-app-service-principal-id';
```

### Debugging Tips:

- Set `DEBUG_SQL=true` to see all SQL queries being executed
- Check the application logs for detailed error messages
- Use `/api/token-status` to verify OAuth token validity
- Use `/api/dashboard-config` to check dashboard configuration
- Test demand forecasting with `/api/demand-forecast` endpoint directly
