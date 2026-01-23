# /// script
# dependencies = [
#   "requests",
#   "marko",
# ]
# ///

import requests
from pathlib import Path
from marko import Markdown
from marko.block import Heading, HTMLBlock

README_URL = 'https://raw.githubusercontent.com/casey/just/refs/heads/master/README.md'
SKILL_FILE = Path(__file__).parent.parent / "skills" / "justfile" / "SKILL.md"

# Using sets for O(1) lookups
EXCLUDE = {'installation', 'backwards compatibility', 'editor support', 'changelog', 'miscellanea', 'contributing', 'frequently asked questions', 'further ramblings', 'packages'}
INCLUDE = {'quick start', 'examples', 'features', 'the default recipe'}

def get_text(element):
    """Recursively extract plain text from an element and its children."""
    if hasattr(element, 'children'):
        if isinstance(element.children, str):
            return element.children
        return "".join(get_text(c) for c in element.children)
    return ""

def filter_markdown(text):
    # Initialize the parser
    markdown = Markdown()
    document = markdown.parse(text)
    
    new_children = []
    keeping = True

    for node in document.children:
        if isinstance(node, Heading):
            # Extract plain text from heading (handles links/bold inside titles)
            title = get_text(node).lower().strip()
            
            # Switch 'keeping' state based on heading title
            if any(title == s or title.startswith(s + ' ') for s in EXCLUDE):
                keeping = False
            elif any(title == s or title.startswith(s + ' ') for s in INCLUDE):
                keeping = True
        
        # Filter out HTML badges or Table of Contents
        if isinstance(node, HTMLBlock):
            content = node.body.lower()
            if "table of contents" in content or "img.shields.io" in content:
                continue

        if keeping:
            new_children.append(node)

    # Update the document and render back to Markdown string
    document.children = new_children
    return markdown.render(document)

def main():
    print("Fetching README...")
    resp = requests.get(README_URL)
    resp.raise_for_status()
    
    print("Syncing Justfile Documentation...")
    new_md = filter_markdown(resp.text)

    # File I/O Logic
    MARKER = 'It fully documents the Justfile syntax and system.\n\n---'
    if SKILL_FILE.exists():
        content = SKILL_FILE.read_text(encoding="utf-8")
        header = content.split(MARKER)[0] + MARKER if MARKER in content else content
    else:
        header = f"Just Skill\n\n{MARKER}"

    SKILL_FILE.parent.mkdir(parents=True, exist_ok=True)
    SKILL_FILE.write_text(f"{header}\n\n{new_md}", encoding="utf-8")
    print(f"Successfully updated {SKILL_FILE}")

if __name__ == "__main__":
    main()