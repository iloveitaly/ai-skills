# /// script
# dependencies = [
#   "requests",
#   "markdown-it-py",
#   "mdformat",
# ]
# ///

import os
import requests
from markdown_it import MarkdownIt
from pathlib import Path

README_URL = 'https://raw.githubusercontent.com/casey/just/refs/heads/master/README.md'
# Adjusting path to match your logic: ../skills/justfile/SKILL.md
SKILL_FILE = Path(__file__).parent.parent / "skills" / "justfile" / "SKILL.md"

EXCLUDE_SECTIONS = [
    'installation', 'backwards compatibility', 'editor support', 
    'changelog', 'miscellanea', 'contributing', 
    'frequently asked questions', 'further ramblings', 'packages'
]

INCLUDE_SECTIONS = [
    'quick start', 'examples', 'features', 'the default recipe'
]

def filter_markdown(content):
    md = MarkdownIt("gfm-like")
    tokens = md.parse(content)
    
    new_tokens = []
    keeping = True
    
    # Iterate through tokens to filter sections
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # Detect Headings
        if token.type == "heading_open":
            # The actual text is usually in the next 'inline' token
            inline_token = tokens[i+1]
            text = inline_token.content.lower().strip()
            
            if any(text == s or text.startswith(s + ' ') for s in EXCLUDE_SECTIONS):
                keeping = False
            elif any(text == s or text.startswith(s + ' ') for s in INCLUDE_SECTIONS):
                keeping = True
        
        # Filter HTML (Table of Contents / Shields)
        if token.type == "html_block":
            if "Table of Contents" in token.content or "img.shields.io" in token.content:
                i += 1
                continue

        if keeping:
            new_tokens.append(token)
        i += 1
        
    # Simple reconstruction (for a more advanced rebuild, use mdformat)
    # Since we are filtering blocks, we can just extract the source map or use a renderer
    return md.renderer.render(new_tokens, md.options, {})

def main():
    print("Fetching README...")
    resp = requests.get(README_URL)
    resp.raise_for_status()
    markdown_text = resp.text

    print("Processing...")
    # Note: markdown-it-py renders to HTML by default. 
    # For a direct MD-to-MD filter like your JS script, we use the logic below:
    lines = markdown_text.splitlines()
    filtered_lines = []
    keeping = True
    
    # Simpler line-based approach for Markdown-to-Markdown preservation
    for line in lines:
        if line.startswith('#'):
            title = line.lstrip('#').strip().lower()
            if any(title == s or title.startswith(s + ' ') for s in EXCLUDE_SECTIONS):
                keeping = False
            elif any(title == s or title.startswith(s + ' ') for s in INCLUDE_SECTIONS):
                keeping = True
        
        if keeping:
            # Skip TOC and Shields
            if "Table of Contents" in line or "img.shields.io" in line:
                continue
            filtered_lines.append(line)

    new_content = "\n".join(filtered_lines)

    print(f"Reading {SKILL_FILE}...")
    skill_path = Path(SKILL_FILE)
    skill_text = skill_path.read_text(encoding="utf-8")

    MARKER = 'It fully documents the Justfile syntax and system.\n\n---'
    if MARKER in skill_text:
        header = skill_text.split(MARKER)[0] + MARKER
    else:
        print("Marker not found! Appending.")
        header = skill_text + ("\n\n---" if not skill_text.strip().endswith("---") else "")

    final_output = f"{header}\n\n{new_content}"
    
    print("Writing...")
    skill_path.write_text(final_output, encoding="utf-8")
    print("Done.")

if __name__ == "__main__":
    main()