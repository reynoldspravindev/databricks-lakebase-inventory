# Model Serving Endpoint Integration

## Overview

The demand forecasting feature has been updated to use a Databricks Model Serving endpoint for real-time predictions. The system now calls your ML model to predict demand for the next 3 months and provides intelligent inventory suggestions based on the predictions.

## Changes Made

### 1. Configuration Files

#### `config.py`
- Added configuration support for model endpoint URL and endpoint name
- Added methods:
  - `get_model_endpoint_name()`: Returns the endpoint name
  - `get_model_endpoint_url()`: Returns the full endpoint invocation URL
  - `is_model_endpoint_configured()`: Checks if endpoint is configured
  - Updated `print_config_summary()` to show model endpoint configuration status

#### `app.yaml`
- Added one new environment variable:
  - `MODEL_ENDPOINT_NAME`: The name of your model serving endpoint
- Reuses existing `DATABRICKS_HOST` for the workspace URL

### 2. Backend Changes

#### `app.py`
- Added `requests` and `pandas` imports for HTTP calls and data manipulation
- Updated `get_demand_forecast_suggestion()` function:
  - Now accepts `item_name` as a required parameter
  - Calls the model serving endpoint with batch data for 3 months
  - Prepares batch input with warehouse_id, category_id, item_name, and month
  - Sums predictions across all 3 months to get total forecasted demand
  - Returns suggestions based on 90-day forecast instead of 30-day
  - Includes graceful fallback to minimum stock logic if endpoint is not configured or fails

- Updated `/api/demand-forecast` endpoint:
  - Now requires `item_name` parameter
  - Returns error if `item_name` is missing

### 3. Frontend Changes

#### `templates/add_item.html`
- Updated `getDemandForecast()` JavaScript function:
  - Gets `item_name` from the form
  - Validates that item_name is not empty
  - Encodes item_name for URL parameter
  - Passes item_name to the API call

#### `templates/edit_item.html`
- Updated `getDemandForecast()` JavaScript function:
  - Gets `item_name` from the form
  - Validates that item_name is not empty
  - Encodes item_name for URL parameter
  - Passes item_name to the API call

### 4. Dependencies

#### `requirements.txt`
- Added `pandas>=2.0.0` for DataFrame operations

## Configuration

### Step 1: Update Environment Variables

Update your `app.yaml` file with your actual model endpoint name:

```yaml
- name: 'MODEL_ENDPOINT_NAME'
  value: "your-demand-forecast-endpoint-name"  # Replace with your actual endpoint name
```

The system will automatically use the existing `DATABRICKS_HOST` variable for the workspace URL.

Alternatively, set this as an environment variable:

```bash
export MODEL_ENDPOINT_NAME="your-demand-forecast-endpoint-name"
```

**Note**: The system reuses the existing `DATABRICKS_HOST` environment variable, so no additional URL configuration is needed.

### Step 2: Verify Model Endpoint

Ensure your model serving endpoint is configured to accept the following input schema:

**Input Columns:**
- `warehouse_id` (float)
- `category_id` (float)
- `item_name` (string)
- `month` (float)

**Input Format:**
```json
{
  "dataframe_split": {
    "columns": ["warehouse_id", "category_id", "item_name", "month"],
    "data": [
      [1.0, 9.0, "Gaming Controller", 1.0],
      [1.0, 9.0, "Gaming Controller", 2.0],
      [1.0, 9.0, "Gaming Controller", 3.0]
    ]
  }
}
```

**Expected Output:**
```json
{
  "predictions": [62, 51, 64]  // One prediction per month
}
```

The system will sum these predictions to calculate the total 90-day forecast.

## How It Works

1. **User Action**: When a user clicks the "Get AI Forecast" button while adding or editing an inventory item, the system:
   - Collects: warehouse_id, category_id, item_name, current_quantity, minimum_stock, and new_quantity
   - Calculates the next 3 months (e.g., if current month is 10, it sends months [11, 12, 1])

2. **Model Call**: The system creates a batch request with 3 rows (one per month) and sends it to your model endpoint

3. **Prediction Processing**: The predictions are summed to get the total forecasted demand for the next 90 days

4. **Inventory Calculation**:
   - **Safety Stock**: Maximum of minimum_stock or 10% of forecast
   - **Recommended Total**: Total forecast + safety stock
   - **Suggested Quantity**: Recommendation based on current inventory, new quantity being added, and forecast

5. **User Feedback**: The suggestion is displayed with reasoning, and the user can apply it with one click

## Fallback Behavior

If the model endpoint is not configured or fails:
- The system falls back to using minimum stock logic
- The user still receives a suggestion based on minimum stock levels
- An informative message is displayed in the reasoning

## Testing

### Test the Configuration

1. Start your application
2. Check the console output for configuration summary:
   ```
   📋 Configuration Summary:
     Model endpoint configured: True
     Model endpoint name: your-endpoint-name
   ```

3. Navigate to Add Item or Edit Item page
4. Fill in warehouse, category, and item name
5. Click the "Get AI Forecast" button (magic wand icon)
6. Verify that you receive a forecast suggestion

### Sample Test Data

Based on the image you provided, try these combinations:
- Warehouse ID: 1, Category ID: 9, Item Name: "Gaming Controller"
- Warehouse ID: 4, Category ID: 5, Item Name: "Bestselling Novel"

## Troubleshooting

### Common Issues

1. **"Model endpoint not configured" message**
   - Verify MODEL_ENDPOINT_NAME is set in app.yaml or environment
   - Verify DATABRICKS_HOST is set correctly
   - Restart the application after setting environment variables

2. **"Error retrieving AI forecast"**
   - Check that your model endpoint is running and accessible
   - Verify OAuth token has permissions to call the endpoint
   - Check application logs for detailed error messages

3. **"item_name is required" error**
   - Ensure item_name field is filled before clicking the forecast button

### Debug Mode

Enable debug logging by checking the application console output when calling the forecast API. The system logs:
- Endpoint URL being called
- Model predictions received
- Total forecast calculated

## Benefits

✅ **Real-time AI Predictions**: Leverage your trained ML model for accurate demand forecasting

✅ **90-Day Forecast**: Predictions for the next 3 months provide better long-term planning

✅ **Intelligent Suggestions**: Combines forecast with safety stock calculations

✅ **Graceful Fallback**: System continues to work even if model endpoint is unavailable

✅ **User-Friendly**: One-click forecast suggestions with clear reasoning

## Next Steps

1. Update `app.yaml` with your actual endpoint name and URL
2. Restart your application
3. Test the forecast feature with sample items
4. Monitor model endpoint performance and adjust as needed

## Support

For issues or questions:
- Check application logs for detailed error messages
- Verify model endpoint is accessible via Databricks workspace
- Ensure OAuth token has proper permissions

