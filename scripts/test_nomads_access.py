#!/usr/bin/env python3
"""
Test script to verify NOAA NOMADS GFS Wave data access

This script tests the correct URL format for accessing GFS Wave data
from the NOAA NOMADS server.
"""

import requests
import sys
from datetime import datetime, timedelta

def test_nomads_urls():
    """Test various URL formats to find the correct one."""
    
    base_url = "http://nomads.ncep.noaa.gov/dods/wave/gfswave"
    
    # Test with recent dates
    test_dates = []
    today = datetime.now()
    for i in range(3):
        date = today - timedelta(days=i)
        test_dates.append(date.strftime("%Y%m%d"))
    
    # Test different URL formats
    url_formats = [
        "{base}/{date}/gfswave.global.0p25_00z",  # Your suggested format
        "{base}/{date}/gfswave.global.0p25_00z.dds",  # With DDS extension
        "{base}/{date}/gfswave.t00z.global.0p25",  # Original format I used
        "{base}/{date}/gfswave_00z_global_0p25",  # Alternative format
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'EDR-Publisher-Test/1.0'
    })
    
    print("Testing NOAA NOMADS GFS Wave URL formats...")
    print("=" * 50)
    
    for date in test_dates:
        print(f"\nTesting date: {date}")
        
        for i, url_format in enumerate(url_formats, 1):
            url = url_format.format(base=base_url, date=date)
            
            try:
                print(f"  {i}. Testing: {url}")
                response = session.head(url, timeout=10)
                
                if response.status_code == 200:
                    print(f"     ✓ SUCCESS (HTTP {response.status_code})")
                    
                    # Try to get some metadata
                    das_url = url + ".das"
                    das_response = session.get(das_url, timeout=10)
                    if das_response.status_code == 200:
                        print(f"     ✓ DAS metadata available")
                        # Print first few lines of metadata
                        lines = das_response.text.split('\n')[:10]
                        for line in lines:
                            if line.strip():
                                print(f"       {line}")
                    
                    return url  # Return first working URL
                    
                elif response.status_code == 404:
                    print(f"     ✗ Not found (HTTP {response.status_code})")
                else:
                    print(f"     ? HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"     ✗ Error: {e}")
    
    print("\nNo working URL format found!")
    return None

def test_opendap_access(url):
    """Test actual data access via OPeNDAP."""
    
    print(f"\nTesting OPeNDAP data access...")
    print(f"URL: {url}")
    
    try:
        import xarray as xr
        
        # Try to open the dataset
        print("Opening dataset with xarray...")
        ds = xr.open_dataset(url, engine='netcdf4')
        
        print("✓ Successfully opened dataset!")
        print(f"Variables: {list(ds.variables.keys())}")
        print(f"Dimensions: {dict(ds.dims)}")
        
        # Test data access
        if 'htsgwsfc' in ds.variables:
            print("Testing variable access...")
            var = ds['htsgwsfc']
            print(f"✓ htsgwsfc shape: {var.shape}")
            print(f"✓ htsgwsfc attributes: {list(var.attrs.keys())}")
        
        ds.close()
        return True
        
    except ImportError:
        print("xarray not available, skipping data access test")
        return False
    except Exception as e:
        print(f"✗ Data access failed: {e}")
        return False

if __name__ == "__main__":
    working_url = test_nomads_urls()
    
    if working_url:
        print(f"\n🎉 Found working URL: {working_url}")
        test_opendap_access(working_url)
    else:
        print("\n❌ No working URL found. Check NOMADS server status or URL format.")
        sys.exit(1)
