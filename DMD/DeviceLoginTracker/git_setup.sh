#!/bin/bash

# Script to set up Git configuration for the Device Login Tracker project
# Save this file and run it on your local machine after downloading the project

# Remove existing origin remote if it exists
git remote remove origin 2>/dev/null

echo "Previous remote connections removed (if any existed)."
echo "Your repository is now local only, with no remote connections."
echo ""
echo "To connect to a new GitHub repository, run:"
echo "git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git"
echo "git push -u origin main"