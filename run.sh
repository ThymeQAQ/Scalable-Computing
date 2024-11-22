#!/bin/bash

echo "Starting the project execution..."

FOLDERS=(
    "e2s"
    "s2s_routing"
    "s2s"
    "leo_network_simulation"
    "ml_image"
)

for folder in "${FOLDERS[@]}"; do
    SCRIPT="$folder/run.sh"
    echo "----------------------------------------"
    echo "Running $SCRIPT in a new terminal..."

    if [ -f "$SCRIPT" ]; then
        wt.exe new-tab --title "$folder" bash -c "cd $folder && bash run.sh"
        sleep 5  
    else
        echo "Error: $SCRIPT not found in $folder. Skipping..."
    fi
done

echo "All scripts executed successfully."
