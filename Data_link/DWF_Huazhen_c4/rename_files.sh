#!/bin/bash

# Script to rename files in organized folders
# Changes n*_XXX.dat to foldername_XXX.dat
# Works on folders: 1e-3, 5e-3, 1e-2, 5e-2, 1e-1, 1

echo "Starting to rename files in organized folders..."

# Define the folders to process
folders=("1e-3" "5e-3" "1e-2" "5e-2" "1e-1" "1")

total_renamed=0

for folder in "${folders[@]}"; do
    echo ""
    echo "========================================"
    echo "Processing folder: $folder"
    
    # Check if folder exists
    if [ ! -d "$folder" ]; then
        echo "  Folder $folder does not exist, skipping..."
        continue
    fi
    
    # Count files in this folder
    file_count=0
    renamed_count=0
    
    # Process all .dat files that match n*_ pattern in this folder
    for file in "$folder"/n*_*.dat; do
        # Check if the file actually exists (in case no matches)
        if [ ! -e "$file" ]; then
            continue
        fi
        
        file_count=$((file_count + 1))
        
        # Extract just the filename without path
        filename=$(basename "$file")
        
        echo "  Found file: $filename"
        
        # Extract the part after n*_ using regex
        if [[ $filename =~ ^n[0-9]+_(.+)$ ]]; then
            suffix="${BASH_REMATCH[1]}"
            new_filename="${folder}_${suffix}"
            new_filepath="$folder/$new_filename"
            
            echo "    Renaming: $filename -> $new_filename"
            
            # Check if target file already exists
            if [ -e "$new_filepath" ]; then
                echo "    ✗ Target file $new_filename already exists, skipping..."
            else
                # Perform the rename
                if mv "$file" "$new_filepath"; then
                    echo "    ✓ Successfully renamed to $new_filename"
                    renamed_count=$((renamed_count + 1))
                    total_renamed=$((total_renamed + 1))
                else
                    echo "    ✗ Failed to rename $filename"
                fi
            fi
        else
            echo "    ! Filename $filename doesn't match expected pattern n*_*.dat"
        fi
        
        echo "    ----------------------------------------"
    done
    
    if [ $file_count -eq 0 ]; then
        echo "  No matching files found in $folder"
    else
        echo "  Summary for $folder: $renamed_count/$file_count files renamed"
    fi
done

echo ""
echo "========================================"
echo "Renaming completed!"
echo "Total files renamed: $total_renamed"

# Show final directory structure
echo ""
echo "Final directory structure:"
for folder in "${folders[@]}"; do
    if [ -d "$folder" ]; then
        file_count=$(ls -1 "$folder" | wc -l)
        echo "  $folder/: $file_count file(s)"
        # Show a few example filenames
        if [ $file_count -gt 0 ]; then
            echo "    Sample files:"
            ls "$folder" | head -3 | sed 's/^/      /'
            if [ $file_count -gt 3 ]; then
                echo "      ..."
            fi
        fi
    fi
done 