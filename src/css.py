import re

class Stylesheet:
    """
    Class type for top-level style sheet.
    :param rules: List of `Rule`.
    """
    def __init__(self, rules: list['Rule']):
        self.rules = rules

    def __repr__(self) -> str:
        return f"Stylesheet({self.rules})"

class Rule:
    """
    Class type for a CSS Rule.
    :param selectors: List of `Selector`.
    :param declarations: List of `Declaration`.
    """
    def __init__(self, selectors: list['Selector'], declarations: list['Declaration']):
        self.selectors = selectors
        self.declarations = declarations

    def __repr__(self) -> str:
        return f"Rule{self.selectors, self.declarations}"


Specificity = tuple[int, int, int] # CSS Specificity type
class Selector:
    """
    Class type for a CSS Selector.
    :param simple_selector: `SimpleSelector` type.
    """
    def __init__(self, simple_selector: 'SimpleSelector'):
        self.simple_selector = simple_selector

    def __repr__(self) -> str:
        return f"Selector({self.simple_selector.id, self.simple_selector.tag_name, self.simple_selector.class_name})"

    def specificity(self) -> Specificity:
        """Returns a tuple of the selector's specificity."""
        a = 1 if self.simple_selector.id else 0
        b = len(self.simple_selector.class_name)
        c = 1 if self.simple_selector.tag_name else 0
        return (a, b, c)
    
class SimpleSelector:
    """
    Class type for a simple CSS Selector (i.e. `#`, `.`, `*`).
    :param tag_name: Element's tag name string.
    :param id: Element's id string.
    :param class_name: Element's class name string.
    """
    def __init__(self, tag_name: str | None, id: str | None, class_name: list[str]):
        self.tag_name = tag_name
        self.id = id
        self.class_name = class_name

class Declaration:
    """
    Class type for a CSS Declaration.
    :param name: The `name` of the `name="value"` pair.
    :param value: The `value` of the `name="value"` pair.
    """
    def __init__(self, name: str, value: 'Value'):
        self.name = name
        self.value = value

    def __repr__(self) -> str:
        return f"Declaration({self.name, self.value})"
    
class Unit:
    """Base class for CSS units."""
    pass

class Px(Unit):
    """The Pixel unit class."""
    def __init__(self):
        super().__init__()
    
    def __repr__(self) -> str:
        return "Px"

class Color:
    """The Color class."""
    def __init__(self, r: int = 0, g: int = 0, b: int = 0, a: int = 0):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def __repr__(self) -> str:
        return "Color(r={self.r}, g={self.g}, b={self.g}, a={self.a})"

class Value:
    """Class that holds all different value types."""

    # Honestly should refactor this to be more explicit with the types and shit.
    def __init__(self, *, keyword: str | None = "", length: tuple[float, Unit] = (0.0, Px()), color: Color = Color()):
        self.keyword = keyword
        self.length = length
        self.color = color

    def to_px(self) -> float:
        if self.length:
            return self.length[0]
        else:
            return 0.0

def parse(source: str) -> Stylesheet:
    """Parses the CSS source, returns `Stylesheet` of `Rules`."""
    parser = Parser(source, 0)
    return Stylesheet(parser._parse_rules())


