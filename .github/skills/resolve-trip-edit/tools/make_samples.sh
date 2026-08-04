#!/bin/zsh
# Render one 20s sample per look at preview resolution, named for the look.
cd /Users/danielwojcik/vscode/davinci-resolve-mcp
export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
export PYTHONPATH="$PYTHONPATH:/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"
P=venv/bin/python
OUT=/Volumes/Lexar/Export/WRO_LOOK_SAMPLES
mkdir -p "$OUT"
export OUTDIR="$OUT" W=1920 H=800

render() {   # $1 = cube basename in tmp/, $2 = friendly sample name
  if [[ -f "$OUT/$2.mp4" && -z "$FORCE" ]]; then
    echo "   (kept) $2.mp4"
    return 0
  fi
  if [[ ! -f "$OUT/$1.mp4" ]]; then
    $P tools/install_look.py "$1" || { echo "!! install failed $1"; return 1; }
    $P tools/render_one.py "$1"   || { echo "!! render failed $1"; return 1; }
  fi
  # Resolve can still hold the file open briefly after the job reports Complete,
  # so a single mv sometimes fails; retry rather than abort the whole run.
  for i in 1 2 3 4 5; do
    mv -f "$OUT/$1.mp4" "$OUT/$2.mp4" 2>/dev/null && break
    sleep 2
  done
  if [[ -f "$OUT/$2.mp4" ]]; then echo "   -> $2.mp4"; else echo "!! rename failed $1"; fi
  rm -f "$OUT/._$1.mp4"
}

render WRO_ShowLook_REFERENCE_v2 SAMPLE_1_Print2383
render WRO_Hollywood_v4          SAMPLE_2_Marvel
render WRO_Look_Equalizer_v6     SAMPLE_3_Equalizer
render WRO_Look_Burnt_v5         SAMPLE_4_Burnt
render WRO_Look_Ferrari_v4       SAMPLE_5_Ferrari
render WRO_Look_Silo_v2          SAMPLE_6_Silo
render WRO_Look_MarvelOlive_v1   SAMPLE_7_MarvelOlive
render WRO_Look_BladeRunner_v1   SAMPLE_8_BladeRunner
echo done
