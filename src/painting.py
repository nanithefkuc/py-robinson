import layout
import css


class DisplayCommand:
    """Base class for all Display commands."""
    pass

class SolidColor(DisplayCommand):
    """A display command to paint a solid color in the associated rectangele."""
    def __init__(self, color: css.Color, rect: layout.Rect):
        self.color = color
        self.rect = rect

    def __repr__(self) -> str:
        return f"SolidColor({self.color}, {self.rect})"

# A list of all display commands.
DisplayList = list[DisplayCommand]

class Canvas:
    """
    Class for the area that all the elements will be painted to.
    :param pixels: The colors of each pixel, from left to right, up to down.
    :param width: The width of the canvas.
    :param height: The height of the canvas.
    """
    def __init__(self, pixels: list[css.Color], width: int, height: int):
        self.pixels = pixels
        self.width = width
        self.height = height

    @staticmethod
    def _new(width: int, height: int) -> 'Canvas':
        """Creates a new blank canvas."""
        white = css.Color(255, 255, 255, 255)
        return Canvas([white] * width * height, width, height)
    
    def _paint_item(self, item: DisplayCommand):
        """Sets the color of each pixel in the output image."""
        if isinstance(item, SolidColor):
            x0 = int(self._clamp(item.rect.x, 0.0, float(self.width)))
            y0 = int(self._clamp(item.rect.y, 0.0, float(self.height)))
            x1 = int(self._clamp(item.rect.x + item.rect.width, 0.0, self.width))
            y1 = int(self._clamp(item.rect.x + item.rect.width, 0.0, self.height))

            for y in range(y0, y1):
                for x in range(x0, x1):
                    # mbrubeck: TODO: Alpha compositing with existing pixels
                    # Nani: Nah, I'm lazy.
                    self.pixels[y * self.width + x] = item.color

    def _clamp(self, value: float, min: float, max: float) -> float:
        """Helper function to do value range clamping."""

        # There is probably a library that does this (numpy probably), but 
        # I don't wanna import another library.
        if value < min:
            return min
        elif value > max:
            return max
        else:
            return value


def paint(layout_root: layout.LayoutBox, bounds: layout.Rect) -> Canvas:
    """Paint a tree of LayoutBoxes to an array of pixels."""
    display_list = build_display_list(layout_root)
    canvas = Canvas._new(int(bounds.width), int(bounds.height))
    for item in display_list:
        canvas._paint_item(item)
    return canvas

def build_display_list(layout_root: layout.LayoutBox) -> DisplayList:
    """Populate display list with all the display commands to render all the elements."""
    lst: DisplayList = []
    _render_layout_box(lst, layout_root)
    return lst

def _render_layout_box(lst: DisplayList, layout_box: layout.LayoutBox):
    """Adds all the display commands to render a Box type element."""
    _render_background(lst, layout_box)
    _render_borders(lst, layout_box)
    for child in layout_box.children:
        _render_layout_box(lst, child)

def _render_background(lst: DisplayList, layout_box: layout.LayoutBox):
    """Adds a solid color background to the output image."""
    color = _get_color(layout_box, "background")
    if color:
        lst.append(SolidColor(color, layout_box.dimensions.border_box()))

def _render_borders(lst: DisplayList, layout_box: layout.LayoutBox):
    """Renders the borders of the Box type element."""
    color = _get_color(layout_box, "border-color")
    if color is None:
        return -1

    d = layout_box.dimensions
    border_box = d.border_box()

    # Left border
    lst.append(SolidColor(color, layout.Rect(
        border_box.x,
        border_box.y,
        d.border.left,
        border_box.height,
    )))

    # Right border
    lst.append(SolidColor(color, layout.Rect(
        border_box.x + border_box.width - d.border.right,
        border_box.y,
        d.border.right,
        border_box.height
    )))

    # Top border
    lst.append(SolidColor(color, layout.Rect(
        border_box.x,
        border_box.y,
        border_box.width,
        d.border.top
    )))

    # Bottom border
    lst.append(SolidColor(color, layout.Rect(
        border_box.x,
        border_box.y + border_box.height - d.border.bottom,
        border_box.width,
        d.border.bottom
    )))

def _get_color(layout_box: layout.LayoutBox, name: str) -> css.Color | None:
    """Return the specified color for CSS Property `name`, or None if no color was specified."""
    if isinstance(layout_box.box_type, (layout.BlockNode, layout.InlineNode)):
        value = layout_box.box_type.styled_node.value(name)
        if isinstance(value, css.Value):
            return value.color
    return None
        