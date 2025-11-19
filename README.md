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

- **AI-Powered Demand Forecasting**: Leverage Databricks Model Serving to predict inventory needs for the next 90 days. The system intelligently recommends optimal stock levels based on warehouse location, product category, and historical sales patterns, with automatic safety stock calculations and fallback logic for continuous operation.

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

#### Prerequisites

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

### Steps:
- Import the notebooks folder to a Databricks Workspace. Ensure the folder hierarachy is maintained. Or, clone this repo on the Databricks workspace.
- Set the config variables in "/notebooks/0 - SETUP/0 - Setup.ipynb"
- Start running the notebooks under the "/notebooks/1 - DEPLOY ASSETS/" and the "/notebooks/1 - DEMAND FORECASTING/" folders in the respective order.
- These notebooks are self explanatory.  



## Databricks Platform Integration

### Lakebase (Managed Postgres) - Transactional Data Layer
This application showcases **Databricks Lakebase** as the operational database for transactional inventory management:
- **Fully Managed PostgreSQL**: No infrastructure management, automatic backups, high availability
- **Separation of Storage & Compute**: Leverage Databricks' cloud-native architecture
- **Near Real-Time Sync**: Automatic bi-directional sync between Lakebase and Unity Catalog as foreign tables
- **ACID Compliance**: Full transactional consistency for inventory operations
- **Native OAuth Integration**: Seamless authentication with Databricks workspace identity

### Unity Catalog - Data Governance
All inventory data is governed through **Unity Catalog**, providing enterprise-grade capabilities:
- **Centralized Governance**: Single source of truth for both transactional (Lakebase) and analytical (Delta Lake) data
- **Fine-Grained Access Control**: Row and column-level security across all tables
- **Complete Data Lineage**: Track data flow from transactional operations to analytics
- **Audit Trails**: Full visibility into data access and modifications
- **Dynamic Data Masking**: Protect sensitive information while maintaining usability

### Databricks Model Serving - AI/ML Integration
Leverage **Databricks Model Serving** for intelligent inventory forecasting:
- **XGBoost Models**: Pre-trained demand forecasting models for 90-day predictions
- **Serverless Inference**: Auto-scaling model endpoints with minimal latency
- **Real-Time Predictions**: Instant inventory recommendations during data entry
- **MLflow Integration**: Model versioning, tracking, and governance
- **Fallback Logic**: Graceful degradation when endpoints are unavailable

### Lakehouse Apps - Application Hosting
Deploy and manage the entire application within **Databricks Lakehouse Apps**:
- **Native Hosting**: Run web applications directly in Databricks workspace
- **Auto-Scaling Compute**: Dynamic resource allocation based on demand
- **Secret Management**: Secure credential storage with Databricks Secret Scope
- **Embedded Analytics**: Direct integration with AI/BI Dashboards
- **OAuth Security**: Workspace-native authentication and authorization

### AI/BI Dashboards - Embedded Analytics
**Databricks AI/BI Dashboards** provide real-time insights within the application:
- **Live Data Connectivity**: Direct queries to Lakebase foreign tables
- **Interactive Visualizations**: Drill-down capabilities and filtering
- **Secure Embedding**: Token-based dashboard embedding with auto-refresh
- **Unified Analytics**: Single platform for operational and analytical workloads

## Application Features

This reference application demonstrates key inventory management capabilities powered by Databricks:

- **Transactional CRUD Operations**: Full inventory lifecycle management backed by Lakebase
- **SKU & Category Management**: Organize products with multi-level hierarchies
- **Multi-Warehouse Support**: Track inventory across locations with geographic data
- **Supplier Management**: Maintain procurement relationships
- **Bulk Data Import**: CSV uploads with validation and error handling
- **Low Stock Alerts**: Automated threshold monitoring
- **AI-Powered Recommendations**: Model Serving integration for demand forecasting
- **Real-Time Analytics**: Embedded dashboards for operational insights
- **Order Management System**: Complete order tracking with OMS integration


