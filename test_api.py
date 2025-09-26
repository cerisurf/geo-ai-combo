#!/usr/bin/env python3
"""
Test script for the EDR API endpoints.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8002"

def test_endpoint(url, description):
    """Test an API endpoint."""
    print(f"\n🧪 Testing: {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            
            # Show some key information based on endpoint
            if "/collections" in url and "collections" in data:
                print(f"Collections found: {len(data['collections'])}")
                if data['collections']:
                    print(f"First collection: {data['collections'][0]['id']}")
            elif "/position" in url and "features" in data:
                print(f"Features returned: {len(data['features'])}")
                if data['features']:
                    props = data['features'][0]['properties']
                    print(f"Sample properties: {list(props.keys())}")
            elif "/area" in url and "features" in data:
                print(f"Features returned: {len(data['features'])}")
            
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Run API tests."""
    print("🚀 Testing EDR API Endpoints")
    print("=" * 50)
    
    tests = [
        (f"{BASE_URL}/", "Landing Page"),
        (f"{BASE_URL}/conformance", "Conformance Classes"),
        (f"{BASE_URL}/collections", "Collections List"),
        (f"{BASE_URL}/collections/wave_data", "Collection Metadata"),
        (f"{BASE_URL}/collections/wave_data/position?coords=POINT(-60.0 45.0)", "Position Query (no time)"),
        (f"{BASE_URL}/collections/wave_data/position?coords=-60.0,45.0", "Position Query (lon,lat format)"),
        (f"{BASE_URL}/collections/wave_data/area?coords=-65,40,-55,50", "Area Query (bbox format)"),
    ]
    
    passed = 0
    total = len(tests)
    
    for url, description in tests:
        if test_endpoint(url, description):
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

