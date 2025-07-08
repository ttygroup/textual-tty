#!/bin/sh

RED_TEXT=31
BLACK_BG=40
BLINK_ON=5
BLINK_OFF=25
RED_TEXT=31
RESET=0
APPLY=m

FLASH_RED="\033[${BLINK_ON};${RED_TEXT};${BLACK_BG}${APPLY}"
RED="\033[${BLINK_OFF};${RED_TEXT};${BLACK_BG}${APPLY}"
OFF="\033[${RESET}${APPLY}"

echo "$FLASH_RED▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜$OFF"
echo "$FLASH_RED▌${RED}  Software Failure.  Press left mouse button to continue  $FLASH_RED▐$OFF"
echo "$FLASH_RED▌${RED}            Guru Meditation #00000004.0000AAC0            $FLASH_RED▐$OFF"
echo "$FLASH_RED▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟$OFF"
echo "$RED                                                            $OFF"
echo "$RED                                                            $OFF"
echo "$RED                                                            $OFF"
echo "$RED                                                            $OFF"
echo "$RED                                                            $OFF"
echo "$RED                                                            $OFF"
echo "$RED                                                            $OFF"
echo "$RED                                                            $OFF"
echo "$RED                                                            $OFF"
echo "$RED                                                            $OFF"
echo "$RED                                                            $OFF"
echo "$RED                                                            $OFF"
echo "$RED                                                            $OFF"
echo "$RED                                                            $OFF"
echo "$RED                                                            $OFF"
