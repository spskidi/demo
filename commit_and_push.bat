@echo off
echo Adding files to git...
git add .

echo Committing changes...
git commit -m "Simplify superuser creation in start.sh"

echo Pushing to remote repository...
git push

echo Done!
