#!/bin/bash

# TPA Simulation Runner Script
# Compiles Diamond_4p and runs simulations for different x,y positions

set -e  # Exit on any error

echo "=== TPA Simulation Runner ==="
echo "Compilation and batch job submission script"
echo

# Step 1: Compilation
echo "Step 1: Compiling Diamond_4p..."

# Create build directory if it doesn't exist
if [ ! -d "build" ]; then
    mkdir build
fi

cd build
echo "Running cmake and make..."
cmake .. && make -j 48

if [ $? -eq 0 ]; then
    echo "✓ Compilation successful!"
else
    echo "✗ Compilation failed!"
    exit 1
fi

cd ..

# Step 2: Setup simulation parameters
echo
echo "Step 2: Setting up simulation grid..."

# Position range: (2.5, 2.5) to (32.5, 32.5) μm
X_MIN=2.5
X_MAX=32.5
Y_MIN=2.5
Y_MAX=32.5

# Grid size: 7x7 = 49 points (under 60 limit)
N_X=7
N_Y=7

# Time step parameter for weighting field intervals (can be modified as needed)
# Examples: 1.0 (0-20ns), 0.5 (0-10ns), 2.0 (0-40ns)
TIME_STEP=1.0  # nanoseconds

# Calculate step sizes
X_STEP=$(echo "scale=6; ($X_MAX - $X_MIN) / ($N_X - 1)" | bc)
Y_STEP=$(echo "scale=6; ($Y_MAX - $Y_MIN) / ($N_Y - 1)" | bc)

echo "Grid configuration:"
echo "  X range: $X_MIN to $X_MAX μm ($N_X points, step: $X_STEP μm)"
echo "  Y range: $Y_MIN to $Y_MAX μm ($N_Y points, step: $Y_STEP μm)"
echo "  Time step: $TIME_STEP ns (21 points: 0 to $((20 * TIME_STEP)) ns)"
echo "  Total jobs: $((N_X * N_Y))"
echo

# Step 3: Create output directory
OUTPUT_DIR="TPA_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p $OUTPUT_DIR
echo "Results will be saved to: $OUTPUT_DIR"
echo

# Step 4: Submit jobs
echo "Step 3: Submitting simulation jobs to background..."
echo

job_count=0
job_pids=()

for i in $(seq 0 $((N_X-1))); do
    for j in $(seq 0 $((N_Y-1))); do
        # Calculate x, y positions
        x_pos=$(echo "scale=3; $X_MIN + $i * $X_STEP" | bc)
        y_pos=$(echo "scale=3; $Y_MIN + $j * $Y_STEP" | bc)
        
        job_count=$((job_count + 1))
        
        echo "Submitting Job $job_count/$((N_X * N_Y)): x=$x_pos μm, y=$y_pos μm"
        
        # Run simulation in background with nohup
        if [ -f "build/Diamond_4p" ]; then
            # Create unique log file for each job
            log_file="$OUTPUT_DIR/job_x${x_pos}_y${y_pos}.log"
            
            # Submit job to background
            nohup ./build/Diamond_4p $x_pos $y_pos $TIME_STEP > "$log_file" 2>&1 &
            job_pid=$!
            job_pids+=($job_pid)
            
            echo "  → Job PID: $job_pid, Log: $log_file"
        else
            echo "  ✗ Error: Diamond_4p executable not found"
            exit 1
        fi
    done
done

echo
echo "All $job_count jobs submitted to background!"
echo "Job PIDs: ${job_pids[@]}"
echo

# Step 5: Wait for all jobs to complete
echo "Step 4: Waiting for all jobs to complete..."
echo "You can monitor progress with: tail -f $OUTPUT_DIR/*.log"
echo

completed_jobs=0
successful_jobs=0
failed_jobs=0

# Create arrays to track job status
declare -A job_status  # "running", "success", "failed"
declare -A job_positions

