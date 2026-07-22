#!/usr/bin/env bash
# Pull an installed Android app's APK(s) via adb, named by package + version.
#
# Usage: tools/pull-apk.sh <package-or-keyword> [output-dir]
#   <package-or-keyword>  exact package name, or a substring to search for
#   [output-dir]          where to write (default: current directory)
#
# Output: <package>-<versionName>-<versionCode>.apk  (single APK), or a directory of the same
# name containing base.apk + split config APKs when the app is split.
#
# Requires: adb on PATH (winget Google.PlatformTools), phone plugged in with USB debugging
# authorized. Works in Git Bash (Windows) and macOS/Linux bash (3.2-safe: no mapfile).

set -euo pipefail

QUERY="${1:?usage: pull-apk.sh <package-or-keyword> [output-dir]}"
OUTDIR="${2:-.}"

# Strip the "package:" prefix and Windows CR that adb shell emits.
clean() { tr -d '\r' | sed 's/^package://'; }

[ "$(adb get-state 2>/dev/null || true)" = "device" ] || {
  echo "no authorized adb device - plug in the phone, enable USB debugging, and approve the" \
       "on-screen prompt (run 'adb devices' to check)." >&2
  exit 1
}

# Resolve the package name (exact, or first substring match).
matches=$(adb shell pm list packages | clean | grep -i "$QUERY" || true)
[ -n "$matches" ] || { echo "no installed package matching '$QUERY'" >&2; exit 1; }
count=$(printf '%s\n' "$matches" | grep -c .)
PKG=$(printf '%s\n' "$matches" | head -1)
[ "$count" -eq 1 ] || echo "note: $count packages match '$QUERY'; using '$PKG'" >&2
echo "package: $PKG"

# Version fields.
dump=$(adb shell dumpsys package "$PKG" | tr -d '\r')
VNAME=$(printf '%s\n' "$dump" | grep -m1 'versionName=' | sed 's/.*versionName=//')
VCODE=$(printf '%s\n' "$dump" | grep -m1 'versionCode=' | sed 's/.*versionCode=\([0-9][0-9]*\).*/\1/')
VNAME=${VNAME:-unknown}
VCODE=${VCODE:-0}
echo "version: $VNAME (code $VCODE)"

# APK path(s) - more than one means a split APK.
PATHS=()
while IFS= read -r line; do
  [ -n "$line" ] && PATHS+=("$line")
done < <(adb shell pm path "$PKG" | clean)
[ "${#PATHS[@]}" -gt 0 ] || { echo "no APK paths returned for $PKG" >&2; exit 1; }

mkdir -p "$OUTDIR"
BASE="${PKG}-${VNAME}-${VCODE}"

if [ "${#PATHS[@]}" -eq 1 ]; then
  DEST="$OUTDIR/${BASE}.apk"
  adb pull "${PATHS[0]}" "$DEST" >/dev/null
  echo "pulled: $DEST"
else
  DEST="$OUTDIR/${BASE}"
  mkdir -p "$DEST"
  for p in "${PATHS[@]}"; do adb pull "$p" "$DEST/" >/dev/null; done
  echo "pulled ${#PATHS[@]} split APKs to: $DEST/"
  echo "(merge with apkeditor/apktool if a single APK is needed)"
fi
