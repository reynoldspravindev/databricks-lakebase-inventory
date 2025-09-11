#!/usr/bin/env python3
"""
Test script to verify Databricks Dashboard and Genie integration.
Run this script to test the integration before starting the Flask app.
"""

import os
import sys
from databricks import sdk

def test_databricks_connection():
    """Test Databricks SDK connection."""
    try:
        workspace_client = sdk.WorkspaceClient()
        print("✅ Databricks SDK connection successful")
        print(f"   Workspace URL: {workspace_client.config.host}")
        return True
    except Exception as e:
        print(f"❌ Databricks SDK connection failed: {e}")
        return False

def test_environment_variables():
    """Test required environment variables."""
    required_vars = {
        'PGDATABASE': 'PostgreSQL database name',
        'PGUSER': 'PostgreSQL username', 
        'PGHOST': 'PostgreSQL host',
        'PGPORT': 'PostgreSQL port',
        'PGSSLMODE': 'PostgreSQL SSL mode'
    }
    
    optional_vars = {
        'DASHBOARD_ID': 'Databricks Dashboard ID (for dashboard embedding)',
        'GENIE_SPACE_ID': 'Databricks Genie Space ID (for AI assistant)',
        'DATABRICKS_HOST': 'Databricks workspace URL'
    }
    
    print("\n📋 Environment Variables Check:")
    
    all_good = True
    for var, description in required_vars.items():
        if os.getenv(var):
            print(f"✅ {var}: {os.getenv(var)}")
        else:
            print(f"❌ {var}: Not set ({description})")
            all_good = False
    
    print("\n📋 Optional Environment Variables:")
    for var, description in optional_vars.items():
        if os.getenv(var):
            print(f"✅ {var}: {os.getenv(var)}")
        else:
            print(f"⚠️  {var}: Not set ({description})")
    
    return all_good

def test_genie_service():
    """Test Genie service initialization."""
    try:
        from genie_service import GenieService
        from databricks import sdk
        
        workspace_client = sdk.WorkspaceClient()
        genie_service = GenieService(workspace_client)
        
        print(f"✅ Genie service initialized successfully")
        print(f"   Configured: {genie_service.is_configured()}")
        
        if genie_service.is_configured():
            print(f"   Genie Space ID: {genie_service.genie_space_id}")
        else:
            print("   ⚠️  Genie not configured (set GENIE_SPACE_ID)")
        
        return True
    except Exception as e:
        print(f"❌ Genie service initialization failed: {e}")
        return False

def test_flask_imports():
    """Test Flask app imports."""
    try:
        # Test importing the main app
        sys.path.append('.')
        from app import app, genie_service
        
        print("✅ Flask app imports successful")
        print(f"   Genie service available: {genie_service is not None}")
        
        # Test route registration
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        genie_routes = [route for route in routes if 'genie' in route]
        dashboard_routes = [route for route in routes if 'dashboard' in route]
        
        print(f"   Total routes: {len(routes)}")
        print(f"   Genie routes: {len(genie_routes)}")
        print(f"   Dashboard routes: {len(dashboard_routes)}")
        
        return True
    except Exception as e:
        print(f"❌ Flask app import failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("🧪 Testing Databricks Dashboard and Genie Integration")
    print("=" * 60)
    
    tests = [
        ("Databricks Connection", test_databricks_connection),
        ("Environment Variables", test_environment_variables),
        ("Genie Service", test_genie_service),
        ("Flask App", test_flask_imports)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! Your integration is ready to use.")
        print("\n📝 Next steps:")
        print("   1. Set GENIE_SPACE_ID environment variable for AI assistant")
        print("   2. Set DASHBOARD_ID environment variable for dashboard embedding")
        print("   3. Run: python app.py")
        print("   4. Visit: http://localhost:8080")
    else:
        print("⚠️  Some tests failed. Please fix the issues before running the app.")
        print("\n🔧 Common fixes:")
        print("   - Set required environment variables")
        print("   - Install dependencies: pip install -r requirements.txt")
        print("   - Check Databricks authentication")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
