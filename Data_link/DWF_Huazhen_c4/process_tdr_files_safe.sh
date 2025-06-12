#!/bin/bash

# Script to safely process all .tdr files with tdx -dd command
# Usage: ./process_tdr_files_safe.sh

echo "Starting to process .tdr files safely..."

# Check if there are any .tdr files in the current directory
if ! ls *.tdr 1> /dev/null 2>&1; then
    echo "No .tdr files found in the current directory."
    exit 1
fi

# Count total number of .tdr files
total_files=$(ls *.tdr | wc -l)
echo "Found $total_files .tdr file(s) to process."

# Function to wait for all tdx processes to complete
wait_for_tdx_completion() {
    echo "Waiting for all tdx processes to complete..."
    while pgrep -x "tdx" > /dev/null; do
        echo "  tdx process still running, waiting..."
        sleep 5
    done
    echo "All tdx processes completed."
}

# Process each .tdr file
count=0
for tdr_file in *.tdr; do
    count=$((count + 1))
    echo ""
    echo "========================================"
    echo "[$count/$total_files] Processing: $tdr_file"
    echo "Started at: $(date)"
    
    # Make sure no other tdx processes are running before starting
    wait_for_tdx_completion
    
    # Execute tdx -dd command on the file
    echo "Executing: tdx -dd $tdr_file"
    tdx -dd "$tdr_file" &
    tdx_pid=$!
    
    # Wait for this specific process to complete
    echo "Waiting for process $tdx_pid to complete..."
    wait $tdx_pid
    exit_code=$?
    
    # Double check that the process is really done
    sleep 2
    wait_for_tdx_completion
    
    if [ $exit_code -eq 0 ]; then
        echo "✓ Successfully processed: $tdr_file"
    else
        echo "✗ Failed to process: $tdr_file (exit code: $exit_code)"
    fi
    
    echo "Completed at: $(date)"
    
    # Brief pause before next file
    if [ $count -lt $total_files ]; then
        echo "Pausing before next file..."
        sleep 5
    fi
done

echo ""
echo "========================================"
echo "All .tdr files have been processed."
echo "Final completion time: $(date)" 