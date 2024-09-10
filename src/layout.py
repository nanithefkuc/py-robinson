import style
from css.utils import color, units
from css import css
from functools import reduce
import collections.abc as c


class Rect:
    def __init__(self, x: float = 0.0, y: float = 0.0, width: float = 0.0, height: float = 0.0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __repr__(self) -> str:
        return f"Rect({self.x}, {self.y}, {self.width}, {self.height})"

    def expanded_by(self, edge: 'EdgeSizes') -> 'Rect':
        x = self.x - edge.left
        y = self.y - edge.top
        width = self.width + edge.left + edge.right
        height = self.height + edge.top + edge.bottom
        return Rect(x, y, width, height)
    

class Dimensions:
    def __init__(self, content: Rect, padding: 'EdgeSizes', border: 'EdgeSizes', margin: 'EdgeSizes'):
        self.content = content
        self.padding = padding
        self.border = border
        self.margin = margin

    def __repr__(self) -> str:
        return f"Dimensions(content={self.content}, padding={self.padding}, border={self.border}, margin={self.margin})"

    def padding_box(self) -> Rect:
        return self.content.expanded_by(self.padding)
    
    def border_box(self) -> Rect:
        return self.padding_box().expanded_by(self.border)
    
    def margin_box(self) -> Rect:
        return self.border_box().expanded_by(self.margin)

    @classmethod
    def _default(cls) -> 'Dimensions':
        return Dimensions(Rect(), EdgeSizes(), EdgeSizes(), EdgeSizes())


class EdgeSizes:
    def __init__(self, left: float = 0.0, right: float = 0.0, top: float = 0.0, bottom: float = 0.0):
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom

    def __repr__(self) -> str:
        return f"EdgeSize({self.left}, {self.right}, {self.top}, {self.bottom})"


class BoxType:
    pass


class BlockNode(BoxType):
    def __init__(self, styled_node: style.StyledNode):
        self.styled_node = styled_node

    def __repr__(self) -> str:
        return f"BlockNode({self.styled_node})"


class InlineNode(BoxType):
    def __init__(self, styled_node: style.StyledNode):
        self.styled_node = styled_node

    def __repr__(self) -> str:
        return f"InlineNode({self.styled_node})"


class AnonymousBlock(BoxType):
    def __repr__(self) -> str:
        return f"AnonymousBlock()"


class LayoutBox:
    def __init__(self, dimensions: Dimensions, box_type: BoxType, children: list['LayoutBox']):
        self.dimensions = dimensions
        self.box_type = box_type
        self.children = children

    def __repr__(self) -> str:
        return f"Layout(dimensions={self.dimensions}, box_type={self.box_type}, children={self.children})"

    @staticmethod
    def _new(box_type: BoxType.__subclasses__) -> 'LayoutBox':
        return LayoutBox(Dimensions._default(), box_type, [])
    
    def _get_style_node(self) -> style.StyledNode:
        if isinstance(self.box_type, BlockNode) or isinstance(self.box_type, InlineNode):
            return self.box_type.styled_node
        else:
            raise ValueError("Anonymous block box has no style node!")

    def _layout(self, containing_block: Dimensions):
        if isinstance(self.box_type, BlockNode):
            self._layout_block(containing_block)
        elif isinstance(self.box_type, InlineNode) or isinstance(self.box_type, AnonymousBlock):
            # TODO
            pass

    def _layout_block(self, containing_block: Dimensions):
        self._calculate_block_width(containing_block)
        self._calculate_block_position(containing_block)
        self._layout_block_children()
        self._calculate_block_height()

    def _calculate_block_width(self, containing_block: Dimensions):
        style = self._get_style_node()

        auto = css.Keyword("auto")
        width = style.value("width") or auto

        zero = css.Length(0.0)

        margin_left = style.lookup("margin-left", "margin", zero)
        margin_right = style.lookup("margin-right", "margin", zero)

        border_left = style.lookup("border-left-width", "border-width", zero)
        border_right = style.lookup("border-right-width", "border-width", zero)

        padding_left = style.lookup("padding-left", "padding", zero)
        padding_right = style.lookup("padding-right", "padding", zero)

        total = _sum([
            margin_left.to_px(),
            margin_right.to_px(),
            border_left.to_px(),
            border_right.to_px(),
            padding_left.to_px(),
            padding_right.to_px(),
            width.to_px()
        ])

        if width != auto and total > containing_block.content.width:
            if margin_left == auto:
                margin_left = css.Length(0.0)
            if margin_right == auto:
                margin_right = css.Length(0.0)

        underflow = containing_block.content.width - total

        match (width == auto, margin_left == auto, margin_right == auto):
            case (False, False, False):
                margin_right = css.Length(margin_right.to_px() + underflow)
            case (False, False, True):
                margin_right = css.Length(underflow)
            case (False, True, False):
                margin_left = css.Length(underflow)
            case (False, True, True):
                margin_left = css.Length(underflow / 2.0)
                margin_right = css.Length(underflow / 2.0)
            case (True, _, _):
                if margin_left == auto:
                    margin_left = css.Length(0.0)
                if margin_right == auto:
                    margin_right = css.Length(0.0)

                if underflow >= 0.0:
                    width = css.Length(underflow)
                else:
                    width = css.Length(0.0)
                    margin_right = css.Length(margin_right.to_px() + underflow)

        d = self.dimensions
        d.content.width = width.to_px()

        d.padding.left = padding_left.to_px()
        d.padding.right = padding_right.to_px()

        d.border.left = border_left.to_px()
        d.border.right = border_right.to_px()

        d.margin.left = margin_left.to_px()
        d.margin.right = margin_right.to_px()

    def _calculate_block_position(self, containing_block: Dimensions):
        styled_node = self._get_style_node()
        d = self.dimensions

        zero = css.Length(0.0)

        d.margin.top = styled_node.lookup("margin-top", "margin", zero).to_px()
        d.margin.bottom = styled_node.lookup("margin-bottom", "margin", zero).to_px()

        d.border.top = styled_node.lookup("border-top", "border", zero).to_px()
        d.border.bottom = styled_node.lookup("border-bottom", "border", zero).to_px()

        d.padding.top = styled_node.lookup("padding-top", "padding", zero).to_px()
        d.padding.bottom = styled_node.lookup("padding-bottom", "padding", zero).to_px()

        d.content.x = containing_block.content.x + d.margin.left + d.border.left + d.padding.left
        d.content.y = containing_block.content.y + d.margin.top + d.border.top + d.padding.top

    def _calculate_block_height(self):
        style_value = self._get_style_node().value("height")

        if style_value is not None and isinstance(style_value.length[1], css.Px):
            self.dimensions.content.height = style_value.to_px()

    def _layout_block_children(self):
        for child in self.children:
            child._layout(self.dimensions)
            self.dimensions.content.height += child.dimensions.margin_box().height

    def _get_inline_container(self) -> 'LayoutBox':
        if isinstance(self.box_type, InlineNode) or isinstance(self.box_type, AnonymousBlock):
            return self
        elif isinstance(self.box_type, BlockNode):
            if self.children and isinstance(self.children[-1].box_type, AnonymousBlock):
                return self.children[-1]
            else:
                new_child = LayoutBox._new(AnonymousBlock)
                self.children.append(new_child)
                return self.children[-1]
        else:
            raise ValueError("Unknown BoxType Instance: {self.box_type}")
            

def layout_tree(node: style.StyledNode, containing_block: Dimensions) -> LayoutBox:
    containing_block.content.y = 0.0

    root_box = _build_layout_tree(node)
    root_box._layout(containing_block)
    return root_box

def _build_layout_tree(style_node: style.StyledNode) -> LayoutBox:
    match style_node.display():
        case style.Display.Block:
            root = LayoutBox._new(BlockNode(style_node))
        case style.Display.Inline:
            root = LayoutBox._new(InlineNode(style_node))
        case style.Display.Null:
            raise ValueError(f"Root node has display: None.")
        
    for child in style_node.children:
        match child.display():
            case style.Display.Block:
                root.children.append(_build_layout_tree(child))
            case style.Display.Inline:
                root._get_inline_container().children.append(_build_layout_tree(child))
            case style.Display.Null:
                pass

    return root

def _sum(iterable: c.Iterable):
    return reduce(lambda a, b: a + b, iterable, 0.0)