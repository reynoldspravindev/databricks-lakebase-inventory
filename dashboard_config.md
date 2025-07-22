# Databricks AI/BI Dashboard Integration Guide

## 🎯 **Overview**

This guide shows how to embed Databricks AI/BI dashboards directly into your inventory management app, following the patterns from the [Lakehouse App demo](https://github.com/souvik-databricks/Demo-Lakehouse-App-powered-by-Unity-Catalog-data/tree/main).

## 📋 **Prerequisites**

1. **Databricks Workspace** with AI/BI enabled
2. **Unity Catalog** access for data governance
3. **Dashboard ID** from your Databricks dashboard
4. **OAuth token** authentication (already configured in your app)

## ⚙️ **Configuration**

### **1. Environment Variables**

Add these to your environment or `.env` file:

```bash
# Databricks Configuration
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DASHBOARD_ID=01ef1234-5678-9abc-def0-123456789abc

# Database Configuration (existing)
PGDATABASE=your_database
PGUSER=your_user
PGHOST=your_host
PGPORT=5432
```

### **2. Dashboard Creation**

Create a dashboard in Databricks that analyzes your inventory data:

```sql
-- Example: Inventory Analytics Dashboard Queries

-- 1. Inventory Overview
SELECT 
    category,
    COUNT(*) as item_count,
    SUM(quantity) as total_quantity,
    SUM(quantity * unit_price) as total_value,
    AVG(unit_price) as avg_price
FROM inventory_app.inventory_items 
GROUP BY category
ORDER BY total_value DESC;

-- 2. Low Stock Analysis
SELECT 
    item_name,
    category,
    quantity,
    minimum_stock,
    (minimum_stock - quantity) as shortage,
    supplier,
    DATEDIFF(NOW(), last_updated) as days_since_update
FROM inventory_app.inventory_items 
WHERE minimum_stock IS NOT NULL 
    AND quantity <= minimum_stock
ORDER BY shortage DESC;

-- 3. Inventory Trends
SELECT 
    DATE(date_added) as add_date,
    COUNT(*) as items_added,
    SUM(quantity * unit_price) as value_added
FROM inventory_app.inventory_items 
WHERE date_added >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(date_added)
ORDER BY add_date;

-- 4. Supplier Performance
SELECT 
    supplier,
    COUNT(*) as item_count,
    SUM(quantity) as total_units,
    SUM(quantity * unit_price) as total_value,
    COUNT(CASE WHEN quantity <= minimum_stock THEN 1 END) as low_stock_items
FROM inventory_app.inventory_items 
WHERE supplier IS NOT NULL
GROUP BY supplier
ORDER BY total_value DESC;
```

### **3. Row-Level Security (Optional)**

Implement Unity Catalog row-level security:

```sql
-- Create a row filter function
CREATE OR REPLACE FUNCTION inventory_app.user_filter(user_role STRING)
RETURNS BOOLEAN
RETURN 
  CASE 
    WHEN user_role = 'admin' THEN TRUE
    WHEN user_role = 'manager' AND location IN ('Warehouse A', 'Office Storage') THEN TRUE
    WHEN user_role = 'employee' AND category = 'Office Supplies' THEN TRUE
    ELSE FALSE
  END;

-- Apply the filter to your table
ALTER TABLE inventory_app.inventory_items 
SET ROW FILTER inventory_app.user_filter(current_user());
```

## 🚀 **Usage Examples**

### **Basic Integration**

```python
# In your app.py, the dashboard is already configured
# Just set the environment variables and it will work

# Get dashboard URL
dashboard_url = get_dashboard_embed_url()

# Check if dashboard is configured
if dashboard_url:
    print("✅ Dashboard ready to embed")
else:
    print("❌ Dashboard not configured - set DASHBOARD_ID")
```

### **Advanced Configuration**

```python
# Custom dashboard parameters
def get_dashboard_embed_url_with_filters(category=None, location=None):
    """Generate dashboard URL with custom filters."""
    base_url = get_dashboard_embed_url()
    
    if not base_url:
        return None
    
    # Add filter parameters
    params = []
    if category:
        params.append(f"category={category}")
    if location:
        params.append(f"location={location}")
    
    if params:
        separator = "&" if "?" in base_url else "?"
        base_url += separator + "&".join(params)
    
    return base_url
```

## 🔒 **Security Features**

### **Authentication Flow**
1. **OAuth Token** - Reuses existing Databricks authentication
2. **Token Refresh** - Automatic token renewal every 15 minutes
3. **Origin Validation** - iframe security with origin checking
4. **Row-Level Security** - Unity Catalog governance enforced

### **Iframe Security**
```javascript
// Content Security Policy headers
app.config['CSP'] = {
    'frame-src': ['self', '*.cloud.databricks.com'],
    'script-src': ['self', 'unsafe-inline'],
    'connect-src': ['self', '*.cloud.databricks.com']
}
```

## 🎨 **Dashboard Features**

### **Embedded Dashboard Includes:**
- ✅ **Real-time Data** - Live updates from inventory changes
- ✅ **Interactive Filters** - Category, location, date range filtering
- ✅ **Responsive Design** - Works on desktop and mobile
- ✅ **Fullscreen Mode** - Toggle for focused analysis
- ✅ **Auto-refresh** - Periodic data updates
- ✅ **Error Handling** - Graceful fallbacks for connection issues

### **Sample Dashboard Visualizations:**
1. **Inventory Value by Category** (Bar Chart)
2. **Stock Levels Over Time** (Line Chart)
3. **Low Stock Alerts** (Table)
4. **Supplier Performance** (Pie Chart)
5. **Location Utilization** (Heatmap)
6. **Inventory Trends** (Time Series)

## 🛠️ **Deployment Options**

### **Option 1: YAML Configuration**
```yaml
# app.yaml
script: app_with_csv.py
env_variables:
  DASHBOARD_ID: "01ef1234-5678-9abc-def0-123456789abc"
  DATABRICKS_HOST: "https://your-workspace.cloud.databricks.com"
```

### **Option 2: Environment File**
```bash
# .env
DASHBOARD_ID=01ef1234-5678-9abc-def0-123456789abc
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
```

### **Option 3: Runtime Configuration**
```python
# Set in your app startup
os.environ['DASHBOARD_ID'] = 'your-dashboard-id'
os.environ['DATABRICKS_HOST'] = 'https://your-workspace.cloud.databricks.com'
```

## 🎯 **Getting Dashboard ID**

1. **Open your dashboard** in Databricks
2. **Copy URL** - Look for the ID in the URL:
   ```
   https://your-workspace.cloud.databricks.com/dashboardsv3/01ef1234-5678-9abc-def0-123456789abc
   ```
3. **Extract ID** - The UUID after `/dashboardsv3/` is your Dashboard ID

## 🧪 **Testing**

### **Local Testing**
```bash
# Set environment variables
export DASHBOARD_ID="your-dashboard-id"
export DATABRICKS_HOST="your-workspace-url"

# Run the app
python app_with_csv.py
```

### **API Testing**
```bash
# Check dashboard configuration
curl http://localhost:5000/api/dashboard-config

# Check token status  
curl http://localhost:5000/api/token-status
```

## 🔄 **Integration Benefits**

✅ **Unified Experience** - Analytics embedded directly in inventory app
✅ **Single Sign-On** - Same authentication for app and dashboard  
✅ **Real-time Insights** - Live data from the same database
✅ **Governance** - Unity Catalog security applies automatically
✅ **Responsive Design** - Works seamlessly across devices
✅ **Cost Effective** - No additional BI tool licensing needed

This integration provides a powerful analytics layer on top of your inventory data while maintaining the security and governance of the Databricks platform! 