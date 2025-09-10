# Analytics Features - Databricks Integration

This document describes the new analytics features integrated into the Flask inventory management application, including Databricks Dashboard embedding and AI Assistant (Genie) functionality.

## 🚀 New Features

### 1. Analytics Menu
- **Location**: Navigation bar dropdown menu
- **Items**: 
  - Dashboard - Embedded Databricks AI/BI dashboard
  - AI Assistant (Genie) - Chat interface for data analysis

### 2. Databricks Dashboard Integration
- **Route**: `/dashboard`
- **Features**:
  - Embedded Databricks AI/BI dashboard
  - Real-time data visualization
  - OAuth authentication
  - Fullscreen mode
  - Auto-refresh capabilities
  - Error handling and fallback UI

### 3. AI Assistant (Genie) Integration
- **Route**: `/genie`
- **Features**:
  - Natural language queries about inventory data
  - Real-time conversation with AI
  - Query result visualization
  - Suggested queries for common analysis
  - Conversation history
  - Generated SQL code display
  - Data export capabilities

## 🔧 Configuration

### Environment Variables

#### Required (existing)
```bash
PGDATABASE=your_database_name
PGUSER=your_username
PGHOST=your_host
PGPORT=5432
PGSSLMODE=require
```

#### Optional (for analytics features)
```bash
# Dashboard Configuration
DASHBOARD_ID=your_dashboard_id
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com

# Genie Configuration  
GENIE_SPACE_ID=your_genie_space_id
```

### Finding Your IDs

#### Dashboard ID
1. Open your Databricks workspace
2. Navigate to AI/BI → Dashboards
3. Open your dashboard
4. Click "Share" → "Embed iframe"
5. Copy the dashboard ID from the URL

#### Genie Space ID
1. Open your Databricks workspace
2. Navigate to AI/BI → Genie
3. Open your Genie space
4. Copy the space ID from the URL (format: `rooms/SPACE-ID?o=`)

## 📁 New Files

### Backend
- `genie_service.py` - Genie conversation management service
- `test_integration.py` - Integration testing script

### Frontend
- `templates/genie.html` - AI Assistant chat interface

### Updated Files
- `app.py` - Added Genie routes and service integration
- `templates/base.html` - Added Analytics dropdown menu
- `requirements.txt` - Added pandas dependency

## 🛠️ Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
export DASHBOARD_ID="your_dashboard_id"
export GENIE_SPACE_ID="your_genie_space_id"
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
```

### 3. Test Integration
```bash
python test_integration.py
```

### 4. Run Application
```bash
python app.py
```

## 🎯 Usage

### Dashboard
1. Navigate to **Analytics** → **Dashboard**
2. View embedded Databricks dashboard
3. Use controls to refresh, fullscreen, or open in Databricks
4. Dashboard automatically refreshes every 5 minutes

### AI Assistant (Genie)
1. Navigate to **Analytics** → **AI Assistant (Genie)**
2. Ask questions about your inventory data
3. Use suggested queries or type custom questions
4. View generated SQL and query results
5. Export data or view conversation history

### Example Queries
- "What are the top 10 items by inventory value?"
- "Which categories have the most items?"
- "Show me items that are low in stock"
- "What's the total inventory value by category?"
- "Which suppliers provide the most items?"

## 🔒 Security

### Authentication
- Uses existing OAuth token system
- Automatic token refresh
- Secure iframe embedding

### Permissions Required
- **Dashboard**: `CAN VIEW` permission on the dashboard
- **Genie**: `CAN VIEW` permission on the Genie Space
- **Data**: `SELECT` permission on Unity Catalog tables

### Data Access
- Row-level security through Unity Catalog
- OAuth-based authentication
- No data stored locally (except conversation history)

## 🐛 Troubleshooting

### Common Issues

#### Dashboard Not Loading
- Check `DASHBOARD_ID` environment variable
- Verify dashboard permissions
- Check OAuth token validity
- Ensure dashboard embedding is enabled in workspace settings

#### Genie Not Working
- Check `GENIE_SPACE_ID` environment variable
- Verify Genie space permissions
- Ensure Genie space is accessible
- Check Databricks workspace URL

#### Authentication Errors
- Verify OAuth token is valid
- Check Databricks workspace access
- Ensure proper permissions are granted

### Debug Mode
Run the test script to diagnose issues:
```bash
python test_integration.py
```

## 📊 API Endpoints

### Dashboard APIs
- `GET /dashboard` - Dashboard page
- `GET /api/dashboard-config` - Dashboard configuration
- `GET /api/token-status` - OAuth token status

### Genie APIs
- `GET /genie` - Genie interface page
- `POST /api/genie/start-conversation` - Start new conversation
- `POST /api/genie/send-message` - Send message to conversation
- `GET /api/genie/conversation/<id>` - Get conversation details
- `GET /api/genie/conversations` - Get all conversations
- `DELETE /api/genie/clear-conversation/<id>` - Clear conversation
- `DELETE /api/genie/clear-all-conversations` - Clear all conversations
- `GET /api/genie/suggested-queries` - Get suggested queries
- `GET /api/genie/config` - Get Genie configuration

## 🔄 Future Enhancements

### Planned Features
- Real-time dashboard updates
- Advanced query suggestions
- Data export in multiple formats
- Conversation sharing
- Custom dashboard widgets
- Mobile app integration

### Customization Options
- Custom Genie space configurations
- Dashboard theme customization
- Query result visualization options
- Conversation persistence settings

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Run the integration test script
3. Verify environment variables
4. Check Databricks workspace permissions
5. Review application logs

## 📚 References

- [Databricks Apps Cookbook - Dashboard Embedding](https://apps-cookbook.dev/docs/dash/bi/embed_dashboard)
- [Databricks Apps Cookbook - Genie API](https://apps-cookbook.dev/docs/dash/bi/genie_api)
- [Databricks SDK Documentation](https://docs.databricks.com/dev-tools/sdk/python.html)
- [Unity Catalog Documentation](https://docs.databricks.com/data-governance/unity-catalog/index.html)
