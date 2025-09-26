#!/usr/bin/env python3
"""
Single URL verification for NOAA NOMADS GFS Wave data

Makes ONE careful request to verify the URL format works.
"""

import requests
import sys
from datetime import datetime, timedelta

def verify_single_url():
    """Make one careful test of the URL format."""
    
    # Use yesterday's date (more likely to be available)
    yesterday = datetime.now() - timedelta(days=1)
    date = yesterday.strftime("%Y%m%d")
    
    # Test the URL format you suggested
    base_url = "http://nomads.ncep.noaa.gov/dods/wave/gfswave"
    test_url = f"{base_url}/{date}/gfswave.global.0p25_00z"
    
    print(f"Testing single URL: {test_url}")
    print("Making one careful request...")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'EDR-Publisher-Verification/1.0'
    })
    
    try:
        # Test with DAS (Dataset Attribute Structure) which is lightweight
        das_url = test_url + ".das"
        print(f"Checking: {das_url}")
        
        response = session.get(das_url, timeout=15, allow_redirects=True)
        
        print(f"HTTP Status: {response.status_code}")
        print(f"Final URL: {response.url}")
        
        if response.status_code == 200:
            print("✓ SUCCESS! URL format is correct.")
            print("First few lines of DAS response:")
            lines = response.text.split('\n')[:5]
            for line in lines:
                if line.strip():
                    print(f"  {line}")
            return True
        else:
            print(f"✗ Failed with HTTP {response.status_code}")
            if response.text:
                print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = verify_single_url()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
