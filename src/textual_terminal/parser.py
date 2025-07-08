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

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

if TYPE_CHECKING:
    from .screen import TerminalScreen

from rich.style import Style
from rich.color import Color


class Parser:
    """
    A state machine that parses a stream of terminal control codes.

    The parser is always in one of several states (GROUND, ESCAPE, CSI_ENTRY,
    etc.). Each byte fed to the `feed()` method can cause a transition to a new
    state and/or execute a handler for a recognized escape sequence.
    """

    def __init__(self, screen: TerminalScreen) -> None:
        """
        Initializes the parser state. Replaces `input_init()`.

        Args:
            screen: A TerminalScreen object that the parser will manipulate.
        """
        self.screen = screen

        # The current state of the parser (e.g., 'GROUND', 'ESCAPE').
        self.current_state: str = "GROUND"

        # A mapping of states to their transition handlers. In Python, this
        # replaces the C array of structs. The values would be dictionaries
        # mapping byte ranges to handler methods and next states.
        self.states: Dict[str, Any] = {}

        # --- Buffers for collecting sequence data ---
        self.intermediate_chars: List[str] = []
        self.param_buffer: str = ""
        self.parsed_params: List[int | str] = []
        self.string_buffer: str = ""  # For OSC, DCS, APC strings

        # --- Saved Cursor and Attribute State (for DECSC/DECRC) ---
        self.saved_cx: int = 0
        self.saved_cy: int = 0
        self.saved_style: Optional[Style] = None
        self.saved_charset: Dict[str, str] = {}  # G0/G1 charset state

        # --- Current Cell Attributes ---
        # A `Style` object representing the style to be applied to the next
        # character written to the grid.
        self.current_style: Optional[Style] = None
        # State for G0/G1 character sets.
        self.current_charset: Dict[str, str] = {}

    def feed(self, data: bytes) -> None:
        """
        Feeds a chunk of bytes into the parser. Replaces `input_parse_buffer()`.

        This is the main entry point. It iterates over the data and passes each
        byte to the state machine engine.

        Args:
            data: A chunk of bytes read from the application's pty.
        """
        for byte in data:
            self._parse_byte(byte)

    def _parse_byte(self, byte: int) -> None:
        """
        The core state machine engine. Replaces the main loop in `input_parse()`.

        It looks up the current state in `self.states`, finds the appropriate
        transition for the given byte, executes the handler, and moves to the
        next state.
        """
        # Simplified parser - handle basic cases
        if self.current_state == "GROUND":
            if byte == 0x1B:  # ESC
                self.current_state = "ESCAPE"
                self._clear()
            elif byte == 0x07:  # BEL
                pass  # Bell - could emit sound/flash
            elif byte == 0x08:  # BS
                self.screen.backspace()
            elif byte == 0x09:  # HT (Tab)
                # Simple tab handling - move to next tab stop
                self.screen.cursor_x = ((self.screen.cursor_x // 8) + 1) * 8
                if self.screen.cursor_x >= self.screen.width:
                    self.screen.cursor_x = self.screen.width - 1
            elif byte == 0x0A:  # LF
                self.screen.line_feed()
            elif byte == 0x0D:  # CR
                self.screen.carriage_return()
            elif byte >= 0x20:  # Printable characters
                char = chr(byte)
                self.screen.write_cell(char, self.screen.current_style)
        elif self.current_state == "ESCAPE":
            if byte == ord("["):  # CSI
                self.current_state = "CSI_ENTRY"
            elif byte == ord("c"):  # RIS (Reset)
                self._reset_terminal()
                self.current_state = "GROUND"
            elif byte == ord("D"):  # IND (Index)
                self.screen.line_feed()
                self.current_state = "GROUND"
            elif byte == ord("M"):  # RI (Reverse Index)
                if self.screen.cursor_y <= self.screen.scroll_top:
                    self.screen.scroll_down(1)
                else:
                    self.screen.cursor_y -= 1
                self.current_state = "GROUND"
            elif byte == ord("7"):  # DECSC (Save Cursor)
                self.screen.save_cursor()
                self.current_state = "GROUND"
            elif byte == ord("8"):  # DECRC (Restore Cursor)
                self.screen.restore_cursor()
                self.current_state = "GROUND"
            else:
                # Unknown escape sequence, go back to ground
                self.current_state = "GROUND"
        elif self.current_state == "CSI_ENTRY":
            if byte == ord("?"):  # Private parameter
                self.intermediate_chars.append("?")
                self.current_state = "CSI_PARAM"
            elif 0x30 <= byte <= 0x3F:  # Parameter bytes
                self.param_buffer += chr(byte)
                self.current_state = "CSI_PARAM"
            elif 0x40 <= byte <= 0x7E:  # Final byte
                self._csi_dispatch(chr(byte))
                self.current_state = "GROUND"
            else:
                # Invalid, return to ground
                self.current_state = "GROUND"
        elif self.current_state == "CSI_PARAM":
            if 0x30 <= byte <= 0x3F:  # Parameter bytes
                self.param_buffer += chr(byte)
            elif 0x40 <= byte <= 0x7E:  # Final byte
                self._csi_dispatch(chr(byte))
                self.current_state = "GROUND"
            else:
                # Invalid, return to ground
                self.current_state = "GROUND"

    def reset(self) -> None:
        """
        Resets the parser to its initial ground state. Replaces `input_reset()`.
        """
        # This would call _clear() and reset the state to GROUND.
        pass

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

    def _ground(self) -> None:
        """
        Handler for transitioning to the GROUND state.

        This is the default state where printable characters are processed. This
        handler ensures any long-running sequence timers are cancelled.
        """
        pass

    def _collect_intermediate(self, char: str) -> None:
        """
        Collects an intermediate character for an escape sequence.

        In a sequence like `CSI ? 25 h`, the '?' is an intermediate character.
        This method appends it to an internal buffer.
        """
        pass

    def _collect_parameter(self, char: str) -> None:
        """
        Collects a parameter character for a sequence.

        This collects characters like '3', '8', ';', '5' from a parameter
        string like "38;5;21". The `_split_params` method will later parse this.
        """
        pass

    def _split_params(self, param_string: str) -> None:
        """
        Parses the collected parameter string into a list of numbers/sub-params.

        It splits the string by ';' and handles sub-parameters separated by ':'.
        This logic replaces `input_split`.
        """
        self.parsed_params.clear()
        if not param_string:
            return

        parts = param_string.split(";")
        for part in parts:
            if ":" in part:
                # Sub-parameters - for now, just take the first one
                sub_parts = part.split(":")
                try:
                    self.parsed_params.append(int(sub_parts[0]) if sub_parts[0] else 0)
                except ValueError:
                    self.parsed_params.append(0)
            else:
                try:
                    self.parsed_params.append(int(part) if part else 0)
                except ValueError:
                    self.parsed_params.append(0)

    def _get_param(self, index: int, default: int) -> int:
        """
        Gets a numeric parameter from the parsed list, with a default value.
        This replaces `input_get`.
        """
        if index < len(self.parsed_params):
            return self.parsed_params[index]
        return default

    # --- C0 Control Code Dispatcher ---

    def _c0_dispatch(self, char_code: int) -> None:
        """
        Handles C0 control codes (bytes from 0x00 to 0x1F).

        This is a dispatch method that calls the appropriate `screen_writer`
        method based on the control code.

        Relevant constants from C (`input_c0_dispatch`):
        - `\a` (BEL): Triggers a bell/alert.
        - `\b` (BS): Moves cursor back one space.
        - `\t` (HT): Moves cursor to the next tab stop.
        - `\n` (LF), `\v` (VT), `\f` (FF): Line feed. May also perform a
          carriage return if MODE_CRLF is set.
        - `\r` (CR): Carriage return (moves cursor to column 0).
        - `\x0e` (SO): Shift Out, activates the G1 charset (for line drawing).
        - `\x0f` (SI): Shift In, activates the G0 charset (the default).
        """
        pass

    # --- Printable Character Handlers ---

    def _print(self, char: str) -> None:
        """
        Handles a standard printable character.

        This method gets the current character attributes (color, bold, etc.)
        and calls the screen writer's `write_cell` method.
        """
        pass

    def _handle_utf8(self, byte: int) -> None:
        """
        Assembles multi-byte UTF-8 characters. Replaces `input_top_bit_set`.

        This method collects bytes for a UTF-8 sequence until a complete
        character is formed, then passes the resulting character and its
        calculated width to the screen writer.
        """
        pass

    # --- Escape (ESC) Sequence Dispatchers ---

    def _esc_dispatch(self) -> None:
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
        pass

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
            self.screen.set_cursor(col, row)
        elif final_char == "A":  # CUU - Cursor Up
            count = self._get_param(0, 1)
            self.screen.cursor_y = max(0, self.screen.cursor_y - count)
        elif final_char == "B":  # CUD - Cursor Down
            count = self._get_param(0, 1)
            self.screen.cursor_y = min(self.screen.height - 1, self.screen.cursor_y + count)
        elif final_char == "C":  # CUF - Cursor Forward
            count = self._get_param(0, 1)
            self.screen.cursor_x = min(self.screen.width - 1, self.screen.cursor_x + count)
        elif final_char == "D":  # CUB - Cursor Backward
            count = self._get_param(0, 1)
            self.screen.cursor_x = max(0, self.screen.cursor_x - count)
        elif final_char == "G":  # CHA - Cursor Horizontal Absolute
            col = self._get_param(0, 1) - 1  # Convert to 0-based
            self.screen.set_cursor(col, None)
        elif final_char == "d":  # VPA - Vertical Position Absolute
            row = self._get_param(0, 1) - 1  # Convert to 0-based
            self.screen.set_cursor(None, row)
        elif final_char == "J":  # ED - Erase in Display
            mode = self._get_param(0, 0)
            self.screen.clear_screen(mode)
        elif final_char == "K":  # EL - Erase in Line
            mode = self._get_param(0, 0)
            self.screen.clear_line(mode)
        elif final_char == "L":  # IL - Insert Lines
            count = self._get_param(0, 1)
            self.screen.insert_lines(count)
        elif final_char == "M":  # DL - Delete Lines
            count = self._get_param(0, 1)
            self.screen.delete_lines(count)
        elif final_char == "@":  # ICH - Insert Characters
            count = self._get_param(0, 1)
            self.screen.insert_characters(count)
        elif final_char == "P":  # DCH - Delete Characters
            count = self._get_param(0, 1)
            self.screen.delete_characters(count)
        elif final_char == "S":  # SU - Scroll Up
            count = self._get_param(0, 1)
            self.screen.scroll_up(count)
        elif final_char == "T":  # SD - Scroll Down
            count = self._get_param(0, 1)
            self.screen.scroll_down(count)
        elif final_char == "r":  # DECSTBM - Set Scroll Region
            top = self._get_param(0, 1) - 1  # Convert to 0-based
            bottom = self._get_param(1, self.screen.height) - 1  # Convert to 0-based
            self.screen.set_scroll_region(top, bottom)
        elif final_char == "m":  # SGR - Select Graphic Rendition
            self._csi_dispatch_sgr()
        elif final_char == "h":  # SM - Set Mode
            self._csi_dispatch_sm_rm(True)
        elif final_char == "l":  # RM - Reset Mode
            self._csi_dispatch_sm_rm(False)

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
        pass

    def _csi_dispatch_sm_rm(self, set_mode: bool) -> None:
        """Handles SM (Set Mode) and RM (Reset Mode) sequences."""
        pass

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
        pass

    # --- OSC, DCS, and other String-based Sequence Handlers ---

    def _enter_string_mode(self, next_state: str, exit_handler: Callable) -> None:
        """Generic handler for entering a string-based escape mode."""
        pass

    def _exit_string_mode(self) -> None:
        """Generic handler for exiting a string-based escape mode."""
        pass

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
        pass

    def _handle_dcs_dispatch(self) -> None:
        """
        Dispatches a DCS (Device Control String).

        Primarily used for passthrough (`tmux;...`) sequences or for things
        like Sixel graphics if support is enabled.
        """
        pass

    def _handle_apc_dispatch(self) -> None:
        """Dispatches an APC (Application Program Command) string."""
        pass

    def _handle_rename_dispatch(self) -> None:
        """Handles the `screen` program's window renaming sequence."""
        pass

    # --- Functions That Will Be Re-implemented Differently ---

    def _reply(self, response: bytes) -> None:
        """
        REIMPLEMENTED: In Python, this should emit an event, not write to a fd.

        In tmux's C code, this function writes a response back to the pty, for
        example in response to a DSR (Device Status Report) query. In a Textual
        app, the parser should not have direct access to the pty output.

        Instead, this method should be replaced with `self.post_message(...)`,
        sending a custom event that the parent widget can listen for and handle
        by writing the data to the process.
        """
        pass

    def _start_timer(self) -> None:
        """
        REIMPLEMENTED: In Python, this should use `asyncio` or Textual's timers.

        This function in C starts a timeout to prevent the parser from getting
        stuck waiting for a sequence terminator. In a Textual application, this
        should be implemented using `self.set_timer()` to call a reset method
        if the sequence doesn't complete in time.
        """
        pass

    def _reset_terminal(self) -> None:
        """Reset terminal to initial state."""
        self.screen.clear_screen(2)
        self.screen.set_cursor(0, 0)
        self.screen.current_style = Style()

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
        if self.screen.current_style is None:
            self.screen.current_style = Style()

        it = iter(self.parsed_params)
        while True:
            try:
                param = next(it)
            except StopIteration:
                break

            if param == 0:
                # Reset all attributes
                self.screen.current_style = Style()
            elif param == 1:
                self.screen.current_style += Style(bold=True)
            elif param == 2:
                self.screen.current_style += Style(dim=True)
            elif param == 3:
                self.screen.current_style += Style(italic=True)
            elif param == 4:
                self.screen.current_style += Style(underline=True)
            elif param == 5:
                self.screen.current_style += Style(blink=True)
            elif param == 7:
                self.screen.current_style += Style(reverse=True)
            elif param == 8:
                self.screen.current_style += Style(conceal=True)
            elif param == 9:
                self.screen.current_style += Style(strike=True)
            elif param == 21:  # Not bold/double underline
                self.screen.current_style += Style(bold=False)
            elif param == 22:  # Neither bold nor faint
                self.screen.current_style += Style(bold=False, dim=False)
            elif param == 23:  # Not italic
                self.screen.current_style += Style(italic=False)
            elif param == 24:  # Not underlined
                self.screen.current_style += Style(underline=False)
            elif param == 25:  # Not blinking
                self.screen.current_style += Style(blink=False)
            elif param == 27:  # Not reversed
                self.screen.current_style += Style(reverse=False)
            elif param == 28:  # Not hidden
                self.screen.current_style += Style(conceal=False)
            elif param == 29:  # Not strikethrough
                self.screen.current_style += Style(strike=False)
            elif 30 <= param <= 37:
                # Standard 16-color foreground
                self.screen.current_style += Style(color=Color.from_ansi(param - 30))
            elif param == 38:
                # Extended foreground color
                new_color = None
                try:
                    color_type = next(it)
                    if color_type == 5:  # 256-color
                        color_code = next(it)
                        new_color = Color.from_ansi(color_code)
                    elif color_type == 2:  # Truecolor (RGB)
                        r = next(it)
                        g = next(it)
                        b = next(it)
                        new_color = Color.from_rgb(r, g, b)
                except StopIteration:
                    # Malformed sequence, ignore
                    pass
                if new_color is not None:
                    self.screen.current_style += Style(color=new_color)
            elif param == 39:
                # Default foreground color
                self.screen.current_style += Style(color=None)
            elif 40 <= param <= 47:
                # Standard 16-color background
                self.screen.current_style += Style(bgcolor=Color.from_ansi(param - 40))
            elif param == 48:
                # Extended background color
                new_bgcolor = None
                try:
                    color_type = next(it)
                    if color_type == 5:  # 256-color
                        color_code = next(it)
                        new_bgcolor = Color.from_ansi(color_code)
                    elif color_type == 2:  # Truecolor (RGB)
                        r = next(it)
                        g = next(it)
                        b = next(it)
                        new_bgcolor = Color.from_rgb(r, g, b)
                except StopIteration:
                    # Malformed sequence, ignore
                    pass
                if new_bgcolor is not None:
                    self.screen.current_style += Style(bgcolor=new_bgcolor)
            elif param == 49:
                # Default background color
                self.screen.current_style += Style(bgcolor=None)
            elif 90 <= param <= 97:
                # Bright 16-color foreground
                self.screen.current_style += Style(color=Color.from_ansi(param - 90 + 8))
            elif 100 <= param <= 107:
                # Bright 16-color background
                self.screen.current_style += Style(bgcolor=Color.from_ansi(param - 100 + 8))

    def _csi_dispatch_sm_rm(self, set_mode: bool) -> None:
        """Handle SM (Set Mode) and RM (Reset Mode) sequences."""
        # Basic mode handling - expand as needed
        for param in self.parsed_params:
            if param == 7:  # Auto-wrap mode
                self.screen.auto_wrap = set_mode
            elif param == 25:  # Cursor visibility
                self.screen.cursor_visible = set_mode
