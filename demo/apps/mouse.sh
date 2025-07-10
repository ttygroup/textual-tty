#!/bin/bash
# Mouse state demo - shows mouse position and button states
# Press 'q' to quit, Ctrl+C also works with proper cleanup

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
CURSOR='\033[7m \033[0m'  # Inverted space for cursor

# Mouse tracking modes (1003 = report all mouse movement)
MOUSE_ENABLE='\033[?1000h\033[?1002h\033[?1003h\033[?1015h\033[?1006h'
MOUSE_DISABLE='\033[?1006l\033[?1015l\033[?1003l\033[?1002l\033[?1000l'

# Cleanup function
cleanup() {
    printf "${MOUSE_DISABLE}"
    printf "\033[?25h"  # Show cursor
    printf "\033[2J\033[H"  # Clear screen and go to top
    echo "Mouse reporting disabled. Goodbye!"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM EXIT

# Track cursor position for redrawing
last_mouse_x=0
last_mouse_y=0

# Get actual terminal dimensions
TERM_ROWS=$(tput lines)
TERM_COLS=$(tput cols)

# Initialize
clear
printf "\033[?25l"  # Hide cursor
printf "${MOUSE_ENABLE}"  # Enable mouse reporting

# Display header
printf "\033[H"  # Go to top
echo -e "${BLUE}=== Mouse State Demo ===${NC}"
echo -e "${YELLOW}Move mouse and click buttons. Press 'q' to quit, Ctrl+C to exit.${NC}"
echo ""
echo -e "${GREEN}Mouse Position: ${NC}Not detected yet"
echo -e "${GREEN}Button State:   ${NC}None"
echo -e "${GREEN}Event Type:     ${NC}Waiting..."
echo -e "${GREEN}Modifiers:      ${NC}None"
echo ""

# Read mouse events
while true; do
    # Read a single character/sequence
    read -rsn1 input
    
    # Check for 'q' to quit
    if [[ "$input" == "q" ]]; then
        break
    fi
    
    # Check for escape sequence (mouse event)
    if [[ "$input" == $'\033' ]]; then
        # Read the rest of the escape sequence
        read -rsn1 next
        if [[ "$next" == "[" ]]; then
            # This is a CSI sequence, read until we get the final character
            sequence=""
            while true; do
                read -rsn1 char
                sequence+="$char"
                # CSI sequences end with a letter or specific characters
                if [[ "$char" =~ [a-zA-Z~] ]]; then
                    break
                fi
            done
            
            # Parse mouse event (SGR format: ESC[<b;x;yM or ESC[<b;x;ym)
            if [[ "$sequence" =~ ^\<([0-9]+)\;([0-9]+)\;([0-9]+)([Mm]) ]]; then
                button="${BASH_REMATCH[1]}"
                x="${BASH_REMATCH[2]}"
                y="${BASH_REMATCH[3]}"
                action="${BASH_REMATCH[4]}"
                
                # Decode button state
                button_num=$((button & 3))
                case $button_num in
                    0) button_name="Left" ;;
                    1) button_name="Middle" ;;
                    2) button_name="Right" ;;
                    3) button_name="Release" ;;
                esac
                
                # Check for drag
                if (( button & 32 )); then
                    event_type="Drag"
                elif [[ "$action" == "M" ]]; then
                    event_type="Press"
                else
                    event_type="Release"
                fi
                
                # Check for modifiers
                modifiers=""
                if (( button & 4 )); then modifiers+="Shift "; fi
                if (( button & 8 )); then modifiers+="Meta "; fi
                if (( button & 16 )); then modifiers+="Ctrl "; fi
                if [[ -z "$modifiers" ]]; then modifiers="None"; fi
                
                # Clear old cursor position (if within terminal bounds)
                if (( last_mouse_y >= 10 && last_mouse_y <= TERM_ROWS && last_mouse_x >= 1 && last_mouse_x <= TERM_COLS )); then
                    printf "\033[%d;%dH " "$last_mouse_y" "$last_mouse_x"
                fi
                
                # Draw new cursor at mouse position (if within terminal bounds, below header)
                if (( y >= 10 && y <= TERM_ROWS && x >= 1 && x <= TERM_COLS )); then
                    printf "\033[%d;%dH${CURSOR}" "$y" "$x"
                fi
                
                # Update tracking variables
                last_mouse_x="$x"
                last_mouse_y="$y"
                
                # Update display
                printf "\033[4;1H"  # Go to line 4, column 1
                printf "\033[K${GREEN}Mouse Position: ${NC}%3d, %3d" "$x" "$y"
                printf "\033[5;1H"  # Go to line 5, column 1  
                printf "\033[K${GREEN}Button State:   ${NC}%s" "$button_name"
                printf "\033[6;1H"  # Go to line 6, column 1
                printf "\033[K${GREEN}Event Type:     ${NC}%s" "$event_type"
                printf "\033[7;1H"  # Go to line 7, column 1
                printf "\033[K${GREEN}Modifiers:      ${NC}%s" "$modifiers"
                
                # Add some debug info
                printf "\033[9;1H"  # Go to line 9, column 1
                printf "\033[K${BLUE}Raw: ${NC}ESC[<%d;%d;%d%s (button=%d)" "$button" "$x" "$y" "$action" "$button"
            fi
        fi
    fi
done

# Cleanup happens automatically via trap