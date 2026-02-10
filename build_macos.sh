#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
TOOLCHAIN_DIR="$ROOT/compiler"

if ! xcrun --show-sdk-path >/dev/null 2>&1; then
  echo "Xcode Command Line Tools not found."
  echo "Install with: xcode-select --install"
  exit 1
fi

download_toolchain() {
  local url
  url="$(python3 - <<'PY'
import json
import re
import sys
import urllib.request
import platform

arch = platform.machine().lower()
arch_terms = ["arm64", "aarch64"] if arch in ("arm64", "aarch64") else ["x86_64", "amd64"]
data = json.load(urllib.request.urlopen("https://api.github.com/repos/llvm/llvm-project/releases/latest"))
assets = data.get("assets", [])
pat = re.compile(r"(clang\\+llvm|LLVM)-.*(apple-darwin|macos).*\\.tar\\.xz$")

def pick(matches):
    for a in matches:
        name = a.get("name", "").lower()
        if any(term in name for term in arch_terms):
            return a.get("browser_download_url")
    return None

filtered = [a for a in assets if pat.search(a.get("name",""))]
url = pick(filtered)
if not url and filtered:
    url = filtered[0].get("browser_download_url")
if not url:
    sys.exit(1)
print(url)
PY
)"
  if [[ -z "$url" ]]; then
    echo "Could not locate a macOS LLVM toolchain."
    exit 1
  fi

  local tmp
  tmp="$(mktemp)"
  echo "Downloading toolchain: $url"
  if command -v curl >/dev/null 2>&1; then
    curl -L --fail "$url" -o "$tmp"
  else
    echo "curl not found."
    exit 1
  fi

  mkdir -p "$TOOLCHAIN_DIR"
  tar -xf "$tmp" -C "$TOOLCHAIN_DIR" --strip-components=1
  rm -f "$tmp"
}

if [[ ! -x "$TOOLCHAIN_DIR/bin/clang++" ]]; then
  download_toolchain
fi

if [[ ! -x "$TOOLCHAIN_DIR/bin/clang++" ]]; then
  echo "Toolchain install failed (missing compiler/bin)."
  exit 1
fi

python3 -m pip install --user pyinstaller >/dev/null

python3 -m PyInstaller \
  --onefile \
  --windowed \
  --clean \
  --add-data "$TOOLCHAIN_DIR:compiler" \
  "$ROOT/IDE.py"

echo "Build complete: $ROOT/dist/IDE"
