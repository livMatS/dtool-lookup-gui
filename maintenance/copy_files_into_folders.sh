#!/bin/bash
# 1st argument: text file with one file per line
# nth arguments: target folders

file_list="$1"
shift

# check whether dos2unix is available and try to convert line endings to lf only if so
CRLF_TO_LF_PIPE=""
if [ -x "$(command -v dos2unix)" ]; then
    CRLF_TO_LF_PIPE="dos2unix --verbose |"  # --verbose writes to stderr
else
    echo 'Warning: dos2unix is not available.' >&2
fi


for target_folder in "$@"
do
    mkdir -p "$target_folder"
    cmd="cat '$file_list' | ${CRLF_TO_LF_PIPE} xargs -I{} cp -r {} '$target_folder'"
    echo "$cmd"
    bash -c "$cmd"
done