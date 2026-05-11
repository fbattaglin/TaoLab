#!/bin/bash
# Install Tao Lab git hooks into .git/hooks/
# Run once after cloning: bash scripts/install_hooks.sh

set -e
REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

cp "$REPO_ROOT/scripts/pre-commit" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"

echo "✓ Installed pre-commit hook."
echo "  Hook guards against committing stale frontend dist/."
