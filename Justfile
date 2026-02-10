# Justfile for generating and updating skills

set quiet

# List all available recipes
default:
    @just --list

# Update the justfile skill using the Python script
generate:
    uv run scripts/update_just_skill.py

# Sync repository metadata from metadata.json
github_repo_set_metadata:
    gh repo edit \
      --description "$(jq -r '.description' metadata.json)" \
      --homepage "$(jq -r '.homepage' metadata.json)" \
      --add-topic "$(jq -r '.keywords | join(",")' metadata.json)"