## API Endpoints

The application provides RESTful API endpoints demonstrating programmatic access to Lakebase data:

- **`GET /api/items`**: Retrieve all inventory items as JSON
- **`GET /api/skus-by-category/<category_id>`**: Retrieve SKUs filtered by category
- **`GET /api/current-inventory`**: Get current inventory quantity for a SKU at a warehouse
- **`GET /api/token-status`**: Check OAuth token validity
- **`GET /api/dashboard-config`**: Get dashboard configuration status
- **`GET /api/demand-forecast`**: Get AI-powered demand forecast suggestions from Model Serving
- **`POST /api/reset-data`**: Reset all data and identity sequences

## Databricks Notebooks

The repository includes notebooks that demonstrate Databricks workflows and ML lifecycle:

### Setup & Deployment (`notebooks/0 - SETUP/`, `notebooks/1 - DEPLOY ASSETS/`)
- Configure Databricks resources (Lakebase, Unity Catalog, Secret Scope)
- Deploy database schema and initialize foreign table sync
- Set up app permissions and resource grants

### AI/ML Workflow (`notebooks/2 - DEMAND FORECASTING/`)
- Generate synthetic sales data for model training
- Train XGBoost forecasting models using Databricks ML Runtime
- Register models in MLflow and deploy to Model Serving endpoints
- Demonstrate end-to-end ML lifecycle on the Lakehouse Platform

## Configuration

### Databricks Platform Configuration

Configure the application to leverage Databricks services:

- **`DATABRICKS_HOST`**: Workspace URL for API access and dashboard embedding
- **`POSTGRES_HOST`**: Lakebase connection endpoint
- **`POSTGRES_SCHEMA`**: Schema name in Lakebase (default: `inventory_app`)
- **`SECRET_SCOPE`**: Databricks Secret Scope name for secure credential storage
- **`MODEL_ENDPOINT_NAME`**: Model Serving endpoint for demand forecasting (optional)
- **`DASHBOARD_ID`**: AI/BI Dashboard ID for embedded analytics (optional)

### Data Management Variables

- **`FORCE_DATA_RESET`**: Reset all data on startup (preserves ML forecast history)
- **`LOAD_SAMPLE_DATA`**: Auto-populate sample data (default: `"true"`)
- **`DEBUG_SQL`**: Enable SQL query logging for debugging
- **`POSTGRES_SKU_TABLE`**, **`POSTGRES_CATEGORY_TABLE`**, etc.: Customize table names

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

- **`data/category_data.sql`**: 10 realistic product categories across various industries
- **`data/sku_data.sql`**: 50 product SKUs with pricing and descriptions
- **`data/warehouse_data.sql`**: 26 strategically located warehouses across North America
- **`data/supplier_data.sql`**: 30+ suppliers with geographic coordinates for map visualization
- **`data/inventory_items_data.sql`**: 100+ realistic retail inventory items across all categories

### Data Folder Structure

```
data/
├── category_data.sql          # Product categories
├── sku_data.sql               # Product SKUs with pricing
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

-- 2. Load SKUs (depends on categories)
\i data/sku_data.sql

-- 3. Load warehouses (no dependencies)
\i data/warehouse_data.sql

-- 4. Load suppliers (no dependencies)
\i data/supplier_data.sql

-- 5. Load inventory items (depends on SKUs, warehouses, suppliers)
\i data/inventory_items_data.sql
```

### Using Sample Data

The application automatically loads comprehensive sample data on first startup (when tables are empty):
- 10 realistic product categories across various industries
- 50 product SKUs with detailed pricing and descriptions
- 26 strategically located warehouses across North America with geographic coordinates
- 30+ suppliers with complete contact information and location data
- 100+ inventory items with realistic pricing and stock levels

## Databricks Model Serving Integration

This application demonstrates how **Databricks Model Serving** provides real-time AI predictions within operational workflows:

### End-to-End ML Lifecycle on Databricks

