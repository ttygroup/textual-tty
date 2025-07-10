"""
The Terminal Parser: A state machine for processing terminal input streams.

This module provides the `Parser` class, which consumes a stream of bytes
from a pseudo-terminal (pty) and translates it into high-level calls to a
`ScreenWriter` API.

It is a direct architectural port of tmux's `input.c`, implementing the same
finite state machine described by Paul Williams (https://vt100.net/emu/).

The core logic is in the `feed()` method, which processes each byte, moves
between states, and calls the appropriate handler methods for escape sequences.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List, Optional

if TYPE_CHECKING:
    from .terminal import Terminal

from rich.style import Style
from rich.color import Color
from .log import debug


class Parser:
    """
    A state machine that parses a stream of terminal control codes.

    The parser is always in one of several states (GROUND, ESCAPE, CSI_ENTRY,
    etc.). Each byte fed to the `feed()` method can cause a transition to a new
    state and/or execute a handler for a recognized escape sequence.
    """

    def __init__(self, terminal: Terminal) -> None:
        """
        Initializes the parser state. Replaces `input_init()`.

        Args:
            terminal: A Terminal object that the parser will manipulate.
        """
        self.terminal = terminal

        # The current state of the parser (e.g., 'GROUND', 'ESCAPE').
        self.current_state: str = "GROUND"

        # --- Buffers for collecting sequence data ---
        self.intermediate_chars: List[str] = []
        self.param_buffer: str = ""
        self.parsed_params: List[int | str] = []
        self.string_buffer: str = ""  # For OSC, DCS, APC strings
        self._string_exit_handler: Optional[Callable] = None

        # --- Current Cell Attributes ---
        # A `Style` object representing the style to be applied to the next
        # character written to the grid.
        self.current_style: Optional[Style] = None

    def feed(self, data: str) -> None:
        """
        Feeds a chunk of text into the parser. Replaces `input_parse_buffer()`.

        This is the main entry point. It iterates over the data and passes each
        character to the state machine engine.
        """
        for char in data:
            self._parse_char(char)

    def _parse_char(self, char: str) -> None:
        """
        The core state machine engine.

        It looks up the current state in `self.states`, finds the appropriate
        transition for the given byte, executes the handler, and moves to the
        next state.
        """
        # Simplified parser - handle basic cases
        if self.current_state == "GROUND":
            if char == "\x1b":  # ESC
                self.current_state = "ESCAPE"
                self._clear()
            elif char == "\x07":  # BEL
                pass  # Bell - could emit sound/flash
            elif char == "\x08":  # BS (Backspace)
                self.terminal.backspace()
            elif char == "\x7f":  # DEL (Delete/Backspace)
                self.terminal.backspace()
            elif char == "\x09":  # HT (Tab)
                # Simple tab handling - move to next tab stop
                self.terminal.cursor_x = ((self.terminal.cursor_x // 8) + 1) * 8
                if self.terminal.cursor_x >= self.terminal.width:
                    self.terminal.cursor_x = self.terminal.width - 1
            elif char == "\x0a":  # LF
                self.terminal.line_feed()
            elif char == "\x0d":  # CR
                self.terminal.carriage_return()
            elif ord(char) >= 0x20:  # Printable characters
                self.terminal.current_style = self.current_style
                self.terminal.write_text(char)
        elif self.current_state == "ESCAPE":
            if char == "[":  # CSI
                self.current_state = "CSI_ENTRY"
            elif char == "]":  # OSC (Operating System Command)
                self._clear()
                self.current_state = "OSC_STRING"
            elif char == "=":  # DECKPAM - Application Keypad Mode
                self.terminal.set_mode(1, True)  # Application keypad mode
                self.current_state = "GROUND"
            elif char == ">":  # DECKPNM - Normal Keypad Mode
                self.terminal.set_mode(1, False)  # Normal keypad mode
                self.current_state = "GROUND"
            elif char == "P":  # DCS - Device Control String
                self._clear()
                self.current_state = "DCS_STRING"
            elif char == "\\":  # ST - String Terminator
                # End of string sequence
                self.current_state = "GROUND"
            elif char == "c":  # RIS (Reset)
                self._esc_dispatch(char)
                self.current_state = "GROUND"
            elif char == "D":  # IND (Index)
                self._esc_dispatch(char)
                self.current_state = "GROUND"
            elif char == "M":  # RI (Reverse Index)
                self._esc_dispatch(char)
                self.current_state = "GROUND"
            elif char == "7":  # DECSC (Save Cursor)
                self._esc_dispatch(char)
                self.current_state = "GROUND"
            elif char == "8":  # DECRC (Restore Cursor)
                self._esc_dispatch(char)
                self.current_state = "GROUND"
            elif char == ">":  # DECKPNM (Keypad Numeric Mode)
                # Set keypad to numeric mode - just consume it
                self.current_state = "GROUND"
            elif char == "(":  # G0 character set designation
                # ESC ( followed by character set designator - consume next char
                self.current_state = "CHARSET_G0"
            elif char == ")":  # G1 character set designation
                # ESC ) followed by character set designator - consume next char
                self.current_state = "CHARSET_G1"
            else:
                # Unknown escape sequence, log and go back to ground
                debug(f"Unknown escape sequence: ESC {char!r}")
                self.current_state = "GROUND"
        elif self.current_state in ("CSI_ENTRY", "CSI_PARAM", "CSI_INTERMEDIATE"):
            self._handle_csi(char)
        elif self.current_state == "OSC_STRING":
            if char == "\x07":  # BEL - terminates OSC
                self._handle_osc_dispatch()
                self.current_state = "GROUND"
            elif char == "\x1b":  # ESC - might be start of ST (String Terminator)
                self.current_state = "OSC_ESC"
            else:
                # Collect characters for OSC string
                self.string_buffer += char
        elif self.current_state == "OSC_ESC":
            if char == "\\":  # ST (String Terminator) - ESC \
                self._handle_osc_dispatch()
                self.current_state = "GROUND"
            else:
                # Not ST, treat as regular character
                self.string_buffer += "\x1b" + char
                self.current_state = "OSC_STRING"
        elif self.current_state == "DCS_STRING":
            if char == "\x07":  # BEL - terminates DCS
                self._handle_dcs_dispatch()
                self.current_state = "GROUND"
            elif char == "\x1b":  # ESC - might be start of ST (String Terminator)
                self.current_state = "DCS_ESC"
            else:
                # Collect characters for DCS string
                self.string_buffer += char
        elif self.current_state == "DCS_ESC":
            if char == "\\":  # ST (String Terminator) - ESC \
                self._handle_dcs_dispatch()
                self.current_state = "GROUND"
            else:
                # Not ST, treat as regular character
                self.string_buffer += "\x1b" + char
                self.current_state = "DCS_STRING"
        elif self.current_state == "CHARSET_G0":
            # Character set designation for G0 - just consume and go back to ground
            self.current_state = "GROUND"
        elif self.current_state == "CHARSET_G1":
            # Character set designation for G1 - just consume and go back to ground
            self.current_state = "GROUND"

    def _handle_csi(self, char: str) -> None:
        """Generic handler for CSI_ENTRY, CSI_PARAM, and CSI_INTERMEDIATE states."""
        # Final byte is the same for all CSI states
        if "\x40" <= char <= "\x7e":
            self._csi_dispatch(char)
            self.current_state = "GROUND"
            return

        # Parameter bytes
        if "\x30" <= char <= "\x3b":
            self._collect_parameter(char)
            if self.current_state == "CSI_ENTRY":
                self.current_state = "CSI_PARAM"
            return

        # Intermediate bytes
        if "\x20" <= char <= "\x2f":
            self._collect_intermediate(char)
            self.current_state = "CSI_INTERMEDIATE"
            return

        # Private parameter bytes (only valid in CSI_ENTRY)
        if "\x3c" <= char <= "\x3f":
            if self.current_state == "CSI_ENTRY":
                self._collect_intermediate(char)
                self.current_state = "CSI_PARAM"
            else:
                # Invalid in other CSI states
                debug(f"Invalid CSI character: {char!r}")
                self.current_state = "GROUND"
            return

        # Any other character is invalid
        debug(f"Invalid CSI character: {char!r}")
        self.current_state = "GROUND"

    def reset(self) -> None:
        """
        Resets the parser to its initial ground state.
        """
        self._clear()
        self.current_state = "GROUND"

    # --- State Buffer and Parameter Handling Methods ---

    def _clear(self) -> None:
        """
        Clears all temporary buffers used for parsing sequences.

        This is called when entering a new escape sequence (ESC, CSI, OSC, etc.)
        to ensure old parameter or intermediate data is discarded.
        """
        self.intermediate_chars.clear()
        self.param_buffer = ""
        self.parsed_params.clear()
        self.string_buffer = ""

    def _collect_intermediate(self, char: str) -> None:
        """
        Collects an intermediate character for an escape sequence.

        In a sequence like `CSI ? 25 h`, the '?' is an intermediate character.
        This method appends it to an internal buffer.
        """
        self.intermediate_chars.append(char)

    def _collect_parameter(self, char: str) -> None:
        """
        Collects a parameter character for a sequence.

        This collects characters like '3', '8', ';', '5' from a parameter
        string like "38;5;21". The `_split_params` method will later parse this.
        """
        self.param_buffer += char

    def _split_params(self, param_string: str) -> None:
        """
        Parses parameter string like "1;2;3" or "38;5;196" into integers.

        Handles empty parameters and sub-parameters (takes only the first part before ':').
        """
        self.parsed_params.clear()
        if not param_string:
            return

        for part in param_string.split(";"):
            if not part:
                self.parsed_params.append(None)
                continue

            # Handle sub-parameters: take only the main part before ':'
            main_part = part.split(":")[0]

            try:
                self.parsed_params.append(int(main_part))
            except ValueError:
                self.parsed_params.append(0)

    def _get_param(self, index: int, default: int) -> int:
        """
        Gets a numeric parameter from the parsed list, with a default value.
        """
        if index < len(self.parsed_params):
            param = self.parsed_params[index]
            return param if param is not None else default
        return default

    # --- Escape (ESC) Sequence Dispatchers ---

    def _esc_dispatch(self, final_char: str) -> None:
        """
        Handles an ESC-based escape sequence (ones that do not start with CSI).

        This is a top-level dispatcher that will look up the sequence in a
        dispatch table and call the appropriate handler method.

        Relevant constants (`enum input_esc_type`):
        - `DECSC`: Save cursor position and attributes.
        - `DECRC`: Restore saved cursor position and attributes.
        - `DECKPAM`: Enter keypad application mode.
        - `DECKPNM`: Exit keypad numeric mode.
        - `RIS`: Hard reset to initial state.
        - `IND`: Index (move cursor down one line).
        - `NEL`: Next Line (equivalent to CR+LF).
        - `HTS`: Set a horizontal tab stop at the current cursor column.
        - `RI`: Reverse Index (move cursor up one line, scrolling if needed).
        - `SCSG0_ON`, `SCSG1_ON`: Designate G0/G1 charsets as ACS line drawing.
        - `SCSG0_OFF`, `SCSG1_OFF`: Designate G0/G1 charsets as ASCII.
        - `DECALN`: Screen alignment test (fills screen with 'E').
        """
        if final_char == "c":  # RIS (Reset in State)
            self._reset_terminal()
        elif final_char == "D":  # IND (Index)
            self.terminal.line_feed()
        elif final_char == "M":  # RI (Reverse Index)
            if self.terminal.cursor_y <= self.terminal.scroll_top:
                self.terminal.scroll_down(1)
            else:
                self.terminal.cursor_y -= 1
        elif final_char == "7":  # DECSC (Save Cursor)
            self.terminal.save_cursor()
        elif final_char == "8":  # DECRC (Restore Cursor)
            self.terminal.restore_cursor()
        # Add more ESC sequences as needed

    # --- Control Sequence Introducer (CSI) Dispatchers ---

    def _csi_dispatch(self, final_char: str) -> None:
        """
        Handles a CSI-based escape sequence (starts with `ESC[`).

        This is a major dispatcher that handles dozens of terminal commands. It will
        look up the final character and intermediate characters in a dispatch
        table and call the specific handler.

        Key branches from C (`enum input_csi_type`):
        - `CUP` (Cursor Position): Moves cursor to (y, x).
        - `ED` (Erase in Display): Clears parts of the screen.
        - `EL` (Erase in Line): Clears parts of the current line.
        - `SGR` (Select Graphic Rendition): Calls `_csi_dispatch_sgr` to set colors/attrs.
        - `SM`/`RM` (Set/Reset Mode): Calls helpers to set/reset terminal modes.
        - `DECSTBM`: Sets the top and bottom margins for the scroll region.
        - `ICH`/`DCH`: Insert/Delete characters.
        - `IL`/`DL`: Insert/Delete lines.
        - `SU`/`SD`: Scroll Up/Down.
        - `DA`/`XDA`: Device Attributes request, which requires sending a response.
        - `DSR`: Device Status Report request, also requires a response.
        - `REP`: Repeat the preceding character N times.
        - `DECSCUSR`: Set cursor style (block, underline, bar).
        """
        # Parse parameters
        self._split_params(self.param_buffer)

        # Handle common CSI sequences
        if final_char == "H" or final_char == "f":  # CUP - Cursor Position
            row = self._get_param(0, 1) - 1  # Convert to 0-based
            col = self._get_param(1, 1) - 1  # Convert to 0-based
            self.terminal.set_cursor(col, row)
        elif final_char == "A":  # CUU - Cursor Up
            count = self._get_param(0, 1)
            self.terminal.cursor_y = max(0, self.terminal.cursor_y - count)
        elif final_char == "B":  # CUD - Cursor Down
            count = self._get_param(0, 1)
            self.terminal.cursor_y = min(self.terminal.height - 1, self.terminal.cursor_y + count)
        elif final_char == "C":  # CUF - Cursor Forward
            count = self._get_param(0, 1)
            self.terminal.cursor_x = min(self.terminal.width - 1, self.terminal.cursor_x + count)
        elif final_char == "D":  # CUB - Cursor Backward
            count = self._get_param(0, 1)
            self.terminal.cursor_x = max(0, self.terminal.cursor_x - count)
        elif final_char == "G":  # CHA - Cursor Horizontal Absolute
            col = self._get_param(0, 1) - 1  # Convert to 0-based
            self.terminal.set_cursor(col, None)
        elif final_char == "d":  # VPA - Vertical Position Absolute
            row = self._get_param(0, 1) - 1  # Convert to 0-based
            self.terminal.set_cursor(None, row)
        elif final_char == "J":  # ED - Erase in Display
            mode = self._get_param(0, 0)
            self.terminal.clear_screen(mode)
        elif final_char == "K":  # EL - Erase in Line
            mode = self._get_param(0, 0)
            self.terminal.clear_line(mode)
        elif final_char == "L":  # IL - Insert Lines
            count = self._get_param(0, 1)
            self.terminal.insert_lines(count)
        elif final_char == "M":  # DL - Delete Lines
            count = self._get_param(0, 1)
            self.terminal.delete_lines(count)
        elif final_char == "@":  # ICH - Insert Characters
            count = self._get_param(0, 1)
            self.terminal.insert_characters(count)
        elif final_char == "P":  # DCH - Delete Characters
            count = self._get_param(0, 1)
            self.terminal.delete_characters(count)
        elif final_char == "S":  # SU - Scroll Up
            count = self._get_param(0, 1)
            self.terminal.scroll_up(count)
        elif final_char == "T":  # SD - Scroll Down
            count = self._get_param(0, 1)
            self.terminal.scroll_down(count)
        elif final_char == "r":  # DECSTBM - Set Scroll Region
            top = self._get_param(0, 1) - 1  # Convert to 0-based
            bottom = self._get_param(1, self.terminal.height) - 1  # Convert to 0-based
            self.terminal.set_scroll_region(top, bottom)
        elif final_char == "b":  # REP - Repeat
            count = self._get_param(0, 1)
            self.terminal.repeat_last_character(count)
        elif final_char == "m":  # SGR - Select Graphic Rendition
            self._csi_dispatch_sgr()
        elif final_char == "h":  # SM - Set Mode
            self._csi_dispatch_sm_rm(True)
        elif final_char == "l":  # RM - Reset Mode
            self._csi_dispatch_sm_rm(False)
        elif final_char == "p":  # Device status queries or mode setting
            # Various device status queries - we consume but don't respond
            # This could be device attributes, mode queries, etc.
            pass
        elif final_char == "t":  # Window operations
            # Various window operations (resize, position queries, etc.)
            # We consume but don't implement window operations
            pass
        elif final_char == "^":  # PM (Privacy Message)
            # Privacy message - we consume but don't implement
            pass
        elif final_char == "s":  # DECSC - Save Cursor (alternative)
            # Save cursor position and attributes
            self.terminal.save_cursor()
        elif final_char == "u":  # DECRC - Restore Cursor (alternative)
            # Restore cursor position and attributes
            self.terminal.restore_cursor()
        elif final_char == "X":  # ECH - Erase Character (possibly with intermediate)
            # Erase n characters at cursor position
            count = self._get_param(0, 1)
            # For now, treat this as delete characters (could be improved)
            for _ in range(count):
                self.terminal.current_buffer.set(self.terminal.cursor_x, self.terminal.cursor_y, " ")
                if self.terminal.cursor_x < self.terminal.width - 1:
                    self.terminal.cursor_x += 1
        elif final_char == "n":  # Device Status Report / Cursor Position Report
            # This is often used by programs to query cursor position
            # We don't need to respond as this is just for compatibility
            pass
        elif final_char == "c":  # Device Attributes
            # Programs query terminal capabilities - we just ignore
            pass
        else:
            # Unknown CSI sequence, log it
            params_str = self.param_buffer if self.param_buffer else "<no params>"
            debug(f"Unknown CSI sequence: ESC[{params_str}{final_char}")

    def _csi_dispatch_sm_rm_private(self, set_mode: bool) -> None:
        """
        Handles private SM/RM sequences (prefixed with `?`).

        Key modes handled (`MODE_*` constants):
        - `?1` (DECCKM): Set cursor keys to application mode.
        - `?7` (DECAWM): Enable/disable autowrap mode.
        - `?12`: Set cursor blinking.
        - `?25`: Show/hide cursor.
        - `?1000-?1003, ?1005, ?1006`: Enable various mouse tracking modes.
        - `?1049`: Enable alternate screen buffer.
        - `?2004`: Enable bracketed paste mode.
        """
        for param in self.parsed_params:
            if param == 1:  # DECCKM - Cursor Keys Application Mode
                # self.terminal.cursor_key_application_mode = set_mode # Not yet implemented
                pass
            elif param == 7:  # DECAWM - Auto-wrap Mode
                self.terminal.auto_wrap = set_mode
            elif param == 25:  # Show/hide cursor
                self.terminal.cursor_visible = set_mode
            elif param == 47:  # Alternate screen buffer (older form)
                if set_mode:
                    self.terminal.alternate_screen_on()
                else:
                    self.terminal.alternate_screen_off()
            elif param == 1049:  # Alternate screen buffer (newer form)
                if set_mode:
                    self.terminal.alternate_screen_on()
                else:
                    self.terminal.alternate_screen_off()
            elif param == 1000:  # Basic mouse tracking
                self.terminal.set_mode(1000, set_mode, private=True)
            elif param == 1002:  # Button event tracking
                self.terminal.set_mode(1002, set_mode, private=True)
            elif param == 1003:  # Any event tracking (movement)
                self.terminal.set_mode(1003, set_mode, private=True)
            elif param == 1006:  # SGR mouse mode
                self.terminal.set_mode(1006, set_mode, private=True)
            elif param == 1015:  # Extended mouse mode
                self.terminal.set_mode(1015, set_mode, private=True)
            # Add more private modes as needed

    # --- OSC, DCS, and other String-based Sequence Handlers ---

    def _handle_osc_dispatch(self) -> None:
        """
        Dispatches an OSC (Operating System Command) string.

        Parses the command number and calls the appropriate handler.
        - `0` or `2`: Set window/icon title.
        - `4`: Set color palette entry.
        - `7`: Set current working directory/URL.
        - `8`: Define hyperlink.
        - `10`: Set default foreground color.
        - `11`: Set default background color.
        - `12`: Set cursor color.
        - `52`: Set/query clipboard content.
        - `104`: Reset color palette entry.
        - `110, 111, 112`: Reset fg/bg/cursor color to default.
        """
        if not self.string_buffer:
            return

        # Parse OSC command: number;data
        parts = self.string_buffer.split(";", 1)
        if len(parts) < 1:
            return

        try:
            cmd = int(parts[0])
        except ValueError:
            return

        # Handle title setting commands (0 and 2)
        if cmd == 0 or cmd == 2:
            # Set window/icon title - we ignore this but consume it
            # so it doesn't leak through to the screen
            pass

        # For now, we just consume OSC sequences without implementing them
        # This prevents them from leaking through to the terminal output

    def _handle_dcs_dispatch(self) -> None:
        """
        Dispatches a DCS (Device Control String).

        Primarily used for passthrough (`tmux;...`) sequences or for things
        like Sixel graphics if support is enabled.
        """
        pass

    def _reset_terminal(self) -> None:
        """Reset terminal to initial state."""
        self.terminal.clear_screen(2)
        self.terminal.set_cursor(0, 0)
        self.current_style = Style()

    def _csi_dispatch_sgr(self) -> None:
        """
        Handles SGR (Select Graphic Rendition) sequences to set text style.

        This is one of the most complex handlers. It iterates through the list
        of numeric parameters from the sequence and applies each one.

        Key branches from C:
        - `0`: Reset all attributes.
        - `1..9`: Set Bold, Dim, Italic, Underline, Blink, Reverse, Hidden, Strikethrough.
        - `21..29`: Reset specific attributes.
        - `30-37`, `40-47`: Set standard 16-color foreground/background.
        - `90-97`, `100-107`: Set bright 16-color foreground/background.
        - `39, 49, 59`: Reset foreground, background, and underline color to default.
        - `38`: Begins an extended color sequence (256-color or RGB).
          - `38:5:{n}` or `38;5;{n}`: 256-color mode.
          - `38:2::{r}:{g}:{b}` or `38;2;{r};{g};{b}`: RGB truecolor mode.
        - `48`: Begins an extended background color sequence.
        - `58`: Begins an extended underline color sequence.
        """
        if not self.parsed_params:
            # Default to [0] if no parameters are given
            self.parsed_params = [0]

        # Ensure current_style is always a Style object
        if self.current_style is None:
            self.current_style = Style()

        it = iter(self.parsed_params)
        while True:
            try:
                param = next(it)
            except StopIteration:
                break

            if param == 0:
                # Reset all attributes
                self.current_style = Style()
            elif param == 1:
                self.current_style += Style(bold=True)
            elif param == 2:
                self.current_style += Style(dim=True)
            elif param == 3:
                self.current_style += Style(italic=True)
            elif param == 4:
                self.current_style += Style(underline=True)
            elif param == 5:
                self.current_style += Style(blink=True)
            elif param == 7:
                self.current_style += Style(reverse=True)
            elif param == 8:
                self.current_style += Style(conceal=True)
            elif param == 9:
                self.current_style += Style(strike=True)
            elif param == 21:  # Not bold/double underline
                self.current_style += Style(bold=False)
            elif param == 22:  # Neither bold nor faint
                self.current_style += Style(bold=False, dim=False)
            elif param == 23:  # Not italic
                self.current_style += Style(italic=False)
            elif param == 24:  # Not underlined
                self.current_style += Style(underline=False)
            elif param == 25:  # Not blinking
                self.current_style += Style(blink=False)
            elif param == 27:  # Not reversed
                self.current_style += Style(reverse=False)
            elif param == 28:  # Not hidden
                self.current_style += Style(conceal=False)
            elif param == 29:  # Not strikethrough
                self.current_style += Style(strike=False)
            elif 30 <= param <= 37:
                # Standard 16-color foreground
                self.current_style += Style(color=Color.from_ansi(param - 30))
            elif param == 38:
                # Extended foreground color
                new_color = None
                try:
                    color_type = next(it)
                    if color_type == 5:  # 256-color
                        color_code = next(it)
                        # Check if we have enough parameters - if color_code came from empty string
                        # we should consider this malformed
                        if color_code is not None:
                            new_color = Color.from_ansi(color_code)
                    elif color_type == 2:  # Truecolor (RGB)
                        r = next(it)
                        g = next(it)
                        b = next(it)
                        # Check if we have valid RGB values
                        if r is not None and g is not None and b is not None:
                            new_color = Color.from_rgb(r, g, b)
                except StopIteration:
                    # Malformed sequence, ignore
                    pass
                if new_color is not None:
                    self.current_style += Style(color=new_color)
            elif param == 39:
                # Default foreground color
                self.current_style += Style(color=Color.default())
            elif 40 <= param <= 47:
                # Standard 16-color background
                self.current_style += Style(bgcolor=Color.from_ansi(param - 40))
            elif param == 48:
                # Extended background color
                new_bgcolor = None
                try:
                    color_type = next(it)
                    if color_type == 5:  # 256-color
                        color_code = next(it)
                        # Check if we have enough parameters - if color_code came from empty string
                        # we should consider this malformed
                        if color_code is not None:
                            new_bgcolor = Color.from_ansi(color_code)
                    elif color_type == 2:  # Truecolor (RGB)
                        r = next(it)
                        g = next(it)
                        b = next(it)
                        # Check if we have valid RGB values
                        if r is not None and g is not None and b is not None:
                            new_bgcolor = Color.from_rgb(r, g, b)
                except StopIteration:
                    # Malformed sequence, ignore
                    pass
                if new_bgcolor is not None:
                    self.current_style += Style(bgcolor=new_bgcolor)
            elif param == 49:
                # Default background color
                self.current_style += Style(bgcolor=Color.default())
            elif 90 <= param <= 97:
                # Bright 16-color foreground
                self.current_style += Style(color=Color.from_ansi(param - 90 + 8))
            elif 100 <= param <= 107:
                # Bright 16-color background
                self.current_style += Style(bgcolor=Color.from_ansi(param - 100 + 8))

        # Update the terminal's current_style
        self.terminal.current_style = self.current_style

    def _csi_dispatch_sm_rm(self, set_mode: bool) -> None:
        """Handle SM (Set Mode) and RM (Reset Mode) sequences."""
        if "?" in self.intermediate_chars:
            self._csi_dispatch_sm_rm_private(set_mode)
            return

        # Basic mode handling - expand as needed
        for param in self.parsed_params:
            if param == 7:  # Auto-wrap mode
                self.terminal.auto_wrap = set_mode
            elif param == 25:  # Cursor visibility
                self.terminal.cursor_visible = set_mode
