import src.html.dom as dom
from src.css import css


PropertyMap = dict[str, css.Value]

class Display:
    Inline = "inline"
    Block = "block"
    Null = "none"

class StyledNode:
    def __init__(self, node: dom.Node, specified_values: PropertyMap, children: list['StyledNode']):
        self.node = node
        self.specified_values = specified_values
        self.children = children

    def __repr__(self) -> str:
        return f"StyledNode(node={self.node}, values={self.specified_values}, children={self.children})"

    def value(self, name: str) -> css.Value | None:
        return self.specified_values.get(name)
    
    def lookup(self, name: str, fallback_name: str, default: css.Length) -> css.Value:
        return self.value(name) or self.value(fallback_name) or default
    
    def display(self) -> Display.__subclasses__:
        value = self.value("display")
        if value:
            if value == "block":
                return Display.Block
            elif value == "none":
                return Display.Null
        return Display.Inline


def style_tree(root: dom.Node, stylesheet: css.Stylesheet) -> StyledNode:
    specified_values: PropertyMap = {}
    root_type: dom.NodeType = root.node_type

    if isinstance(root_type, dom.Element):
        specified_values = _specified_values_func(root_type, stylesheet)
    elif isinstance(root, dom.Text):
        specified_values = {}

    children = [style_tree(child, stylesheet) for child in root.children]

    return StyledNode(root, specified_values, children)

def _specified_values_func(elem: dom.Element, stylesheet: css.Stylesheet) -> PropertyMap:
    values = {}
    rules = _matching_rules(elem, stylesheet)

    rules.sort(key=lambda pair: pair[0])
    for _, rule in rules:
        for declaration in rule.declarations:
            values[declaration.name] = declaration.value

    return values

_MatchedRule = tuple[css.Specificity, css.Rule]

def _matching_rules(elem: dom.Element, stylesheet: css.Stylesheet) -> list[_MatchedRule]:
    return [match for rule in stylesheet.rules if (match := _match_rule(elem, rule))]

def _match_rule(elem: dom.Element, rule: css.Rule) -> _MatchedRule | None:
    for selector in rule.selectors:
        if _matches(elem, selector):
            return (selector.specificity(), rule)
    return None

def _matches(elem: dom.Element, selector: css.Selector) -> bool:
    if isinstance(selector, css.SimpleSelector):
        return _matches_simple_selector(elem, selector)
    return False

def _matches_simple_selector(elem: dom.Element, selector: css.SimpleSelector) -> bool:
    if selector.tag_name and elem.tag_name != selector.tag_name:
        return False
    
    if selector.id and elem.id() != selector.id:
        return False
    
    if any(cls not in elem.classes() for cls in selector.class_name):
        return False
    
    return True