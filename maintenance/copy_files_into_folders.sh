#!/bin/bash
# 1st argument: text file with one file per line
# nth arguments: target folders

file_list="$1"
shift

for target_folder in "$@"
do
    mkdir -p "$target_folder"
    echo "cat '$file_list' | xargs -n 1 -I{} cp -r {} '$target_folder'"
    cat "$file_list" | xargs -n 1 -I{} cp -r {} "$target_folder"
done