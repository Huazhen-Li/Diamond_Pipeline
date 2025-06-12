#!/bin/bash

# Script to organize files by their numeric prefix into folders
# Files with pattern n*_ will be organized based on the number:
# 1358 -> 1e-3, 1359 -> 5e-3, 1360 -> 1e-2, 1361 -> 5e-2, 1362 -> 1e-1, 1363 -> 1

echo "Starting to organize files by numeric prefix..."

# Define the mapping from numbers to folder names
declare -A folder_mapping
folder_mapping[1358]="1e-3"
folder_mapping[1359]="5e-3"
folder_mapping[1360]="1e-2"
folder_mapping[1361]="5e-2"
folder_mapping[1362]="1e-1"
folder_mapping[1363]="1"

# Find all files that match the pattern n*_
files_found=0
for file in n*_*; do
    # Check if the file actually exists (in case no matches)
    if [ ! -e "$file" ]; then
        continue
    fi
    
    files_found=$((files_found + 1))
    
    # Extract the number from the filename (between 'n' and '_')
    if [[ $file =~ ^n([0-9]+)_ ]]; then
        number="${BASH_REMATCH[1]}"
        echo "Processing file: $file (number: $number)"
        
        # Check if we have a mapping for this number
        if [[ -n "${folder_mapping[$number]}" ]]; then
            folder_name="${folder_mapping[$number]}"
            
            # Create the folder if it doesn't exist
            if [ ! -d "$folder_name" ]; then
                mkdir -p "$folder_name"
                echo "  Created folder: $folder_name"
            fi
            
            # Move the file to the appropriate folder
            if mv "$file" "$folder_name/"; then
                echo "  ✓ Moved $file to $folder_name/"
            else
                echo "  ✗ Failed to move $file to $folder_name/"
            fi
        else
            echo "  ! No mapping found for number $number, skipping file $file"
        fi
    else
        echo "  ! Could not extract number from filename: $file"
    fi
    
    echo "  ----------------------------------------"
done

if [ $files_found -eq 0 ]; then
    echo "No files found matching pattern n*_*"
else
    echo ""
    echo "File organization completed!"
    echo "Total files processed: $files_found"
    
    # Show the final directory structure
    echo ""
    echo "Current directory structure:"
    for folder in "${folder_mapping[@]}"; do
        if [ -d "$folder" ]; then
            file_count=$(ls -1 "$folder" | wc -l)
            echo "  $folder/: $file_count file(s)"
        fi
    done
fi 