class Parser:
    """
    CSS Parser.
    :param source: CSS stylesheet source.
    :param pos: Parser cursor start position.
    """
    def __init__(self, source: str, pos: int = 0):
        self.pos = pos
        self.source = source

    def _parse_rules(self) -> list[Rule]:
        """Parses a list of `Rule`."""
        rules = []
        while not self._eof():
            self._consume_whitespace()
            if self._eof():
                break
            rules.append(self._parse_rule())
        return rules

    def _parse_rule(self) -> Rule:
        """Parses a `Rule`."""
        selectors = self._parse_selectors()
        declarations = self._parse_declarations()
        return Rule(selectors, declarations)

    def _parse_selectors(self) -> list[Selector]:
        """Parses a list of `Selector`."""
        selectors = []
        while True:
            selectors.append(Selector(self._parse_simple_selector()))
            self._consume_whitespace()
            next_char = self._next_char()
            if next_char == ',':
                self._consume_char()
                self._consume_whitespace()
            elif next_char == '{':
                break
            else:
                raise ValueError(f"Unexpected character {next_char} in selector list")
        selectors.sort(key=lambda s: s.specificity(), reverse=True)
        return selectors

    def _parse_simple_selector(self) -> SimpleSelector:
        """Parses a `Selector`."""
        tag_name = None
        id = None
        class_name = []
        while not self._eof():
            next_char = self._next_char()
            if next_char == '#':
                self._consume_char()
                id = self._parse_identifier()
            elif next_char == '.':
                self._consume_char()
                class_name.append(self._parse_identifier())
            elif next_char == '*':
                self._consume_char()
            elif _valid_identifier_char(next_char):
                tag_name = self._parse_identifier()
            else:
                break
        return SimpleSelector(tag_name, id, class_name)

    def _parse_declarations(self) -> list[Declaration]:
        """Parses a list of `Declaration`."""
        self._expect_char('{')
        declarations = []
        while True:
            self._consume_whitespace()
            if self._next_char() == '}':
                self._consume_char()
                break
            declarations.append(self._parse_declaration())
        return declarations

    def _parse_declaration(self) -> Declaration:
        """Parses a `Declaration`."""
        name = self._parse_identifier()
        self._consume_whitespace()
        self._expect_char(':')
        self._consume_whitespace()
        value = self._parse_value()
        self._consume_whitespace()
        self._expect_char(';')
        return Declaration(name, value)

    def _parse_value(self) -> Value:
        """Parses some values."""
        next_char = self._next_char()
        if next_char.isdigit() or next_char == '.':
            return self._parse_length()
        elif next_char == '#':
            return self._parse_color()
        else:
            return Value(keyword=self._parse_identifier())

    def _parse_length(self) -> Value:
        """Parses a length value."""
        length = self._parse_float()
        unit_str = self._parse_unit()

        return Value(length=(length, unit_str))

    def _parse_float(self):
        """Parses float numbers."""
        return float(self._consume_while(lambda c: c.isdigit() or c == '.'))
    
    def _parse_unit(self) -> Unit:
        """Parses CSS length units. Currently only supports `px`."""
        if self._parse_identifier().lower() == "px":
            return Px()
        else:
            raise SyntaxError("Unrecognized unit")

    def _parse_color(self) -> Value:
        """Parses a color from a hex string."""
        self._expect_char('#')
        return Value(color=Color(
            r=self._parse_hex_pair(),
            g=self._parse_hex_pair(),
            b=self._parse_hex_pair(),
            a=255
        ))

    def _parse_hex_pair(self) -> int:
        """Parses color values 2 Hexadecimal values at a time."""
        s = self.source[self.pos:self.pos + 2]
        self.pos += 2
        return int(s, 16)

    def _parse_identifier(self) -> str:
        """Parses identifiers."""
        return self._consume_while(_valid_identifier_char)

    def _consume_whitespace(self) -> None:
        """Moves cursor forward while current character is whitespace."""
        self._consume_while(str.isspace)

    def _consume_while(self, test) -> str:
        """Moves cursor forward while `test` function returns true."""
        result = []
        while not self._eof() and test(self._next_char()):
            result.append(self._consume_char())
        return ''.join(result)

    def _consume_char(self) -> str:
        """Moves cursor forward one character."""
        c = self.source[self.pos]
        self.pos += 1
        return c

    def _expect_char(self, c) -> None:
        """If exact string `s` is found at current position, consume it."""
        if self._consume_char() != c:
            raise ValueError(f"Expected '{c}' at byte {self.pos} but not found")

    def _next_char(self) -> str:
        """Reads the next character without consuming it."""
        # The comment for this function on github is most likely wrong.

        # Probably needs better error handling, like with rust's .unwrap()
        c = self.source[self.pos + 1]

        if c:
            return c
        else:
            raise ValueError("No character left to read.")

    def _eof(self) -> bool:
        """Returns true if all input is consumed."""
        return self.pos >= len(self.source)

def _valid_identifier_char(c) -> bool:
    # TODO: Include U+00A0 and higher.
    return re.match(r'[a-zA-Z0-9_-]', c) is not None

# Usage example
if __name__ == "__main__":
    css = """
        h1, h2, h3 { margin: auto; color: #cc0000; }
        div.note { margin-bottom: 20px; padding: 10px; }
        #main { width: 100px; }
    """
    print(parse(css))
