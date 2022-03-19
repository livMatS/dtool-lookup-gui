#!/bin/bash
# generate standard size icons
prefix=${1:-data/icons}
# see https://blog.icons8.com/articles/choosing-the-right-size-and-format-for-icons/
sizes=(1024x1024 512x512 256x256 128x128 96x96 64x64 48x48 32x32 24x24 22x22 16x16)
formats=(ico png xpm)
for size in "${sizes[@]}"; do
  echo "Create icons in $prefix/$size"
  mkdir -p "$prefix/$size"
  for format in "${formats[@]}"; do
    mogrify -path "$prefix/$size" -resize $size -density $size -format $format -background none "$prefix/*.svg"
  done
done
