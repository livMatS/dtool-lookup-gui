#!/bin/bash
# 1st argument: text file with one file per line
# nth arguments: target folders

file_list="$1"
shift

for target_folder in "$@"
do
    mkdir -p "$target_folder"
    echo xargs -a "$file_list" cp -r -t "$target_folder"
    xargs -a "$file_list" cp -r -t "$target_folder"
done

