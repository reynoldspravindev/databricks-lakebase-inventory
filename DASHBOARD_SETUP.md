# Dashboard Setup Guide

Your dashboard functionality is now available in the Flask app! The dashboard uses a smart proxy approach to embed Databricks dashboards directly in your app.

## How It Works

The app now includes a **proxy server** that bypasses Azure Databricks iframe restrictions:

✅ **Embedded dashboard** - Full Databricks dashboard displayed directly in your app  
✅ **Proxy authentication** - Automatic OAuth token handling through the proxy  
✅ **Fallback options** - Links to open in Databricks if embedding fails  
✅ **Auto-refresh** - Dashboard updates automatically every 5 minutes  

## Environment Variables Required

### 1. Dashboard ID
```bash
export DASHBOARD_ID="your-databricks-dashboard-id"
```

To find your Dashboard ID:
1. Go to your Azure Databricks workspace
2. Open the dashboard you want to link
3. Look at the URL: `https://adb-xxx.11.azuredatabricks.net/sql/dashboards/[DASHBOARD_ID]`
4. Copy the ID from the URL

### 2. Databricks Host (if not auto-detected)
```bash
export DATABRICKS_HOST="https://adb-xxx.11.azuredatabricks.net"
```

## Testing the Dashboard

1. **Start your Flask app:**
   ```bash
   python app.py
   ```

2. **Access the dashboard:**
   - Go to `http://localhost:8080/dashboard`
   - Or click "Analytics" in the navigation menu

3. **View analytics:**
   - See quick stats in the app
   - Click "View Analytics" to open full dashboard in Databricks

## What You'll See

### In-App Analytics Preview
- **Quick Stats**: Total items, low stock count, inventory value, categories
- **Stock Status**: Visual distribution of stock levels
- **Quick Actions**: Links to manage inventory

### Full Analytics (in Databricks)
- **Advanced Charts**: Trends, forecasts, detailed breakdowns
- **Custom Queries**: Complex analytics and reporting
- **Real-time Data**: Live updates from your inventory database

## Troubleshooting

### Common Issues

❌ **Dashboard shows loading spinner forever**: Authentication or network issue  
✅ **Solution**: Check the console for errors, verify Dashboard ID, and use the "Retry" button

❌ **"Dashboard not configured"**: Dashboard ID not set  
✅ **Solution**: Set the `DASHBOARD_ID` environment variable

❌ **Proxy authentication fails**: OAuth token issues  
✅ **Solution**: Restart the app to refresh tokens, check Databricks workspace access

❌ **Dashboard content appears but looks broken**: CSS/JS loading issues  
✅ **Solution**: Use the "Open in Databricks" button as fallback

### API Endpoints for Debugging
- `/api/dashboard-config` - Check dashboard configuration
- `/api/token-status` - Check OAuth token status

## Creating a Dashboard in Databricks

If you don't have a dashboard yet:

1. **Go to Databricks SQL** in your workspace
2. **Create queries** using your `inventory_app.inventory_items` table
3. **Build visualizations** (charts, tables, etc.)
4. **Create a dashboard** and add your visualizations
5. **Copy the dashboard ID** from the URL
6. **Set the environment variable** and restart your app

## Example Databricks Queries

Here are some useful queries for your inventory dashboard:

```sql
-- Low Stock Items
SELECT item_name, quantity, minimum_stock, supplier
FROM inventory_app.inventory_items 
WHERE quantity <= minimum_stock;

-- Inventory Value by Category
SELECT category, SUM(quantity * unit_price) as total_value
FROM inventory_app.inventory_items 
GROUP BY category;

-- Stock Levels Over Time
SELECT date_added, COUNT(*) as items_added
FROM inventory_app.inventory_items 
GROUP BY date_added
ORDER BY date_added;
```

Your inventory app now provides a seamless bridge to powerful Databricks analytics! 