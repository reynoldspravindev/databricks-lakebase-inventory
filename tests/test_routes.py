#!/usr/bin/env python3
"""
Test script to verify Flask routes are working correctly.
"""

import requests
import sys
import time

def test_route(base_url, route, expected_status=200):
    """Test a specific route."""
    try:
        url = f"{base_url}{route}"
        response = requests.get(url, timeout=10)
        print(f"✅ {route}: {response.status_code}")
        return response.status_code == expected_status
    except requests.exceptions.RequestException as e:
        print(f"❌ {route}: {e}")
        return False

def main():
    """Test all routes."""
    base_url = "http://localhost:8080"
    
    print("🧪 Testing Flask Routes")
    print("=" * 40)
    
    # Wait a moment for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(2)
    
    routes_to_test = [
        ("/", "Home page"),
        ("/dashboard", "Dashboard page"),
        ("/genie", "Genie page"),
        ("/add", "Add item page"),
        ("/low-stock", "Low stock page"),
        ("/api/dashboard-config", "Dashboard config API"),
        ("/api/genie/config", "Genie config API"),
    ]
    
    results = []
    for route, description in routes_to_test:
        print(f"\n🔍 Testing {description}...")
        success = test_route(base_url, route)
        results.append((route, success))
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    
    all_passed = True
    for route, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {route}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All routes are working!")
    else:
        print("\n⚠️  Some routes failed. Check the server logs.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
