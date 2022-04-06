#!/bin/bash -x
# generate standard size icons
# needs png2icns, i.e. via
#    sudo apt install icnsutils
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
# icns: Apple Icon Image format
# https://en.wikipedia.org/wiki/Apple_Icon_Image_format
icns_sizes=(16x16 32x32 48x48 128x128 256x256 512x512)
for svg_file in $prefix/*.svg; do
  svg_basename=$(basename "${svg_file}")
  base="${svg_basename%%.*}"
  icns_file="$prefix/$base.icns"
  png_files=()
  for icns_size in "${icns_sizes[@]}"; do
    png_files+=("${prefix}/${icns_size}/${base}.png")
  done
  png2icns "${icns_file}" ${png_files[@]}
done
