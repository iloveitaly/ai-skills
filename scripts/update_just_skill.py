# /// script
# dependencies = [
#   "requests",
#   "mistletoe",
# ]
# ///

import requests
from pathlib import Path
import mistletoe
from mistletoe.ast_renderer import ASTRenderer

README_URL = 'https://raw.githubusercontent.com/casey/just/refs/heads/master/README.md'
SKILL_FILE = Path(__file__).parent.parent / "skills" / "justfile" / "SKILL.md"

EXCLUDE_SECTIONS = {'installation', 'backwards compatibility', 'editor support', 'changelog', 'miscellanea', 'contributing', 'frequently asked questions', 'further ramblings', 'packages'}
INCLUDE_SECTIONS = {'quick start', 'examples', 'features', 'the default recipe'}

def get_heading_text(node):
    """Extracts plain text from a mistletoe heading node."""
    text = ""
    for child in node.children:
        if hasattr(child, 'content'):
            text += child.content
        elif hasattr(child, 'children'):
            text += get_heading_text(child)
    return text.lower().strip()

def filter_markdown(markdown_str):
    doc = mistletoe.Document(markdown_str)
    new_children = []
    keeping = True

    for node in doc.children:
        if isinstance(node, mistletoe.block_token.Heading):
            text = get_heading_text(node)
            
            # Check for explicit exclusion
            if any(text == s or text.startswith(s + ' ') for s in EXCLUDE_SECTIONS):
                keeping = False
            # Check for explicit inclusion
            elif any(text == s or text.startswith(s + ' ') for s in INCLUDE_SECTIONS):
                keeping = True
        
        if keeping:
            # Filter out the Table of Contents and specific badges
            if isinstance(node, mistletoe.block_token.HTMLBlock):
                content = node.content.lower()
                if "table of contents" in content or "img.shields.io" in content:
                    continue
            new_children.append(node)

    # Re-render the filtered AST back to Markdown
    # Mistletoe doesn't have a built-in "Markdown" renderer, so we use a simple reconstruction
    from mistletoe.markdown_renderer import MarkdownRenderer
    with MarkdownRenderer() as renderer:
        return renderer.render(mistletoe.Document(new_children))

def main():
    print("Fetching README...")
    resp = requests.get(README_URL)
    resp.raise_for_status()
    
    print("Processing AST...")
    # Using the filtered logic
    new_content = filter_markdown(resp.text)

    print(f"Reading {SKILL_FILE.name}...")
    if not SKILL_FILE.exists():
        SKILL_FILE.parent.mkdir(parents=True, exist_ok=True)
        SKILL_FILE.write_text("It fully documents the Justfile syntax and system.\n\n---")

    skill_text = SKILL_FILE.read_text(encoding="utf-8")
    MARKER = 'It fully documents the Justfile syntax and system.\n\n---'
    
    if MARKER in skill_text:
        header = skill_text.split(MARKER)[0] + MARKER
    else:
        header = skill_text + "\n\n---"

    final_output = f"{header}\n\n{new_content}"
    
    SKILL_FILE.write_text(final_output, encoding="utf-8")
    print("Done! Justfile documentation updated.")

if __name__ == "__main__":
    main()