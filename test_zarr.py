#!/usr/bin/env python3
"""
Test script to verify Zarr data access.
"""

import sys
sys.path.append('.')

from edr_publisher.data.zarr_accessor import ZarrDataAccessor

def test_zarr_access():
    """Test basic Zarr data access."""
    try:
        accessor = ZarrDataAccessor("data/wave_data.zarr")
        
        print("Testing collection metadata...")
        metadata = accessor.get_collection_metadata()
        print(f"Collection ID: {metadata['id']}")
        print(f"Title: {metadata['title']}")
        print(f"Parameters: {list(metadata['parameter_names'].keys())}")
        print(f"Temporal extent: {metadata['extent']['temporal']}")
        print(f"Spatial extent: {metadata['extent']['spatial']}")
        
        print("\nTesting position query...")
        result = accessor.query_position(lon=-60.0, lat=45.0)
        print(f"Position query result type: {result['type']}")
        print(f"Number of features: {len(result['features'])}")
        if result['features']:
            print(f"First feature: {result['features'][0]}")
        
        print("\n✅ Zarr access test passed!")
        
    except Exception as e:
        print(f"❌ Zarr access test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_zarr_access()

