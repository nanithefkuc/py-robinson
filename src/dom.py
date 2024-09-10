# Type alias for attribute map
AttrMap = dict[str, str]
    

# NodeType class equivalent to Rust's enum
class NodeType:
    """Base class for HTML Node types."""
    pass
    

class DocType(NodeType):
    """
    Node type class for the `<!DOCTYPE>` tag.
    :param doc_type: Doc-type string value, usually `html`.
    """
    def __init__(self, doc_type: str):
        self.doc_type = doc_type

    def __repr__(self):
        return f"DocType({self.doc_type!r})"
        

class Text(NodeType):
    """
    Node type class for text no enclosed in HTML element tags.
    :param text: Text string.
    """
    def __init__(self, text: str):
        self.text = text

    def __repr__(self):
        return f"Text({self.text!r})"


class Element(NodeType):
    """
    Node type class for HTML element tags (i.e. `<p>`).
    :param tag_name: Tag name string. (i.e. 'p' for `<p>`).
    :param attrs: Attribute dictionary
    """
    def __init__(self, tag_name: str, attrs: AttrMap):
        self.tag_name = tag_name
        self.attrs = attrs

    def __repr__(self):
        return f"Element({self.tag_name!r}, {self.attrs!r})"
    
    def id(self) -> str | None:
        """Returns the id of the element."""
        return self.attrs.get("id")

    def classes(self) -> set[str]:
        """Returns a list of classes of the element."""
        classlist = self.attrs.get("class")
        return set(classlist.split()) if classlist else set()


class Comment(NodeType):
    """
    Node type class for HTML comment tags `<!-- -->`.
    :param comment: Comment string.
    """
    def __init__(self, comment: str):
        self.comment = comment

    def __repr__(self):
        return f"Comment({self.comment!r})"


# Node class
class Node:
    """
    Node class extension to NodeType class.
    :param node_type: NodeType subclass instance
    :param children: List of node's child nodes.
    """
    def __init__(self, node_type: NodeType, children: list['Node'] = []):
        self.children = children
        self.node_type = node_type

    def __repr__(self):
        return f"Node({self.node_type!r}, {self.children!r})"


# Constructor function for convenience
def doctype(doc_type: str) -> Node:
    """Returns Node of `DocType` type."""
    return Node(DocType(doc_type))

def text(data: str) -> Node:
    """Returns Node of `Text` type."""
    return Node(Text(data))

def elem(tag_name: str, attrs: AttrMap, children: list[Node]) -> Node:
    """Returns Node of `Element` type."""
    return Node(Element(tag_name, attrs), children)

def comment(comment: str) -> Node:
    """Returns Node of `Comment` type."""
    return Node(Comment(comment))


# Example usage
if __name__ == "__main__":
    node = elem("div", {"id": "main", "class": "container"}, [
        text("Hello World!"),
        elem("span", {"class": "highlight"}, [text("Some highlighted text.")]),
        comment("This is a comment."),
        doctype('HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd"')
    ])
    print(node)
