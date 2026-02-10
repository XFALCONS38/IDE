# AlgoTimer IDE (C/C++ Learning Toolkit)

This is a lightweight learning IDE for C and C++ focused on **timing, memory, and algorithm analysis**.
It includes automatic input-time exclusion, benchmark mode, complexity estimation, and optional step counting.

## Key Features
- **C / C++ toggle** (single editor or split view).
- **Accurate algorithm timing**: pauses while waiting for input.
- **CPU time** and **memory stats** (Windows: Peak WS + Private, plus code heap delta).
- **Step counter**: use `IDE_STEP()` / `IDE_STEPN(n)` inside your code.
- **Benchmark mode**: run multiple times, see mean + standard deviation.
- **Complexity estimator**: run multiple N values, plot + best-fit O(1)/O(n)/O(n log n)/O(n^2).
- **Race mode**: split screen, compile/run both, compare speeds.
- **Snippet library**: insert templates like DFS, BFS, Segment Tree, etc.
- **Syntax highlighting** and **theme switcher** (dark/light).
- **Auto-save projects** into a `projects/` folder.
- **Kill process** button for runaway programs.

## Quick Start (Prebuilt App)
You will have a **separate build for each OS**. Download the one for your OS:

### Windows
1. Download `IDE.exe`.
2. Run it directly (portable).
3. On first run, it auto-extracts the bundled compiler.

### macOS
1. Download the macOS build (`IDE` or `.app`).
2. Run it. If macOS blocks it, allow it via **System Settings > Privacy & Security**.
3. (Required once) Install Xcode Command Line Tools:
   ```
   xcode-select --install
   ```

### Linux
1. Download the Linux build (`IDE`).
2. Make it executable and run:
   ```
   chmod +x IDE
   ./IDE
   ```

## Build From Source (One-File Per OS)
All builds are **one-file** for each OS. Build on the OS you want to target.

### Windows
Script: `build_windows.ps1`
```
.\build_windows.ps1
```
Output: `dist\IDE.exe`

### Linux
Script: `build_linux.sh`
```
chmod +x build_linux.sh
./build_linux.sh
```
Output: `dist/IDE`

### macOS
Script: `build_macos.sh`
```
chmod +x build_macos.sh
./build_macos.sh
```
Output: `dist/IDE` (or `.app` depending on PyInstaller config)

## Bundled Compiler Notes
- **Windows**: w64devkit is bundled automatically (GCC/G++).
- **Linux**: build script auto-downloads a portable GCC/G++ toolchain from musl.cc.
- **macOS**: build script auto-downloads an LLVM clang toolchain, but still needs Xcode Command Line Tools for headers/SDK.

## Step Counter (How To Use)
The IDE cannot guess "steps" automatically. You define steps by inserting:
```c
IDE_STEP();      // +1 step
IDE_STEPN(5);    // +5 steps
```
Typical usage: add `IDE_STEP()` once per loop iteration or per comparison.

## Complexity Estimator Tips
- Use **multiple N values** and **multiple runs per N**.
- Provide an input template that includes `{N}`.
- The tool estimates best-fit among O(1), O(n), O(n log n), O(n^2).

## Folder Layout
```
IDE.py                 Main app
projects/              Auto-saved code files
build_windows.ps1      Windows one-file build script
build_linux.sh         Linux one-file build script
build_macos.sh         macOS one-file build script
BUILDING.md            Build details
```

## Runtime Data Location
- If the app runs from a **writable folder**, temp files and projects are stored next to the app.
- If it runs from a **read‑only location**, it uses a user data folder:
  - Linux: `~/.local/share/AlgoTimerIDE` (or `$XDG_DATA_HOME/AlgoTimerIDE`)
  - macOS: `~/Library/Application Support/AlgoTimerIDE`
  - Windows: `%LOCALAPPDATA%\AlgoTimerIDE`

## Troubleshooting
- **Compilation errors**: make sure the correct compiler is bundled for your OS.
- **No compiler found**: place toolchain in `compiler/bin` (Linux/macOS) or rebuild with the Windows script.
- **Timing is 0**: your program may be too fast; use larger inputs or complexity mode.

---
If you want extra features (e.g., auto-step injection, more snippets, extra languages), just ask.
