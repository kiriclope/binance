#!/bin/bash

message=$(date +'%d-%m-%Y_%R') 

git checkout "$1"

echo "branch $1"
echo "folder $2"

git add -u $2 
git commit -m "${message}" 

# if [ -n "$(git status --porcelain)" ];
# then
#     echo "IT IS CLEAN"
# else
    # git status 
    # echo "Pushing data to remote server!!!"
git push -u origin $1 
# fi 
