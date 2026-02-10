#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
TOOLCHAIN_DIR="$ROOT/compiler"

download_toolchain() {
  local arch
  arch="$(uname -m)"
  local tgz=""
  case "$arch" in
    x86_64|amd64) tgz="x86_64-linux-musl-native.tgz" ;;
    aarch64|arm64) tgz="aarch64-linux-musl-native.tgz" ;;
    i686|i386) tgz="i686-linux-musl-native.tgz" ;;
    armv7l) tgz="armv7l-linux-musleabihf-native.tgz" ;;
    armv6l) tgz="armv6-linux-musleabihf-native.tgz" ;;
    *) echo "Unsupported architecture: $arch"; exit 1 ;;
  esac

  local url="https://musl.cc/$tgz"
  local tmp
  tmp="$(mktemp)"
  echo "Downloading toolchain: $url"

  if command -v curl >/dev/null 2>&1; then
    curl -L --fail "$url" -o "$tmp"
  elif command -v wget >/dev/null 2>&1; then
    wget -O "$tmp" "$url"
  else
    echo "Neither curl nor wget found."
    exit 1
  fi

  mkdir -p "$TOOLCHAIN_DIR"
  tar -xf "$tmp" -C "$TOOLCHAIN_DIR" --strip-components=1
  rm -f "$tmp"
}

if [[ ! -x "$TOOLCHAIN_DIR/bin/g++" && ! -x "$TOOLCHAIN_DIR/bin/clang++" ]]; then
  download_toolchain
fi

if [[ ! -x "$TOOLCHAIN_DIR/bin/g++" && ! -x "$TOOLCHAIN_DIR/bin/clang++" ]]; then
  echo "Toolchain install failed (missing compiler/bin)."
  exit 1
fi

python3 -m pip install --user pyinstaller >/dev/null

python3 -m PyInstaller \
  --onefile \
  --noconsole \
  --clean \
  --add-data "$TOOLCHAIN_DIR:compiler" \
  "$ROOT/IDE.py"

echo "Build complete: $ROOT/dist/IDE"
