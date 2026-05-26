#!/bin/bash
# sync-to-repo.sh - Sincroniza skills locales al repo

cd ~/repos/nelson-hermes-skills || exit 1
git add .
git commit -m "sync: $(date '+%Y-%m-%d %H:%M:%S')"
git push