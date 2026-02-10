# Building Portable Bundles (Windows / macOS / Linux)

This IDE can be shipped as a **single-file app per OS**. Each OS needs its **own build**.

## Common Requirements
- Python 3.10+ with Tkinter
- PyInstaller (the scripts install it automatically)
- A **portable compiler toolchain** placed in `compiler/` (for macOS/Linux)

The IDE looks for compilers in:
```
compiler/bin
compiler/clang/bin
compiler/llvm/bin
```

If you bundle the toolchain, users can run the IDE without installing a compiler.

---

## Windows (one-file EXE)
Script: `build_windows.ps1`

What it does:
- Downloads **w64devkit** (GCC/G++) as `w64devkit.zip`
- Builds a **single EXE** with PyInstaller and embeds the toolchain zip

Output:
```
dist\IDE.exe
```

---

## Linux (one-file)
Script: `build_linux.sh`

Before running:
- The script **auto-downloads** a portable compiler from musl.cc based on your CPU architecture.

Output:
```
dist/IDE
```

---

## macOS (one-file)
Script: `build_macos.sh`

Notes:
- macOS still requires **Xcode Command Line Tools** for the system SDK.
  - Install once with: `xcode-select --install`
- The script **auto-downloads** an LLVM clang toolchain (from LLVM GitHub releases) if missing.

Output:
```
dist/IDE
```

---

## Why separate builds?
Executable formats and bundled compilers are **OS-specific**. A single binary cannot run on all three OSes.
