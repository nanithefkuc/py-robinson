import argparse
from PIL.Image import new

import css
import dom
import html
import layout
import style
import painting

def _read_source(filename: str) -> str:
    """Helper function to read in the files and store as a variable."""
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()

if __name__ == "__main__":
    # Parse command-line options.
    parser = argparse.ArgumentParser(description='Parses and displays HTML code as a picture/PDF')
    parser.add_argument("-d", "--document", help="HTML document", default="src/examples/test.html")
    parser.add_argument("-c", "--css", help="CSS stylesheet", default="src/examples/test.css")
    parser.add_argument("-o", "--output", help="Output file", default="output.png")
    parser.add_argument("-f", "--format", help="Output file format", choices=["png", "pdf"], default="png")

    args = parser.parse_args()

    # Choose a format
    if args.format == "png":
        png = True
    elif args.format == "pdf":
        png = False
    else:
        raise ValueError(f"Unknown output format: {args.format}")
    
    # Read input files
    html_source = _read_source(args.document)
    css_source = _read_source(args.css)

    # Since we don't have an actual window, hard-code the "viewport" size.
    viewport = layout.Dimensions._default()
    viewport.content.width = 800.0
    viewport.content.height = 600.0

    # Parsing and rendering
    root_node = html.parse(html_source)
    stylesheet = css.parse(css_source)
    style_root = style.style_tree(root_node, stylesheet)
    layout_root = layout.layout_tree(style_root, viewport)

    # Create output file if it doesn't exist.
    if args.output:
        filename = args.output
    else:
        filename = "output.png" if png else "output.pdf"
    
    # Draw the image to the file.
    if png:
        canvas = painting.paint(layout_root, viewport.content)
        w, h = canvas.width, canvas.height

        img = new('RGBA', (w, h))

        for y in range(h):
            for x in range(w):
                color = canvas.pixels[y * w + x]
                img.putpixel((x, y), (color.r, color.g, color.b, color.a))

        img.save(filename, format='PNG')
        print(f"Saved output as {filename}")