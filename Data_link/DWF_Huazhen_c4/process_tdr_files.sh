#!/bin/bash

# Script to process all .tdr files with tdx -dd command
# Usage: ./process_tdr_files.sh

echo "Starting to process .tdr files..."

# Check if there are any .tdr files in the current directory
if ! ls *.tdr 1> /dev/null 2>&1; then
    echo "No .tdr files found in the current directory."
    exit 1
fi

# Count total number of .tdr files
total_files=$(ls *.tdr | wc -l)
echo "Found $total_files .tdr file(s) to process."

# Process each .tdr file
count=0
for tdr_file in *.tdr; do
    count=$((count + 1))
    echo "[$count/$total_files] Processing: $tdr_file"
    echo "Starting tdx -dd command at $(date)"
    
    # Execute tdx -dd command on the file and wait for completion
    tdx -dd "$tdr_file"
    exit_code=$?
    
    # Wait a moment to ensure all file operations are complete
    sleep 2
    
    if [ $exit_code -eq 0 ]; then
        echo "✓ Successfully processed: $tdr_file at $(date)"
    else
        echo "✗ Failed to process: $tdr_file (exit code: $exit_code) at $(date)"
    fi
    
    echo "----------------------------------------"
    
    # Optional: Add a longer pause between files if needed
    if [ $count -lt $total_files ]; then
        echo "Waiting before processing next file..."
        sleep 3
    fi
done

echo "All .tdr files have been processed at $(date)." 