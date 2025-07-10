#!/bin/bash

# Read window title
read -p "Window title?: " window_title

# Read icon title
read -p "Window icon title?: " icon_title

# Check if no changes
if [[ -z "$window_title" && -z "$icon_title" ]]; then
    echo "No change"
    exit 0
fi

# Check if both are the same and both provided
if [[ -n "$window_title" && -n "$icon_title" && "$window_title" == "$icon_title" ]]; then
    echo "setting window and icon title to $window_title"
    printf "\033]0;%s\007" "$window_title"
else
    # Handle window title if provided
    if [[ -n "$window_title" ]]; then
        echo "setting window title to $window_title"
        printf "\033]2;%s\007" "$window_title"
    fi

    # Handle icon title if provided
    if [[ -n "$icon_title" ]]; then
        echo "setting icon title to $icon_title"
        printf "\033]1;%s\007" "$icon_title"
    fi
fi

# Wait for user to press return
read -p "Press return to exit"