# Initialize job tracking
job_index=0
for i in $(seq 0 $((N_X-1))); do
    for j in $(seq 0 $((N_Y-1))); do
        x_pos=$(echo "scale=3; $X_MIN + $i * $X_STEP" | bc)
        y_pos=$(echo "scale=3; $Y_MIN + $j * $Y_STEP" | bc)
        pid=${job_pids[$job_index]}
        job_status[$pid]="running"
        job_positions[$pid]="x${x_pos}_y${y_pos}"
        job_index=$((job_index + 1))
    done
done

while [ $completed_jobs -lt $job_count ]; do
    sleep 10  # Check every 10 seconds
    
    running_jobs=0
    
    for pid in "${job_pids[@]}"; do
        if [ "${job_status[$pid]}" = "running" ]; then
            position=${job_positions[$pid]}
            expected_file="TPA_simulation_$position.txt"
            log_file="$OUTPUT_DIR/job_$position.log"
            
            # Check if output file exists and contains "DONE!" 
            if [ -f "$expected_file" ] && grep -q "DONE !" "$log_file" 2>/dev/null; then
                # Task completed successfully - kill hanging process if needed
                if kill -0 $pid 2>/dev/null; then
                    echo "  🔄 Job $position completed but process hanging, terminating..."
                    kill $pid 2>/dev/null
                    sleep 2
                    kill -9 $pid 2>/dev/null  # Force kill if needed
                fi
                job_status[$pid]="success"
                successful_jobs=$((successful_jobs + 1))
                echo "  ✓ Job $position completed successfully"
                
            elif kill -0 $pid 2>/dev/null; then
                # Process still running, check for timeout (optional)
                running_jobs=$((running_jobs + 1))
                
            else
                # Process finished but no output file or "DONE!" found
                wait $pid 2>/dev/null
                exit_code=$?
                
                if [ -f "$expected_file" ]; then
                    # File exists but no "DONE!" - might be incomplete
                    job_status[$pid]="success"
                    successful_jobs=$((successful_jobs + 1))
                    echo "  ⚠️  Job $position completed (no DONE marker, but file exists)"
                else
                    job_status[$pid]="failed"
                    failed_jobs=$((failed_jobs + 1))
                    echo "  ✗ Job $position failed: exit code $exit_code, no output file"
                fi
            fi
        fi
    done
    
    completed_jobs=$((successful_jobs + failed_jobs))
    echo "Progress: $completed_jobs/$job_count jobs finished ($successful_jobs successful, $failed_jobs failed, $running_jobs still running)..."
done

echo
echo "=== All simulations finished! ==="
echo "Final results: $successful_jobs successful, $failed_jobs failed"
if [ $failed_jobs -gt 0 ]; then
    echo "⚠️  Some jobs failed. Check log files for details."
fi

# Step 6: Organize output files
echo "Step 5: Organizing output files..."
echo

# Move TPA simulation result files to output directory
for file in TPA_simulation_*.txt; do
    if [ -f "$file" ]; then
        mv "$file" "$OUTPUT_DIR/"
        echo "  Moved: $file"
    fi
done

echo
echo "Results organization completed!"
echo "Results saved in: $OUTPUT_DIR"
echo "Total jobs processed: $job_count"

# Step 7: Generate summary
echo
echo "Step 6: Generating summary..."
tpa_files=$(ls -1 $OUTPUT_DIR/TPA_simulation_*.txt 2>/dev/null | wc -l)
log_files=$(ls -1 $OUTPUT_DIR/job_*.log 2>/dev/null | wc -l)
echo "  TPA result files: $tpa_files"
echo "  Log files: $log_files"
echo "  Total directory size: $(du -sh $OUTPUT_DIR | cut -f1)"

echo
echo "=== Script completed successfully! ==="
echo
echo "To monitor individual jobs, check log files:"
echo "  tail -f $OUTPUT_DIR/job_*.log"
echo
echo "Result files are in: $OUTPUT_DIR/TPA_simulation_*.txt" 