import dom
import re


def parse(source: str) -> dom.Node:
    "Parses HTML source string into DOM tree."
    nodes = Parser(source, 0)._parse_nodes()

    if len(nodes) == 1:
        return nodes[0]
    else:
        return dom.elem("html", {}, nodes)


class Parser:
    """
    Parser class to turn source code into DOM Tree.
    :param source: HTML source code.
    :param pos: Parser cursor start position.
    """
    def __init__(self, source: str, pos: int = 0):
        self.source = source
        self.pos = pos

    def _parse_nodes(self) -> list[dom.Node]:
        """Parse a sequence of sibling nodes."""
        nodes = []
        while True:
            self._consume_whitespace()
            if self._eof() or self._starts_with("</"):
                break
            node = self._parse_node()
            nodes.append(node)
        return nodes

    def _parse_node(self) -> dom.Node:
        """Parse a single node."""
        if self._starts_with("<!DOCTYPE", case_insensitive=True):
            return self._parse_doctype()
        elif self._starts_with("<!--"):
            return self._parse_comment()
        elif self._starts_with("<"):
            return self._parse_element()
        else:
            return self._parse_text()

    def _parse_doctype(self) -> dom.Node:
        """Parse a HTML `DOCTYPE` tag."""
        # Expect opening
        self._expect("<!DOCTYPE", case_insensitive=True)
        
        # Declaration content
        doctype = self._consume_while(lambda c: c != ">")

        # Expect closing
        self._expect(">")

        return dom.doctype(doctype.strip())

    def _parse_comment(self) -> dom.Node:
        """Parse a HTML comment."""
        # Opening tag
        self._expect("<!--")

        # Contents
        comment = self._consume_while(lambda c: not self._starts_with("-->"))

        # Closing comment tag
        self._expect("-->")

        return dom.comment(comment)

    def _parse_element(self) -> dom.Node:
        """Parse a HTML element (supports self-closing tags)."""
        # Opening tag
        self._expect("<")
        tag_name = self._parse_name()
        attrs = self._parse_attributes()

        # Check if this is a self-closing tag
        if self._starts_with("/>"):
            self._expect("/>")
            element = dom.elem(tag_name, attrs, [])
            return element
        
        self._expect(">")

        # Check if this is a self-closing tag without the '/' according to HTML5 standard
        if tag_name.lower() in ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr']:
            element = dom.elem(tag_name, attrs, [])
            return element

        # Contents
        children = self._parse_nodes()

        # Closing tag.
        self._expect("</")
        self._expect(tag_name)
        self._expect(">")

        element = dom.elem(tag_name, attrs, children)
        return element
    
    def _parse_name(self) -> str:
        """Parse the name of the tag or attribute."""
        name = self._consume_while(lambda c: re.match(r'[a-zA-Z0-9\-]', c))
        return name

    def _parse_attributes(self) -> dom.AttrMap:
        """Parse a list of `name=\"value\"` pairs, seperated by whitespace."""
        attributes = {}
        while True:
            self._consume_whitespace()
            if self._starts_with("/>") or self._starts_with(">"):
                break
            name, value = self._parse_attr()
            attributes[name] = value
        return attributes

    def _parse_attr(self) -> tuple[str, str]:
        """Parse a single `name=\"value\"` pair."""
        name = self._parse_name()
        self._expect("=")
        value = self._parse_attr_value()
        return (name, value)

    def _parse_attr_value(self) -> str:
        """Parse a quoted value (`\'\'` or `\"\"`)."""
        open_quote = self._consume_char()
        assert open_quote in ('"', "'")
        value = self._consume_while(lambda c: c != open_quote)
        close_quote = self._consume_char()
        assert open_quote == close_quote
        return value

    def _parse_text(self) -> dom.Node:
        """Parse HTML text."""
        text = self._consume_while(lambda c: c != '<')
        return dom.text(text)

    def _consume_whitespace(self):
        """Skips over whitespace."""
        self._consume_while(str.isspace)

    def _consume_while(self, test) -> str:
        """Advances the cursor until `test` returns `False`."""
        result = []
        while not self._eof() and test(self._next_char()):
            result.append(self._consume_char())
        return ''.join(result)

    def _consume_char(self) -> str:
        """Returns the current character and advances the cursor to next character."""
        c = self._next_char()
        self.pos += len(c)
        return c

    def _next_char(self) -> str:
        """Returns the next character without advancing the cursor."""
        if self._eof():
            return ''
        return self.source[self.pos]

    def _starts_with(self, s: str, case_insensitive: bool = False) -> bool:
        """
        Boolean check if `s` is at the current cursor position.
        :param case_insensitive: Toggles case-insensitive check, default is `False`.
        """
        if case_insensitive:
            return self.source[self.pos:].lower().startswith(s.lower())
        else:
            return self.source[self.pos:].startswith(s)

    # If the exact string `s` is found at the current position, consume it.
    # Otherwise, raise an error.
    def _expect(self, s: str, case_insensitive: bool = False):
        """
        If exact string `s` is found at current position, consume it.
        :param case_insensitive: Toggles case-insensitive check, default is `False`.
        """
        if self._starts_with(s, case_insensitive):
            self.pos += len(s)
        else:
            raise ValueError(f"Expected {s!r} at byte {self.pos} but it was not found")

    # Return true if all input is consumed.
    def _eof(self) -> bool:
        """Returns `True` if reached End of File."""
        return self.pos >= len(self.source)
