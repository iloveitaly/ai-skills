# Justfile for generating and updating skills

set quiet

# List all available recipes
default:
    @just --list

# Update the justfile skill using the Python script
generate:
    uv run scripts/update_just_skill.py