1. **Data Generation**: Synthetic sales data created in Delta Lake tables
2. **Model Training**: XGBoost models trained using Databricks ML Runtime
3. **MLflow Registry**: Models versioned and tracked in Unity Catalog
4. **Model Serving**: Auto-scaling serverless endpoints for inference
5. **Application Integration**: REST API calls from web app for real-time predictions

### Architecture Flow
```
Lakebase (Inventory) → Unity Catalog (Foreign Tables) → Delta Lake (Sales History)
                                                               ↓
                                                         Model Training
                                                               ↓
                                                         MLflow Registry
                                                               ↓
                                                      Model Serving Endpoint
                                                               ↓
                                                    Lakehouse App (Predictions)
```

### Business Value
- **Real-Time Intelligence**: AI recommendations during data entry, not after-the-fact
- **No Infrastructure**: Serverless endpoints scale automatically
- **Unified Platform**: Training and inference on the same data, no data movement
- **Governance**: Models governed by Unity Catalog like any other asset
- **Fallback Logic**: Graceful degradation maintains app functionality

## Lakebase Schema & Unity Catalog Sync

The application demonstrates a transactional schema in **Lakebase** with automatic sync to **Unity Catalog**:

### Lakebase Tables (Transactional Layer)
- **`inventory_items`**: Core inventory records with FK relationships
- **`inventory_sku`**: Product master data with pricing
- **`inventory_category`**: Product categorization
- **`inventory_warehouse`**: Location master with geographic coordinates
- **`inventory_supplier`**: Vendor management
- **`inventory_demand_forecast`**: ML model predictions (historical)

### Unity Catalog Foreign Tables (Analytical Layer)
All Lakebase tables are automatically synced to Unity Catalog as **foreign tables**:
- **Near Real-Time Latency**: Changes in Lakebase appear in Unity Catalog within seconds
- **Bi-Directional Sync**: Write to Unity Catalog, read from Lakebase (Reverse ETL capability)
- **Query Federation**: Join transactional data with Delta Lake tables seamlessly
- **Unified Governance**: Single set of permissions managed through Unity Catalog
- **Analytics Ready**: Power AI/BI dashboards, ML models, and Databricks workflows with live operational data

This architecture enables true **Lakehouse convergence** - OLTP and OLAP workloads on a single platform.

## Why Databricks for Inventory Management?

This application demonstrates how Databricks unifies traditionally separate systems into a single platform:

### Traditional Architecture (Before Databricks)
```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ PostgreSQL  │────▶│ ETL Pipeline │────▶│ Data Warehouse│
│  (OLTP)     │     │ (Batch/CDC)  │     │  (Analytics)  │
└─────────────┘     └──────────────┘     └──────────────┘
        │                                         │
        ▼                                         ▼
   Web App                                   BI Tools
```
**Challenges**: Data duplication, latency, complexity, multiple security layers

### Lakehouse Architecture (With Databricks)
```
┌──────────────────────────────────────────┐
│         Databricks Lakehouse             │
│  ┌────────────┐  ┌──────────────────┐   │
│  │  Lakebase  │◀▶│ Unity Catalog    │   │
│  │  (OLTP)    │  │ (Foreign Tables) │   │
│  └────────────┘  └──────────────────┘   │
│         ▲                  ▲             │
│         │                  │             │
│  ┌──────┴──────┐   ┌──────┴─────────┐   │
│  │ Lakehouse   │   │ AI/BI Dashboards│   │
│  │    Apps     │   │ Model Serving   │   │
│  └─────────────┘   └─────────────────┘   │
└──────────────────────────────────────────┘
```
**Benefits**: 
- **Single Platform**: No separate systems to manage
- **Real-Time Sync**: Near-instant data availability for analytics
- **Unified Governance**: One security model via Unity Catalog
- **AI/ML Ready**: Models train on live operational data
- **Lower TCO**: No ETL infrastructure, no data duplication

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
