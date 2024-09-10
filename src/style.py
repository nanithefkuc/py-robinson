import dom
import css


PropertyMap = dict[str, css.Value]

class Display:
    """Base class for the display types"""
    pass

class DisplayBlock(Display):
    """Type class to display Block elements."""
    def __repr__(self) -> str:
        return "DisplayBlock"

class DisplayInline(Display):
    """Type class to display Inline elements."""
    def __repr__(self) -> str:
        return "DisplayInline"

class DisplayNone(Display):
    """Type class to display no elements."""
    def __repr__(self) -> str:
        return "DisplayNone"

class StyledNode:
    """
    A node with associated style data.
    :param node: A DOM tree node.
    :param specified_values: CSS styles dictionary.
    :param children: List of child nodes to this node.
    """
    def __init__(self, node: dom.Node, specified_values: PropertyMap, children: list['StyledNode']):
        self.node = node
        self.specified_values = specified_values
        self.children = children

    def __repr__(self) -> str:
        return f"StyledNode(node={self.node}, values={self.specified_values}, children={self.children})"

    def value(self, name: str) -> css.Value | None:
        """Return the specified value of a property if it exists, otherwise None."""
        v = self.specified_values.get(name)

        if v:
            return v
        else:
            return None
    
    def lookup(self, name: str, fallback_name: str, default: css.Value) -> css.Value:
        """Return the specified value of property `name`, property `fallback_name`if 
        that doesn't exist, or value `default` if neither does."""
        return self.value(name) or self.value(fallback_name) or default
    
    def display(self) -> Display:
        """The value of the `display` property. Defaults to `Inline`."""
        value = self.value("display")
        if value:
            if value == "block":
                return DisplayBlock()
            elif value == "none":
                return DisplayNone()
        return DisplayInline()


def style_tree(root: dom.Node, stylesheet: css.Stylesheet) -> StyledNode:
    """Apply a stylesheet to an entire DOM tree, returning a StyledNode tree."""

    # Mbrubeck: This finds only the specified values at the moment. Eventually it should be extended
    # to find the computed values too, including inherited values.
    # Nani: I'm lazy
    specified_values: PropertyMap = {}
    root_type: dom.NodeType = root.node_type

    if isinstance(root_type, dom.Element):
        specified_values = _specified_values(root_type, stylesheet)
    elif isinstance(root, dom.Text):
        specified_values = {}

    children = [style_tree(child, stylesheet) for child in root.children]

    return StyledNode(root, specified_values, children)

def _specified_values(elem: dom.Element, stylesheet: css.Stylesheet) -> PropertyMap:
    """Apply styles to a single element, returning the specified style."""

    # Mbrubeck: TODO: Allow multiple UA/author/user stylesheets, and implement the cascade.
    # Nani: Again, I am too lazy to think about this.
    values = {}
    rules = _matching_rules(elem, stylesheet)

    rules.sort(key=lambda pair: pair[0])
    for _, rule in rules:
        for declaration in rule.declarations:
            values[declaration.name] = declaration.value

    return values

# A single CSS Rule and the specificity of its most specific matching selector.
_MatchedRule = tuple[css.Specificity, css.Rule]

def _matching_rules(elem: dom.Element, stylesheet: css.Stylesheet) -> list[_MatchedRule]:
    """Linearly scans all of the rules, returns a list of rules."""
    return [match for rule in stylesheet.rules if (match := _match_rule(elem, rule))]

def _match_rule(elem: dom.Element, rule: css.Rule) -> _MatchedRule | None:
    """If `rule` matches `elem`, return a `_MatchedRule`, else return `None`."""
    for selector in rule.selectors:
        if _matches(elem, selector):
            return (selector.specificity(), rule)
    return None

def _matches(elem: dom.Element, selector: css.Selector) -> bool:
    """Matches selectors."""
    if isinstance(selector, css.SimpleSelector):
        return _matches_simple_selector(elem, selector)
    return False

def _matches_simple_selector(elem: dom.Element, selector: css.SimpleSelector) -> bool:
    """Returns true if matched tag/ID/class, else return False."""
    if selector.tag_name and elem.tag_name != selector.tag_name:
        return False
    
    if selector.id and elem.id() != selector.id:
        return False
    
    if any(cls not in elem.classes() for cls in selector.class_name):
        return False
    
    return True