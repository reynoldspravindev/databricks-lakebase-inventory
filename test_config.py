#!/usr/bin/env python3
"""
Test script to verify configuration loading and iframe URL generation.
"""

import sys
import os

def test_config_loading():
    """Test configuration loading from YAML and environment variables."""
    print("🧪 Testing Configuration Loading")
    print("=" * 50)
    
    try:
        from config import config
        
        print("✅ Configuration module loaded successfully")
        
        # Test configuration summary
        config.print_config_summary()
        
        # Test specific URL generation
        print("\n🔗 URL Generation Tests:")
        
        embed_url = config.get_dashboard_embed_url()
        if embed_url:
            print(f"✅ Dashboard Embed URL: {embed_url}")
        else:
            print("❌ Dashboard Embed URL: Not configured")
        
        public_url = config.get_dashboard_public_url()
        if public_url:
            print(f"✅ Dashboard Public URL: {public_url}")
        else:
            print("❌ Dashboard Public URL: Not configured")
        
        genie_space_id = config.get_genie_space_id()
        if genie_space_id:
            print(f"✅ Genie Space ID: {genie_space_id}")
        else:
            print("❌ Genie Space ID: Not configured")
        
        # Test database config
        db_config = config.get_database_config()
        print(f"\n🗄️  Database Config: {db_config}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import config module: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_iframe_url_format():
    """Test iframe URL format matches Databricks documentation."""
    print("\n🔗 Testing Iframe URL Format")
    print("=" * 50)
    
    # Test URL format based on Databricks Apps Cookbook
    test_cases = [
        {
            "host": "https://workspace.azuredatabricks.net",
            "dashboard_id": "test-dashboard-123",
            "expected_embed": "https://workspace.azuredatabricks.net/embed/dashboardsv3/test-dashboard-123",
            "expected_public": "https://workspace.azuredatabricks.net/dashboardsv3/test-dashboard-123"
        },
        {
            "host": "https://e2-demo-field-eng.cloud.databricks.com",
            "dashboard_id": "abc123def456",
            "expected_embed": "https://e2-demo-field-eng.cloud.databricks.com/embed/dashboardsv3/abc123def456",
            "expected_public": "https://e2-demo-field-eng.cloud.databricks.com/dashboardsv3/abc123def456"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Host: {test_case['host']}")
        print(f"  Dashboard ID: {test_case['dashboard_id']}")
        
        # Simulate URL generation
        base_url = test_case['host'].rstrip('/')
        embed_url = f"{base_url}/embed/dashboardsv3/{test_case['dashboard_id']}"
        public_url = f"{base_url}/dashboardsv3/{test_case['dashboard_id']}"
        
        embed_match = embed_url == test_case['expected_embed']
        public_match = public_url == test_case['expected_public']
        
        print(f"  Embed URL: {embed_url}")
        print(f"  Expected:  {test_case['expected_embed']}")
        print(f"  ✅ Match" if embed_match else f"  ❌ Mismatch")
        
        print(f"  Public URL: {public_url}")
        print(f"  Expected:   {test_case['expected_public']}")
        print(f"  ✅ Match" if public_match else f"  ❌ Mismatch")
    
    return True

def main():
    """Run all configuration tests."""
    print("🧪 Configuration and Iframe URL Testing")
    print("=" * 60)
    
    tests = [
        ("Configuration Loading", test_config_loading),
        ("Iframe URL Format", test_iframe_url_format)
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
        print("🎉 All configuration tests passed!")
        print("\n📝 Next steps:")
        print("   1. Update app.yaml with your actual Databricks configuration")
        print("   2. Or set environment variables:")
        print("      export DASHBOARD_ID='your_dashboard_id'")
        print("      export DATABRICKS_HOST='https://your-workspace.cloud.databricks.com'")
        print("      export GENIE_SPACE_ID='your_genie_space_id'")
        print("   3. Run: python app.py")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
