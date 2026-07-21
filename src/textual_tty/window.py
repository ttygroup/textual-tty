"""A bare-bones draggable, resizable window for Textual apps.

Replaces the dead textual-window dependency with the few things a terminal
window actually needs: a draggable title bar, a close button, a resize grip,
and focus-brings-to-front. The children post bubbling messages and the window
handles them, so nothing here walks the DOM looking for its ancestors.
"""

from __future__ import annotations

from typing import Literal

from textual import events
from textual.app import ComposeResult
from textual.containers import Container
from textual.geometry import Offset
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

HORIZONTAL = Literal["left", "center", "right"]
VERTICAL = Literal["top", "middle", "bottom"]


class Grabbed(Message):
    """The user pressed on a window chrome widget, starting a drag."""


class Dragged(Message):
    """The user has dragged a window chrome widget `total` cells since grabbing it.

    The total is measured from the grab point in screen coordinates, so applying
    `start_geometry + total` is idempotent — a dropped or repeated event can
    never make the window drift.
    """

    def __init__(self, total: Offset) -> None:
        self.total = total
        super().__init__()


class _Draggable(Static):
    """A static that captures the mouse and reports drags as messages."""

    # Subclasses narrow these so each gets its own handler name on Window.
    Grabbed = Grabbed
    Dragged = Dragged

    def on_mouse_down(self, event: events.MouseDown) -> None:
        if event.button == 1:
            self._grab = event.screen_offset
            self.capture_mouse()
            self.add_class("dragging")
            self.post_message(self.Grabbed())

    def on_mouse_up(self, event: events.MouseUp) -> None:
        self.release_mouse()
        self.remove_class("dragging")

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if self.app.mouse_captured is self:
            self.post_message(self.Dragged(event.screen_offset - self._grab))


class TitleBar(_Draggable):
    """Draggable title bar; dragging moves the window."""

    class Grabbed(Grabbed):
        """The title bar was pressed."""

    class Dragged(Dragged):
        """The title bar was dragged."""


class ResizeGrip(_Draggable):
    """Bottom-right grip; dragging resizes the window."""

    class Grabbed(Grabbed):
        """The grip was pressed."""

    class Dragged(Dragged):
        """The grip was dragged."""

    def __init__(self, **kwargs) -> None:
        super().__init__("◢", **kwargs)


class CloseButton(Static):
    """Window close button."""

    class Pressed(Message):
        """The close button was clicked."""

    def __init__(self, **kwargs) -> None:
        super().__init__("✕", **kwargs)

    def on_click(self) -> None:
        self.post_message(self.Pressed())


class Window(Widget):
    """A simple draggable, resizable window container.

    Structure:
        Window
        ├── #header (Container)      TitleBar + CloseButton
        ├── #content (Container)     user content
        └── #footer (Container)      ResizeGrip

    Mount content by passing children to the constructor, or later through
    `window.content.mount(...)`.
    """

    MIN_WIDTH = 20
    MIN_HEIGHT = 6

    DEFAULT_CSS = """
    Window {
        position: absolute;
        width: 40;
        height: 20;
        /* Solid side bands in the title colour: blank borders show the window
           background, which avoids the ragged half-cell look of line borders. */
        background: $primary;
        border-left: blank;
        border-right: blank;
    }

    Window:focus-within {
        background: $secondary;
    }

    Window > #header {
        height: 1;
        width: 100%;
        background: $primary;
        layout: horizontal;
    }

    Window > #header > TitleBar {
        width: 1fr;
        height: 1;
        text-style: bold;
    }

    Window > #header > CloseButton {
        width: 3;
        height: 1;
        content-align: center middle;
    }

    Window > #header > CloseButton:hover {
        background: $error;
    }

    Window > #content {
        width: 100%;
        height: 1fr;
        background: $surface;
    }

    Window > #footer {
        height: 1;
        width: 100%;
        background: $primary-darken-1;
        layout: horizontal;
    }

    Window > #footer > ResizeGrip {
        dock: right;
        width: 2;
        height: 1;
    }

    Window:focus-within > #header {
        background: $secondary;
    }
    """

    title: reactive[str] = reactive("")

    def __init__(
        self,
        *children: Widget,
        title: str = "",
        show_close: bool = True,
        starting_horizontal: HORIZONTAL = "center",
        starting_vertical: VERTICAL = "middle",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._initial_children = list(children)
        self._show_close = show_close
        self._starting_h = starting_horizontal
        self._starting_v = starting_vertical
        self.set_reactive(Window.title, title)

    def compose(self) -> ComposeResult:
        with Container(id="header"):
            yield TitleBar(self.title, id="titlebar")
            if self._show_close:
                yield CloseButton()
        yield Container(*self._initial_children, id="content")
        with Container(id="footer"):
            yield ResizeGrip()

    def on_mount(self) -> None:
        self.call_after_refresh(self._position_window)

    def _position_window(self) -> None:
        """Apply the starting_horizontal/vertical placement."""
        if self.parent is None:  # closed before the first refresh (instant process exit)
            return
        parent_size = self.parent.size
        my_size = self.size
        h_positions = {
            "left": 0,
            "center": (parent_size.width - my_size.width) // 2,
            "right": parent_size.width - my_size.width,
        }
        v_positions = {
            "top": 0,
            "middle": (parent_size.height - my_size.height) // 2,
            "bottom": parent_size.height - my_size.height,
        }
        self.offset = Offset(h_positions[self._starting_h], v_positions[self._starting_v])

    def watch_title(self, new_title: str) -> None:
        if self.is_mounted:
            self.query_one("#titlebar", TitleBar).update(new_title)

    @property
    def content(self) -> Container:
        """The content area of the window."""
        return self.query_one("#content", Container)

    # --- messages from the chrome children --- #

    def on_title_bar_grabbed(self, message: TitleBar.Grabbed) -> None:
        message.stop()
        self._grab_offset = self.offset

    def on_title_bar_dragged(self, message: TitleBar.Dragged) -> None:
        message.stop()
        self.offset = self._grab_offset + message.total

    def on_resize_grip_grabbed(self, message: ResizeGrip.Grabbed) -> None:
        message.stop()
        # region.size is the same basis styles.width/height set: border in, margin out.
        self._grab_size = self.region.size

    def on_resize_grip_dragged(self, message: ResizeGrip.Dragged) -> None:
        message.stop()
        self.styles.width = max(self.MIN_WIDTH, self._grab_size.width + message.total.x)
        self.styles.height = max(self.MIN_HEIGHT, self._grab_size.height + message.total.y)

    def on_close_button_pressed(self, message: CloseButton.Pressed) -> None:
        message.stop()
        self.remove()

    # --- stacking --- #

    def bring_to_front(self) -> None:
        """Move this window above its siblings."""
        if self.parent is not None:
            self.parent.move_child(self, after=-1)

    def on_focus(self) -> None:
        self.bring_to_front()

    def on_descendant_focus(self, event: events.DescendantFocus) -> None:
        self.bring_to_front()
