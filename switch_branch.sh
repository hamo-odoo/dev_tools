#!/bin/bash

BRANCH=$1

BASE=~/odoo18/
REPOS=("community" "enterprise")

for repo in "${REPOS[@]}"; do
    echo "➡️  $repo"
    cd "$BASE/$repo" || exit 1
    git fetch odoo "$BRANCH"
    git checkout "$BRANCH"
    git pull odoo "$BRANCH" --rebase
done

echo "✅ Switched all repos to $BRANCH"
