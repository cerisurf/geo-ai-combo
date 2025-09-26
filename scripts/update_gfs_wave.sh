#!/bin/bash
"""
GFS Wave Data Update Script for EDR Publisher

Simple wrapper script to update GFS Wave data with common configurations.

Usage:
    ./update_gfs_wave.sh [OPTIONS]

Examples:
    ./update_gfs_wave.sh                    # Download latest global data
    ./update_gfs_wave.sh --region europe   # Download European waters
    ./update_gfs_wave.sh --hours 72        # Download 72 hours of forecast
"""

set -e  # Exit on any error

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_DIR="$SCRIPT_DIR/data_pipeline"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default configuration
CONFIG_FILE="$PIPELINE_DIR/config.json"
PYTHON_CMD="python3"

# Check if we're in a virtual environment or have Python dependencies
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help                Show this help message"
    echo "  --region REGION       Download specific region (global, europe, atlantic, pacific)"
    echo "  --hours HOURS         Number of forecast hours (default: 120)"
    echo "  --date YYYYMMDD       Specific date to download"
    echo "  --run HH              Specific forecast run (00, 06, 12, 18)"
    echo "  --output-name NAME    Output dataset name (default: gfs_wave_data)"
    echo "  --dry-run             Show what would be done without doing it"
    echo "  --download-only       Only download, don't convert"
    echo "  --convert-only FILE   Only convert existing NetCDF file"
    echo ""
    echo "Examples:"
    echo "  $0                              # Download latest global data"
    echo "  $0 --region europe --hours 72  # European waters, 72 hours"
    echo "  $0 --date 20250926 --run 12    # Specific date and run"
    echo "  $0 --dry-run                    # Preview what would be downloaded"
}

# Function to get region bounds from config
get_region_bounds() {
    local region="$1"
    case "$region" in
        "global"|"")
            echo ""
            ;;
        "europe"|"european_waters")
            echo "40,70,-15,40"
            ;;
        "atlantic"|"north_atlantic")
            echo "35,75,-80,10"
            ;;
        "pacific"|"north_pacific")
            echo "20,70,140,240"
            ;;
        "mediterranean")
            echo "30,47,-6,37"
            ;;
        "gulf_mexico"|"gulf_of_mexico")
            echo "18,31,-98,-80"
            ;;
        *)
            echo "Unknown region: $region" >&2
            echo "Available regions: global, europe, atlantic, pacific, mediterranean, gulf_mexico" >&2
            exit 1
            ;;
    esac
}

# Parse command line arguments
REGION=""
HOURS=""
DATE=""
RUN=""
OUTPUT_NAME=""
DRY_RUN=""
DOWNLOAD_ONLY=""
CONVERT_ONLY=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_usage
            exit 0
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --hours)
            HOURS="$2"
            shift 2
            ;;
        --date)
            DATE="$2"
            shift 2
            ;;
        --run)
            RUN="$2"
            shift 2
            ;;
        --output-name)
            OUTPUT_NAME="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --download-only)
            DOWNLOAD_ONLY="true"
            shift
            ;;
        --convert-only)
            CONVERT_ONLY="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            show_usage
            exit 1
            ;;
    esac
done

# Check dependencies
echo "Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Please install Python 3." >&2
    exit 1
fi

# Check Python packages
python3 -c "import xarray, requests, numpy" 2>/dev/null || {
    echo "Error: Required Python packages not found." >&2
    echo "Please install: pip install xarray requests numpy netcdf4 zarr" >&2
    exit 1
}

echo "Dependencies OK ✓"

# Handle convert-only mode
if [ -n "$CONVERT_ONLY" ]; then
    echo "Converting existing NetCDF file: $CONVERT_ONLY"
    
    if [ ! -f "$CONVERT_ONLY" ]; then
        echo "Error: File not found: $CONVERT_ONLY" >&2
        exit 1
    fi
    
    OUTPUT_PATH="${OUTPUT_NAME:-gfs_wave_data}.zarr"
    
    python3 "$PIPELINE_DIR/convert_to_zarr.py" \
        "$CONVERT_ONLY" \
        "./data/$OUTPUT_PATH" \
        $DRY_RUN
    
    echo "Conversion completed!"
    exit 0
fi

# Prepare arguments for the update script
UPDATE_ARGS=()

if [ -n "$CONFIG_FILE" ]; then
    UPDATE_ARGS+=(--config "$CONFIG_FILE")
fi

if [ -n "$DATE" ]; then
    UPDATE_ARGS+=(--date "$DATE")
fi

if [ -n "$RUN" ]; then
    UPDATE_ARGS+=(--run "$RUN")
fi

if [ -n "$HOURS" ]; then
    UPDATE_ARGS+=(--hours "$HOURS")
fi

if [ -n "$OUTPUT_NAME" ]; then
    UPDATE_ARGS+=(--output-name "$OUTPUT_NAME")
fi

if [ -n "$DRY_RUN" ]; then
    UPDATE_ARGS+=($DRY_RUN)
fi

# Handle region
if [ -n "$REGION" ]; then
    REGION_BOUNDS=$(get_region_bounds "$REGION")
    if [ -n "$REGION_BOUNDS" ]; then
        UPDATE_ARGS+=(--region "$REGION_BOUNDS")
    fi
fi

# Show configuration
echo "GFS Wave Data Update"
echo "===================="
echo "Region: ${REGION:-global}"
echo "Hours: ${HOURS:-120}"
echo "Date: ${DATE:-latest}"
echo "Run: ${RUN:-latest}"
echo "Output: ${OUTPUT_NAME:-gfs_wave_data}"
echo ""

# Handle download-only mode
if [ -n "$DOWNLOAD_ONLY" ]; then
    echo "Download only mode - running download script..."
    
    DOWNLOAD_ARGS=()
    DOWNLOAD_ARGS+=(--output-dir "./data/raw")
    DOWNLOAD_ARGS+=(--method "dods")
    
    if [ -n "$DATE" ]; then
        DOWNLOAD_ARGS+=(--date "$DATE")
    fi
    
    if [ -n "$RUN" ]; then
        DOWNLOAD_ARGS+=(--run "$RUN")
    fi
    
    if [ -n "$HOURS" ]; then
        DOWNLOAD_ARGS+=(--hours "$HOURS")
    fi
    
    if [ -n "$REGION_BOUNDS" ]; then
        DOWNLOAD_ARGS+=(--region "$REGION_BOUNDS")
    fi
    
    if [ -n "$DRY_RUN" ]; then
        DOWNLOAD_ARGS+=($DRY_RUN)
    fi
    
    python3 "$PIPELINE_DIR/download_gfs_wave.py" "${DOWNLOAD_ARGS[@]}"
    echo "Download completed!"
    exit 0
fi

# Run the complete update workflow
echo "Starting complete update workflow..."
python3 "$PIPELINE_DIR/update_wave_data.py" "${UPDATE_ARGS[@]}"

# Check result
if [ $? -eq 0 ]; then
    echo ""
    echo "✓ GFS Wave data update completed successfully!"
    echo ""
    echo "The new data is now available in your EDR API at:"
    echo "  http://localhost:8080/collections"
    echo ""
    echo "You can view it in the frontend at:"
    echo "  http://localhost:3000"
else
    echo ""
    echo "✗ Update failed. Check the logs for details."
    exit 1
fi
