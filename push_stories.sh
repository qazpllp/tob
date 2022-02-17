#!/bin/bash
#  Creates/pushes a separate branch which matches master, and also contains the stories. Ensure the stories are populated before running this command. Pushes and replaces origin/stories

# Ensure using master branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ $BRANCH != "master" ]; then
    echo "Must be on master branch"
    exit 1
fi

# Move to fresh stories branch - up to date with master
git branch -D stories
git checkout -b stories

# Remove stories from gitignore
sed -i '/stories/d' .gitignore

# Commit stories
git commit -m "update gitignore" .gitignore
git add .
git commit -m "add stories"

# Push 
git push --force --set-upstream origin stories

# Return to master branch
git checkout master
