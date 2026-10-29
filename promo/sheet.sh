#!/usr/bin/env bash
# Contact sheet of a recorded segment to pick the cuts: promo/sheet.sh <segment> [seconds between frames]
# Writes promo/work/sheets/<segment>.jpg with the time of each frame.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
step=${2:-0.5}
mkdir -p "$here/work/sheets"
ffmpeg -loglevel error -y -i "$here/work/segs/$1.mp4" \
  -vf "fps=1/$step,scale=480:-1,drawtext=text='%{pts\:hms}':x=8:y=8:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6,tile=4x6" \
  -frames:v 1 "$here/work/sheets/$1.jpg"
echo "$here/work/sheets/$1.jpg"
