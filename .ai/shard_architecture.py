#!/usr/bin/env python3
"""Script to shard architecture.md into multiple files."""

import re
from pathlib import Path

def slugify(text):
    """Convert section title to filename."""
    # Remove number prefix like "1. "
    text = re.sub(r'^\d+\.\s+', '', text)
    # Convert to lowercase and replace spaces with dashes
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text

def shard_document(source_path, dest_folder):
    """Shard a markdown document by level 2 headings."""
    source = Path(source_path)
    dest = Path(dest_folder)
    dest.mkdir(parents=True, exist_ok=True)

    # Read entire document
    content = source.read_text(encoding='utf-8')
    lines = content.split('\n')

    # Find level 1 heading and intro
    level1_heading = ""
    intro_lines = []
    sections = []
    current_section = None
    current_lines = []
    in_code_block = False

    for line in lines:
        # Track code blocks to avoid false section detection
        if line.strip().startswith('```'):
            in_code_block = not in_code_block

        # Check for level 1 heading (only once at start)
        if line.startswith('# ') and not level1_heading:
            level1_heading = line
            continue

        # Check for level 2 heading (but not in code block)
        if line.startswith('## ') and not in_code_block:
            # Save previous section
            if current_section:
                sections.append((current_section, '\n'.join(current_lines)))
            # Start new section
            current_section = line[3:].strip()  # Remove "## "
            current_lines = [line]
        elif current_section:
            # Add to current section
            current_lines.append(line)
        else:
            # Add to intro (before first section)
            intro_lines.append(line)

    # Don't forget last section
    if current_section:
        sections.append((current_section, '\n'.join(current_lines)))

    # Create index.md
    index_content = [level1_heading, '']
    index_content.extend(intro_lines)
    index_content.extend(['', '## Sections', ''])

    section_files = []

    for title, section_content in sections:
        # Generate filename
        filename = slugify(title) + '.md'
        section_files.append((filename, title))

        # Adjust heading levels (## -> #, ### -> ##, etc.)
        adjusted_lines = []
        for line in section_content.split('\n'):
            if line.startswith('######'):
                adjusted_lines.append(line[1:])  # Remove one #
            elif line.startswith('#####'):
                adjusted_lines.append(line[1:])
            elif line.startswith('####'):
                adjusted_lines.append(line[1:])
            elif line.startswith('###'):
                adjusted_lines.append(line[1:])
            elif line.startswith('##'):
                adjusted_lines.append(line[1:])  # ## -> #
            else:
                adjusted_lines.append(line)

        # Write section file
        section_path = dest / filename
        section_path.write_text('\n'.join(adjusted_lines), encoding='utf-8')
        print(f"Created: {section_path}")

    # Add links to index
    for filename, title in section_files:
        index_content.append(f'- [{title}](./{filename})')

    # Write index.md
    index_path = dest / 'index.md'
    index_path.write_text('\n'.join(index_content), encoding='utf-8')
    print(f"Created: {index_path}")

    print(f"\nDocument sharded successfully:")
    print(f"- Source: {source_path}")
    print(f"- Destination: {dest_folder}/")
    print(f"- Files created: {len(section_files) + 1}")
    print(f"- Sections: {len(sections)}")

if __name__ == '__main__':
    shard_document('docs/architecture.md', 'docs/architecture')
