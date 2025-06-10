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

# Grid size: 8x7 = 56 points (under 60 limit)
N_X=8
N_Y=7

# Calculate step sizes
X_STEP=$(echo "scale=6; ($X_MAX - $X_MIN) / ($N_X - 1)" | bc)
Y_STEP=$(echo "scale=6; ($Y_MAX - $Y_MIN) / ($N_Y - 1)" | bc)

echo "Grid configuration:"
echo "  X range: $X_MIN to $X_MAX μm ($N_X points, step: $X_STEP μm)"
echo "  Y range: $Y_MIN to $Y_MAX μm ($N_Y points, step: $Y_STEP μm)"
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
            nohup ./build/Diamond_4p $x_pos $y_pos > "$log_file" 2>&1 &
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
while [ $completed_jobs -lt $job_count ]; do
    sleep 10  # Check every 10 seconds
    
    running_jobs=0
    for pid in "${job_pids[@]}"; do
        if kill -0 $pid 2>/dev/null; then
            running_jobs=$((running_jobs + 1))
        fi
    done
    
    completed_jobs=$((job_count - running_jobs))
    echo "Progress: $completed_jobs/$job_count jobs completed ($running_jobs still running)..."
done

echo
echo "=== All simulations completed! ==="

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