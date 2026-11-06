#!/bin/bash
# Final delivery encode: film grain over the tense live-action section (0:31-0:48) added after
# the grade, then a two-pass 9 Mbps x264 encode (keeps the file under ~80 MB).
# usage: finish.sh master.mp4 削減アミダクジ_PV.mp4
set -e
VF="noise=alls=14:allf=t:enable='between(t,30.95,48.0)'"
cd "$(dirname "$2")"
ffmpeg -v error -y -i "$1" -vf "$VF" -c:v libx264 -preset slow -b:v 9000k -tune grain -pass 1 -an -f null /dev/null
ffmpeg -v error -y -i "$1" -vf "$VF" -c:v libx264 -preset slow -b:v 9000k -tune grain -pass 2 \
  -pix_fmt yuv420p -movflags +faststart -c:a copy "$(basename "$2")"
rm -f ffmpeg2pass*
