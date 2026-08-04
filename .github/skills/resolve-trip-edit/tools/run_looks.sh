#!/bin/zsh
set -e
cd /Users/danielwojcik/vscode/davinci-resolve-mcp
export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
export PYTHONPATH="$PYTHONPATH:/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"
P=venv/bin/python
for L in "$@"; do
  $P tmp/install_look.py "$L"
  $P tmp/render_one.py "$L"
  $P tmp/film_profile.py "/Volumes/Lexar/Export/_LOOKTEST/$L.mp4" "$L" 120 >/dev/null 2>&1
  echo "   profiled $L"
done
