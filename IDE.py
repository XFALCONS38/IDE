import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading
import os
import re
import time
import math
import statistics
import sys
import shutil
import urllib.request
import zipfile

# --- CONFIGURATION ---
def get_platform_key():
    if sys.platform.startswith("win"):
        return "win32"
    if sys.platform == "darwin":
        return "darwin"
    return "linux"

PLATFORM_KEY = get_platform_key()

COMPILER_URLS = {
    "win32": "https://github.com/skeeto/w64devkit/releases/download/v1.20.0/w64devkit-1.20.0.zip",
}

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = BASE_DIR

def pick_work_dir():
    if os.path.isdir(BASE_DIR) and os.access(BASE_DIR, os.W_OK):
        return BASE_DIR
    home = os.path.expanduser("~")
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA", home)
    elif sys.platform == "darwin":
        base = os.path.join(home, "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.join(home, ".local", "share"))
    return os.path.join(base, "AlgoTimerIDE")

WORK_DIR = pick_work_dir()
os.makedirs(WORK_DIR, exist_ok=True)

BUNDLED_COMPILER_ZIP_NAMES = {
    "win32": ["w64devkit.zip", "w64devkit-1.20.0.zip"],
    "linux": ["toolchain-linux.zip", "compiler-linux.zip"],
    "darwin": ["toolchain-macos.zip", "compiler-macos.zip"],
}

def find_bundled_compiler_zip():
    for name in BUNDLED_COMPILER_ZIP_NAMES.get(PLATFORM_KEY, []):
        path = os.path.join(BUNDLE_DIR, name)
        if os.path.exists(path):
            return path
    return None

def iter_bundled_compiler_bin_candidates():
    candidates = []
    if os.name == "nt":
        candidates.extend([
            os.path.join(LOCAL_COMPILER_DIR, "w64devkit", "bin"),
            os.path.join(BUNDLE_DIR, "w64devkit", "bin"),
            os.path.join(LOCAL_COMPILER_DIR, "bin"),
            os.path.join(BUNDLE_DIR, "bin"),
        ])
    else:
        roots = [
            LOCAL_COMPILER_DIR,
            os.path.join(LOCAL_COMPILER_DIR, "toolchain"),
            os.path.join(LOCAL_COMPILER_DIR, "llvm"),
            os.path.join(LOCAL_COMPILER_DIR, "clang"),
            os.path.join(BUNDLE_DIR, "compiler"),
            os.path.join(BUNDLE_DIR, "toolchain"),
            os.path.join(BUNDLE_DIR, "llvm"),
            os.path.join(BUNDLE_DIR, "clang"),
        ]
        for root in roots:
            candidates.append(os.path.join(root, "bin"))

    seen = set()
    for path in candidates:
        if path and path not in seen:
            seen.add(path)
            yield path

os.makedirs(PROJECTS_DIR, exist_ok=True)
LOCAL_COMPILER_DIR = os.path.join(WORK_DIR, "compiler")
PROJECTS_DIR = os.path.join(WORK_DIR, "projects")
TEMP_SOURCE_FILE_CPP = os.path.join(WORK_DIR, "temp_code.cpp")
TEMP_SOURCE_FILE_C = os.path.join(WORK_DIR, "temp_code.c")
TEMP_SOURCE_FILE_CPP_RIGHT = os.path.join(WORK_DIR, "temp_code_right.cpp")
TEMP_SOURCE_FILE_C_RIGHT = os.path.join(WORK_DIR, "temp_code_right.c")
EXE_SUFFIX = ".exe" if os.name == "nt" else ""
TEMP_EXE_FILE = os.path.join(WORK_DIR, f"temp_code{EXE_SUFFIX}")
TEMP_EXE_FILE_RIGHT = os.path.join(WORK_DIR, f"temp_code_right{EXE_SUFFIX}")
BENCHMARK_DEFAULT_RUNS = 10
RUN_BUTTON_TEXT = "Run & Measure Algo Time"

THEMES = {
    "Dark": {
        "root_bg": "#1f1f1f",
        "toolbar_bg": "#2b2b2b",
        "toolbar_fg": "#e0e0e0",
        "info_bg": "#ffeb3b",
        "info_fg": "#000000",
        "editor_bg": "#1e1e1e",
        "editor_fg": "#d4d4d4",
        "insert_bg": "#ffffff",
        "status_fg": "#dddddd",
        "button_run_bg": "#d32f2f",
        "button_kill_bg": "#616161",
        "button_fg": "#ffffff",
        "highlight": {
            "keyword": "#569cd6",
            "type": "#4ec9b0",
            "string": "#ce9178",
            "comment": "#6a9955",
            "number": "#b5cea8",
            "preproc": "#9cdcfe",
        },
    },
    "Light": {
        "root_bg": "#f5f5f5",
        "toolbar_bg": "#e0e0e0",
        "toolbar_fg": "#222222",
        "info_bg": "#fff59d",
        "info_fg": "#000000",
        "editor_bg": "#ffffff",
        "editor_fg": "#1e1e1e",
        "insert_bg": "#000000",
        "status_fg": "#333333",
        "button_run_bg": "#d32f2f",
        "button_kill_bg": "#757575",
        "button_fg": "#ffffff",
        "highlight": {
            "keyword": "#1f4e79",
            "type": "#267f99",
            "string": "#a31515",
            "comment": "#008000",
            "number": "#098658",
            "preproc": "#0451a5",
        },
    },
}

SNIPPETS = {
    "CP Template": {
        "C++": """#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    // Your code here
    return 0;
}
""",
        "C": """#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

int main() {
    // Your code here
    return 0;
}
""",
    },
    "DFS (adj list)": {
        "C++": """#include <bits/stdc++.h>
using namespace std;

const int MAXN = 200000;
vector<int> g[MAXN];
bool vis[MAXN];

void dfs(int u) {
    vis[u] = true;
    for (int v : g[u]) {
        if (!vis[v]) dfs(v);
    }
}
""",
        "C": """#include <stdio.h>
#include <string.h>

#define MAXN 200000
#define MAXM 400000

int head[MAXN], to[MAXM], nxt[MAXM], edge_cnt;
char vis[MAXN];

void add_edge(int u, int v) {
    to[edge_cnt] = v;
    nxt[edge_cnt] = head[u];
    head[u] = edge_cnt++;
}

void dfs(int u) {
    vis[u] = 1;
    for (int e = head[u]; e != -1; e = nxt[e]) {
        int v = to[e];
        if (!vis[v]) dfs(v);
    }
}

void init_graph(int n) {
    for (int i = 0; i < n; i++) head[i] = -1;
    edge_cnt = 0;
    memset(vis, 0, sizeof(vis));
}
""",
    },
    "BFS (queue)": {
        "C++": """#include <bits/stdc++.h>
using namespace std;

const int MAXN = 200000;
vector<int> g[MAXN];
int distv[MAXN];

void bfs(int src) {
    queue<int> q;
    fill(distv, distv + MAXN, -1);
    distv[src] = 0;
    q.push(src);
    while (!q.empty()) {
        int u = q.front();
        q.pop();
        for (int v : g[u]) {
            if (distv[v] == -1) {
                distv[v] = distv[u] + 1;
                q.push(v);
            }
        }
    }
}
""",
        "C": None,
    },
    "Segment Tree (sum)": {
        "C++": """#include <bits/stdc++.h>
using namespace std;

struct SegTree {
    int n;
    vector<long long> st;
    SegTree(int n): n(n), st(4 * n, 0) {}
    void update(int p, long long val, int node, int l, int r) {
        if (l == r) { st[node] = val; return; }
        int mid = (l + r) / 2;
        if (p <= mid) update(p, val, node * 2, l, mid);
        else update(p, val, node * 2 + 1, mid + 1, r);
        st[node] = st[node * 2] + st[node * 2 + 1];
    }
    long long query(int ql, int qr, int node, int l, int r) {
        if (qr < l || r < ql) return 0;
        if (ql <= l && r <= qr) return st[node];
        int mid = (l + r) / 2;
        return query(ql, qr, node * 2, l, mid) + query(ql, qr, node * 2 + 1, mid + 1, r);
    }
};
""",
        "C": None,
    },
    "DSU (Union-Find)": {
        "C++": """#include <bits/stdc++.h>
using namespace std;

struct DSU {
    vector<int> p, r;
    DSU(int n): p(n), r(n, 0) { iota(p.begin(), p.end(), 0); }
    int find(int x) { return p[x] == x ? x : p[x] = find(p[x]); }
    void unite(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return;
        if (r[a] < r[b]) swap(a, b);
        p[b] = a;
        if (r[a] == r[b]) r[a]++;
    }
};
""",
        "C": None,
    },
    "Dijkstra": {
        "C++": """#include <bits/stdc++.h>
using namespace std;

using ll = long long;
const ll INF = (1LL<<62);

vector<vector<pair<int,int>>> g;
vector<ll> distv;

void dijkstra(int src) {
    int n = (int)g.size();
    distv.assign(n, INF);
    priority_queue<pair<ll,int>, vector<pair<ll,int>>, greater<pair<ll,int>>> pq;
    distv[src] = 0;
    pq.push({0, src});
    while (!pq.empty()) {
        auto [d, u] = pq.top(); pq.pop();
        if (d != distv[u]) continue;
        for (auto [v, w] : g[u]) {
            if (distv[v] > d + w) {
                distv[v] = d + w;
                pq.push({distv[v], v});
            }
        }
    }
}
""",
        "C": None,
    },
}

class AlgoTimerIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("C/C++ Algo IDE (Pure CPU Time)")
        self.root.geometry("1100x750")

        self.compiler_cmd_cpp = None
        self.compiler_cmd_c = None
        self.c_compiler_is_cpp_driver = False
        self.running_process = None
        self.running_processes = []
        self._autosave_job = None
        self._highlight_jobs = {}
        self._complexity_window = None

        self.benchmark_var = tk.BooleanVar(value=False)
        self.benchmark_runs_var = tk.IntVar(value=BENCHMARK_DEFAULT_RUNS)
        self.complexity_runs_var = tk.IntVar(value=3)
        self.language_var = tk.StringVar(value="C++")
        self.split_var = tk.BooleanVar(value=False)
        self.theme_var = tk.StringVar(value="Dark")
        self.project_name_var = tk.StringVar(value="Untitled")

        # --- UI SETUP ---
        self.toolbar = tk.Frame(root, pady=5)
        self.toolbar.pack(fill=tk.X)

        self.btn_run = tk.Button(
            self.toolbar,
            text=RUN_BUTTON_TEXT,
            command=self.run_thread,
            bg="#d32f2f",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            width=25,
        )
        self.btn_run.pack(side=tk.LEFT, padx=10)

        self.btn_kill = tk.Button(
            self.toolbar,
            text="Kill Process",
            command=self.kill_process,
            bg="#616161",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=12,
        )
        self.btn_kill.pack(side=tk.LEFT, padx=6)

        self.btn_race = tk.Button(
            self.toolbar,
            text="Race",
            command=self.open_race_dialog,
            font=("Segoe UI", 10, "bold"),
            width=8,
        )
        self.btn_race.pack(side=tk.LEFT, padx=6)

        self.chk_split = tk.Checkbutton(
            self.toolbar,
            text="Split View",
            variable=self.split_var,
            command=self.toggle_split,
            font=("Segoe UI", 10),
        )
        self.chk_split.pack(side=tk.LEFT, padx=6)

        self.chk_bench = tk.Checkbutton(
            self.toolbar,
            text="Benchmark",
            variable=self.benchmark_var,
            command=self.on_benchmark_toggle,
            font=("Segoe UI", 10),
        )
        self.chk_bench.pack(side=tk.LEFT, padx=6)

        self.entry_runs = tk.Entry(
            self.toolbar,
            textvariable=self.benchmark_runs_var,
            width=4,
            font=("Segoe UI", 10),
        )
        self.entry_runs.pack(side=tk.LEFT, padx=(2, 0))

        self.lbl_runs = tk.Label(self.toolbar, text="runs", font=("Segoe UI", 10))
        self.lbl_runs.pack(side=tk.LEFT, padx=(2, 10))

        self.btn_complexity = tk.Button(
            self.toolbar,
            text="Complexity",
            command=self.open_complexity_window,
            font=("Segoe UI", 10, "bold"),
            width=12,
        )
        self.btn_complexity.pack(side=tk.LEFT, padx=6)

        self.lbl_complexity = tk.Label(self.toolbar, text="Complexity: N/A", font=("Segoe UI", 10))
        self.lbl_complexity.pack(side=tk.LEFT, padx=8)

        self.lbl_status = tk.Label(self.toolbar, text="Ready", font=("Segoe UI", 10))
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        self.options_bar = tk.Frame(root, pady=3)
        self.options_bar.pack(fill=tk.X)

        self.lbl_project = tk.Label(self.options_bar, text="Project:", font=("Segoe UI", 10))
        self.lbl_project.pack(side=tk.LEFT, padx=(10, 4))

        self.entry_project = tk.Entry(
            self.options_bar,
            textvariable=self.project_name_var,
            width=22,
            font=("Segoe UI", 10),
        )
        self.entry_project.pack(side=tk.LEFT, padx=(0, 12))

        self.lbl_theme = tk.Label(self.options_bar, text="Theme:", font=("Segoe UI", 10))
        self.lbl_theme.pack(side=tk.LEFT, padx=(10, 4))

        self.theme_menu = tk.OptionMenu(self.options_bar, self.theme_var, *THEMES.keys(), command=self.apply_theme)
        self.theme_menu.config(width=8, font=("Segoe UI", 10))
        self.theme_menu.pack(side=tk.LEFT, padx=(0, 12))

        self.lbl_language = tk.Label(self.options_bar, text="Language:", font=("Segoe UI", 10))
        self.lbl_language.pack(side=tk.LEFT, padx=(10, 4))

        self.language_menu = tk.OptionMenu(self.options_bar, self.language_var, "C", "C++", command=self.on_language_change)
        self.language_menu.config(width=6, font=("Segoe UI", 10))
        self.language_menu.pack(side=tk.LEFT, padx=(0, 12))

        # Instructions
        self.info_frame = tk.Frame(root, pady=2)
        self.info_frame.pack(fill=tk.X)
        self.info_label = tk.Label(
            self.info_frame,
            text="Info: Timer pauses during input. Use IDE_STEP() / IDE_STEPN(n) to count steps.",
        )
        self.info_label.pack()

        # Work area (snippet sidebar + editors)
        self.work_area = tk.Frame(root)
        self.work_area.pack(fill=tk.BOTH, expand=True)

        self.snippet_frame = tk.Frame(self.work_area, width=220)
        self.snippet_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Editors (split view)
        self.editor_pane = tk.PanedWindow(self.work_area, orient=tk.HORIZONTAL, sashwidth=6)
        self.editor_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.left_frame = tk.Frame(self.editor_pane)
        self.right_frame = tk.Frame(self.editor_pane)

        self.editor_left = scrolledtext.ScrolledText(
            self.left_frame,
            font=("Consolas", 13),
            undo=True,
        )
        self.editor_left.pack(fill=tk.BOTH, expand=True)

        self.editor_right = scrolledtext.ScrolledText(
            self.right_frame,
            font=("Consolas", 13),
            undo=True,
        )
        self.editor_right.pack(fill=tk.BOTH, expand=True)

        self.active_editor = self.editor_left
        self.editor_left.bind("<FocusIn>", lambda e, ed=self.editor_left: self.set_active_editor(ed))
        self.editor_right.bind("<FocusIn>", lambda e, ed=self.editor_right: self.set_active_editor(ed))

        self.editor_pane.add(self.left_frame, stretch="always")

        default_code = """#include <stdio.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif

int main() {
    int n;
    
    printf("--- Phase 1: Input ---\n");
    printf("Enter a number (take your time): ");
    
    // The timer will PAUSE here automatically!
    scanf("%d", &n); 
    
    printf("\n--- Phase 2: Heavy Work ---\n");
    printf("Processing... (simulating 2 seconds of work)\n");
    
    // This part is timed!
#ifdef _WIN32
    Sleep(2000);
#else
    usleep(2000 * 1000);
#endif
    
    printf("Done! The complexity timer captured strictly the 2 seconds.\n");

    return 0;
}"""
        self.editor_left.insert(tk.END, default_code)
        self.editor_right.insert(tk.END, default_code)

        self.editor = self.editor_left

        self.editor_left.edit_modified(False)
        self.editor_right.edit_modified(False)
        self.editor_left.bind("<<Modified>>", lambda e, ed=self.editor_left: self.on_editor_modified(ed))
        self.editor_right.bind("<<Modified>>", lambda e, ed=self.editor_right: self.on_editor_modified(ed))
        self.project_name_var.trace_add("write", self.on_project_name_change)

        self.build_snippet_sidebar()

        os.makedirs(PROJECTS_DIR, exist_ok=True)
        self.apply_theme()
        self.schedule_highlight(self.editor_left)
        self.schedule_highlight(self.editor_right)
        self.check_compiler()

    # --- INTELLIGENT CODE INJECTION ---

    def _build_code_mask(self, text):
        mask = [True] * len(text)
        i = 0
        in_single = False
        in_multi = False
        in_string = False
        in_char = False
        escape = False

        while i < len(text):
            ch = text[i]
            nxt = text[i + 1] if i + 1 < len(text) else ""

            if in_single:
                mask[i] = False
                if ch == "\n":
                    in_single = False
                i += 1
                continue

            if in_multi:
                mask[i] = False
                if ch == "*" and nxt == "/":
                    mask[i + 1] = False
                    i += 2
                    in_multi = False
                else:
                    i += 1
                continue

            if in_string:
                mask[i] = False
                if escape:
                    escape = False
                else:
                    if ch == "\\":
                        escape = True
                    elif ch == '"':
                        in_string = False
                i += 1
                continue

            if in_char:
                mask[i] = False
                if escape:
                    escape = False
                else:
                    if ch == "\\":
                        escape = True
                    elif ch == "'":
                        in_char = False
                i += 1
                continue

            if ch == "/" and nxt == "/":
                mask[i] = False
                mask[i + 1] = False
                in_single = True
                i += 2
                continue

            if ch == "/" and nxt == "*":
                mask[i] = False
                mask[i + 1] = False
                in_multi = True
                i += 2
                continue

            if ch == '"':
                mask[i] = False
                in_string = True
                i += 1
                continue

            if ch == "'":
                mask[i] = False
                in_char = True
                i += 1
                continue

            i += 1

        return mask

    def _replace_in_code(self, text, pattern, repl, flags=re.DOTALL):
        mask = self._build_code_mask(text)
        out = []
        last = 0
        for match in re.finditer(pattern, text, flags):
            if not all(mask[match.start():match.end()]):
                continue
            out.append(text[last:match.start()])
            out.append(repl(match) if callable(repl) else repl)
            last = match.end()
        out.append(text[last:])
        return "".join(out)

    def _find_code_match(self, text, pattern, flags=re.DOTALL):
        mask = self._build_code_mask(text)
        for match in re.finditer(pattern, text, flags):
            if all(mask[match.start():match.end()]):
                return match
        return None

    def inject_smart_timer(self, user_code):
        """
        1. Injects a Timer Utility.
        2. Wraps 'main' to start/stop this timer.
        3. Finds input functions and wraps them to PAUSE the timer.
        """

        lang = self.language_var.get()
        if lang == "C":
            timer_header = r"""
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <time.h>
#ifdef _WIN32
#include <windows.h>
#include <psapi.h>
#endif

// --- IDE INJECTED TIMER ---
double _IDE_TOTAL_TIME = 0.0;  // wall time (no input)
double _IDE_TOTAL_CPU = 0.0;   // cpu time
int _IDE_IS_RUNNING = 0;
int _IDE_BENCHMARK = 0;

double _IDE_START_WALL = 0.0;
double _IDE_START_CPU = 0.0;

unsigned long long _IDE_STEP_COUNT = 0;

#define _IDE_MAGIC 0xC0DEC0DEu
typedef struct { size_t size; unsigned int magic; } _IDE_HDR;
size_t _IDE_CUR_HEAP = 0;
size_t _IDE_MAX_HEAP = 0;
size_t _IDE_HEAP_BASE = 0;
int _IDE_TRACK_HEAP = 0;

#ifndef IDE_STEP
#define IDE_STEP() do { _IDE_STEP_COUNT++; } while (0)
#endif
#ifndef IDE_STEPN
#define IDE_STEPN(n) do { _IDE_STEP_COUNT += (unsigned long long)(n); } while (0)
#endif

#ifdef _WIN32
SIZE_T _IDE_BASE_WS = 0;
SIZE_T _IDE_BASE_PRIV = 0;
#endif

static void* _IDE_raw_malloc(size_t size) { return malloc(size); }
static void* _IDE_raw_realloc(void* ptr, size_t size) { return realloc(ptr, size); }
static void _IDE_raw_free(void* ptr) { free(ptr); }

void* _IDE_malloc(size_t size) {
    size_t total = size + sizeof(_IDE_HDR);
    _IDE_HDR* h = (_IDE_HDR*)_IDE_raw_malloc(total);
    if (!h) return NULL;
    h->size = size;
    h->magic = _IDE_MAGIC;
    _IDE_CUR_HEAP += size;
    if (_IDE_TRACK_HEAP && _IDE_CUR_HEAP > _IDE_MAX_HEAP) _IDE_MAX_HEAP = _IDE_CUR_HEAP;
    return (void*)(h + 1);
}

void* _IDE_calloc(size_t n, size_t size) {
    size_t bytes = n * size;
    void* p = _IDE_malloc(bytes);
    if (p) memset(p, 0, bytes);
    return p;
}

void* _IDE_realloc(void* ptr, size_t size) {
    if (!ptr) return _IDE_malloc(size);
    if (size == 0) { _IDE_raw_free(ptr); return NULL; }
    _IDE_HDR* h = ((_IDE_HDR*)ptr) - 1;
    if (h->magic != _IDE_MAGIC) {
        return _IDE_raw_realloc(ptr, size);
    }
    size_t old = h->size;
    size_t total = size + sizeof(_IDE_HDR);
    _IDE_HDR* nh = (_IDE_HDR*)_IDE_raw_realloc(h, total);
    if (!nh) return NULL;
    nh->size = size;
    nh->magic = _IDE_MAGIC;
    if (size > old) _IDE_CUR_HEAP += (size - old);
    else _IDE_CUR_HEAP -= (old - size);
    if (_IDE_TRACK_HEAP && _IDE_CUR_HEAP > _IDE_MAX_HEAP) _IDE_MAX_HEAP = _IDE_CUR_HEAP;
    return (void*)(nh + 1);
}

void _IDE_free(void* ptr) {
    if (!ptr) { _IDE_raw_free(ptr); return; }
    _IDE_HDR* h = ((_IDE_HDR*)ptr) - 1;
    if (h->magic != _IDE_MAGIC) {
        _IDE_raw_free(ptr);
        return;
    }
    if (_IDE_CUR_HEAP >= h->size) _IDE_CUR_HEAP -= h->size;
    else _IDE_CUR_HEAP = 0;
    h->magic = 0;
    _IDE_raw_free(h);
}

double _IDE_WALL_SECONDS() {
#ifdef _WIN32
    static LARGE_INTEGER freq;
    static int init = 0;
    LARGE_INTEGER now;
    if (!init) {
        QueryPerformanceFrequency(&freq);
        init = 1;
    }
    QueryPerformanceCounter(&now);
    return (double)now.QuadPart / (double)freq.QuadPart;
#elif defined(CLOCK_MONOTONIC)
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) == 0) {
        return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
    }
    return 0.0;
#else
    return (double)clock() / (double)CLOCKS_PER_SEC;
#endif
}

double _IDE_CPU_SECONDS() {
#ifdef _WIN32
    FILETIME create_time, exit_time, kernel_time, user_time;
    if (GetProcessTimes(GetCurrentProcess(), &create_time, &exit_time, &kernel_time, &user_time)) {
        ULARGE_INTEGER k, u;
        k.LowPart = kernel_time.dwLowDateTime;
        k.HighPart = kernel_time.dwHighDateTime;
        u.LowPart = user_time.dwLowDateTime;
        u.HighPart = user_time.dwHighDateTime;
        return (double)(k.QuadPart + u.QuadPart) / 10000000.0;
    }
    return 0.0;
#elif defined(CLOCK_PROCESS_CPUTIME_ID)
    struct timespec ts;
    if (clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &ts) == 0) {
        return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
    }
    return 0.0;
#else
    return (double)clock() / (double)CLOCKS_PER_SEC;
#endif
}

void _IDE_START() {
    if (!_IDE_IS_RUNNING) {
        _IDE_START_WALL = _IDE_WALL_SECONDS();
        _IDE_START_CPU = _IDE_CPU_SECONDS();
#ifdef _WIN32
        PROCESS_MEMORY_COUNTERS_EX pmc;
        if (GetProcessMemoryInfo(GetCurrentProcess(), (PROCESS_MEMORY_COUNTERS*)&pmc, sizeof(pmc))) {
            _IDE_BASE_WS = pmc.WorkingSetSize;
            _IDE_BASE_PRIV = pmc.PrivateUsage;
        }
#endif
        _IDE_HEAP_BASE = _IDE_CUR_HEAP;
        _IDE_MAX_HEAP = _IDE_CUR_HEAP;
        _IDE_TRACK_HEAP = 1;
        _IDE_IS_RUNNING = 1;
    }
}

void _IDE_PAUSE() {
    fflush(stdout);
    if (_IDE_IS_RUNNING) {
        double end_wall = _IDE_WALL_SECONDS();
        double end_cpu = _IDE_CPU_SECONDS();
        _IDE_TOTAL_TIME += (end_wall - _IDE_START_WALL);
        _IDE_TOTAL_CPU += (end_cpu - _IDE_START_CPU);
        _IDE_IS_RUNNING = 0;
    }
}

void _IDE_RESUME() {
    _IDE_START();
}

int _IDE_SCANF(const char* fmt, ...) {
    _IDE_PAUSE();
    va_list args;
    va_start(args, fmt);
    int r = vscanf(fmt, args);
    va_end(args);
    _IDE_RESUME();
    return r;
}

int _IDE_SCANF_S(const char* fmt, ...) {
    _IDE_PAUSE();
    va_list args;
    va_start(args, fmt);
#ifdef _MSC_VER
    int r = vscanf_s(fmt, args);
#else
    int r = vscanf(fmt, args);
#endif
    va_end(args);
    _IDE_RESUME();
    return r;
}

void _IDE_PRINT_RESULT() {
    _IDE_PAUSE();
    size_t code_heap_bytes = _IDE_MAX_HEAP >= _IDE_HEAP_BASE ? (_IDE_MAX_HEAP - _IDE_HEAP_BASE) : 0;
    double code_heap_kb = (double)code_heap_bytes / 1024.0;
    printf("\n==========================================\n");
    printf("   ALGORITHM TIME: %.9f seconds\n", _IDE_TOTAL_TIME);
    printf("   CPU TIME:       %.9f seconds\n", _IDE_TOTAL_CPU);
    printf("   STEPS:          %llu\n", (unsigned long long)_IDE_STEP_COUNT);
    printf("   CODE HEAP:      %.6f KB (%.0f bytes)\n", code_heap_kb, (double)code_heap_bytes);
    printf("   (User input time was excluded)\n");
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS_EX pmc;
    SIZE_T peak_ws = 0;
    SIZE_T base_ws = _IDE_BASE_WS;
    SIZE_T base_priv = _IDE_BASE_PRIV;
    if (GetProcessMemoryInfo(GetCurrentProcess(), (PROCESS_MEMORY_COUNTERS*)&pmc, sizeof(pmc))) {
        peak_ws = pmc.PeakWorkingSetSize;
        SIZE_T priv = pmc.PrivateUsage;
        double peak_mb = (double)peak_ws / (1024.0 * 1024.0);
        double delta_ws_kb = peak_ws >= base_ws ? (double)(peak_ws - base_ws) / 1024.0 : 0.0;
        double priv_mb = (double)priv / (1024.0 * 1024.0);
        double delta_priv_kb = priv >= base_priv ? (double)(priv - base_priv) / 1024.0 : 0.0;
        printf("   CODE MEMORY: %.6f KB (%.0f bytes)\n", delta_priv_kb, (double)(priv >= base_priv ? (priv - base_priv) : 0));
        printf("   PEAK WS:     %.2f MB (delta %.6f KB, %.0f bytes)\n", peak_mb, delta_ws_kb, (double)(peak_ws >= base_ws ? (peak_ws - base_ws) : 0));
        printf("   PRIVATE:     %.2f MB (delta %.6f KB, %.0f bytes)\n", priv_mb, delta_priv_kb, (double)(priv >= base_priv ? (priv - base_priv) : 0));
        if (_IDE_BENCHMARK) {
            printf("IDE_PEAK_MEM=%.0f\n", (double)peak_ws);
            printf("IDE_BASE_MEM=%.0f\n", (double)base_ws);
        }
    } else {
        printf("   CODE MEMORY: N/A\n");
        printf("   PEAK WS:     N/A\n");
        printf("   PRIVATE:     N/A\n");
    }
#else
    printf("   CODE MEMORY: N/A (non-Windows)\n");
    printf("   PEAK WS:     N/A (non-Windows)\n");
    printf("   PRIVATE:     N/A (non-Windows)\n");
#endif
    printf("==========================================\n");
    if (_IDE_BENCHMARK) {
        printf("IDE_TIME=%.9f\n", _IDE_TOTAL_TIME);
        printf("IDE_CPU=%.9f\n", _IDE_TOTAL_CPU);
        printf("IDE_STEPS=%llu\n", (unsigned long long)_IDE_STEP_COUNT);
    }
#ifdef _WIN32
    if (!_IDE_BENCHMARK) {
        system("pause");
    }
#endif
}
// --------------------------

#ifndef __cplusplus
#define malloc(size) _IDE_malloc(size)
#define calloc(n, s) _IDE_calloc(n, s)
#define realloc(p, s) _IDE_realloc(p, s)
#define free(p) _IDE_free(p)
#endif
"""
        else:
            timer_header = r"""
#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <time.h>
#include <new>
#ifdef _WIN32
#include <windows.h>
#include <psapi.h>
#endif

// --- IDE INJECTED TIMER ---
double _IDE_TOTAL_TIME = 0.0;  // wall time (no input)
double _IDE_TOTAL_CPU = 0.0;   // cpu time
int _IDE_IS_RUNNING = 0;
int _IDE_BENCHMARK = 0;

double _IDE_START_WALL = 0.0;
double _IDE_START_CPU = 0.0;

unsigned long long _IDE_STEP_COUNT = 0;

#define _IDE_MAGIC 0xC0DEC0DEu
typedef struct { size_t size; unsigned int magic; } _IDE_HDR;
size_t _IDE_CUR_HEAP = 0;
size_t _IDE_MAX_HEAP = 0;
size_t _IDE_HEAP_BASE = 0;
int _IDE_TRACK_HEAP = 0;

#ifndef IDE_STEP
#define IDE_STEP() do { _IDE_STEP_COUNT++; } while (0)
#endif
#ifndef IDE_STEPN
#define IDE_STEPN(n) do { _IDE_STEP_COUNT += (unsigned long long)(n); } while (0)
#endif

#ifdef _WIN32
SIZE_T _IDE_BASE_WS = 0;
SIZE_T _IDE_BASE_PRIV = 0;
#endif

static void* _IDE_raw_malloc(size_t size) { return malloc(size); }
static void* _IDE_raw_realloc(void* ptr, size_t size) { return realloc(ptr, size); }
static void _IDE_raw_free(void* ptr) { free(ptr); }

void* _IDE_malloc(size_t size) {
    size_t total = size + sizeof(_IDE_HDR);
    _IDE_HDR* h = (_IDE_HDR*)_IDE_raw_malloc(total);
    if (!h) return NULL;
    h->size = size;
    h->magic = _IDE_MAGIC;
    _IDE_CUR_HEAP += size;
    if (_IDE_TRACK_HEAP && _IDE_CUR_HEAP > _IDE_MAX_HEAP) _IDE_MAX_HEAP = _IDE_CUR_HEAP;
    return (void*)(h + 1);
}

void* _IDE_calloc(size_t n, size_t size) {
    size_t bytes = n * size;
    void* p = _IDE_malloc(bytes);
    if (p) memset(p, 0, bytes);
    return p;
}

void* _IDE_realloc(void* ptr, size_t size) {
    if (!ptr) return _IDE_malloc(size);
    if (size == 0) { _IDE_raw_free(ptr); return NULL; }
    _IDE_HDR* h = ((_IDE_HDR*)ptr) - 1;
    if (h->magic != _IDE_MAGIC) {
        return _IDE_raw_realloc(ptr, size);
    }
    size_t old = h->size;
    size_t total = size + sizeof(_IDE_HDR);
    _IDE_HDR* nh = (_IDE_HDR*)_IDE_raw_realloc(h, total);
    if (!nh) return NULL;
    nh->size = size;
    nh->magic = _IDE_MAGIC;
    if (size > old) _IDE_CUR_HEAP += (size - old);
    else _IDE_CUR_HEAP -= (old - size);
    if (_IDE_TRACK_HEAP && _IDE_CUR_HEAP > _IDE_MAX_HEAP) _IDE_MAX_HEAP = _IDE_CUR_HEAP;
    return (void*)(nh + 1);
}

void _IDE_free(void* ptr) {
    if (!ptr) { _IDE_raw_free(ptr); return; }
    _IDE_HDR* h = ((_IDE_HDR*)ptr) - 1;
    if (h->magic != _IDE_MAGIC) {
        _IDE_raw_free(ptr);
        return;
    }
    if (_IDE_CUR_HEAP >= h->size) _IDE_CUR_HEAP -= h->size;
    else _IDE_CUR_HEAP = 0;
    h->magic = 0;
    _IDE_raw_free(h);
}

void* operator new(std::size_t size) {
    void* p = _IDE_malloc(size);
    if (!p) throw std::bad_alloc();
    return p;
}

void* operator new[](std::size_t size) {
    void* p = _IDE_malloc(size);
    if (!p) throw std::bad_alloc();
    return p;
}

void operator delete(void* p) noexcept { _IDE_free(p); }
void operator delete[](void* p) noexcept { _IDE_free(p); }

void* operator new(std::size_t size, const std::nothrow_t&) noexcept { return _IDE_malloc(size); }
void* operator new[](std::size_t size, const std::nothrow_t&) noexcept { return _IDE_malloc(size); }
void operator delete(void* p, const std::nothrow_t&) noexcept { _IDE_free(p); }
void operator delete[](void* p, const std::nothrow_t&) noexcept { _IDE_free(p); }

double _IDE_WALL_SECONDS() {
#ifdef _WIN32
    static LARGE_INTEGER freq;
    static int init = 0;
    LARGE_INTEGER now;
    if (!init) {
        QueryPerformanceFrequency(&freq);
        init = 1;
    }
    QueryPerformanceCounter(&now);
    return (double)now.QuadPart / (double)freq.QuadPart;
#elif defined(CLOCK_MONOTONIC)
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) == 0) {
        return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
    }
    return 0.0;
#else
    return (double)clock() / (double)CLOCKS_PER_SEC;
#endif
}

double _IDE_CPU_SECONDS() {
#ifdef _WIN32
    FILETIME create_time, exit_time, kernel_time, user_time;
    if (GetProcessTimes(GetCurrentProcess(), &create_time, &exit_time, &kernel_time, &user_time)) {
        ULARGE_INTEGER k, u;
        k.LowPart = kernel_time.dwLowDateTime;
        k.HighPart = kernel_time.dwHighDateTime;
        u.LowPart = user_time.dwLowDateTime;
        u.HighPart = user_time.dwHighDateTime;
        return (double)(k.QuadPart + u.QuadPart) / 10000000.0;
    }
    return 0.0;
#elif defined(CLOCK_PROCESS_CPUTIME_ID)
    struct timespec ts;
    if (clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &ts) == 0) {
        return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
    }
    return 0.0;
#else
    return (double)clock() / (double)CLOCKS_PER_SEC;
#endif
}

void _IDE_START() {
    if (!_IDE_IS_RUNNING) {
        _IDE_START_WALL = _IDE_WALL_SECONDS();
        _IDE_START_CPU = _IDE_CPU_SECONDS();
#ifdef _WIN32
        PROCESS_MEMORY_COUNTERS_EX pmc;
        if (GetProcessMemoryInfo(GetCurrentProcess(), (PROCESS_MEMORY_COUNTERS*)&pmc, sizeof(pmc))) {
            _IDE_BASE_WS = pmc.WorkingSetSize;
            _IDE_BASE_PRIV = pmc.PrivateUsage;
        }
#endif
        _IDE_HEAP_BASE = _IDE_CUR_HEAP;
        _IDE_MAX_HEAP = _IDE_CUR_HEAP;
        _IDE_TRACK_HEAP = 1;
        _IDE_IS_RUNNING = 1;
    }
}

void _IDE_PAUSE() {
    fflush(stdout);
    std::cout.flush();
    if (_IDE_IS_RUNNING) {
        double end_wall = _IDE_WALL_SECONDS();
        double end_cpu = _IDE_CPU_SECONDS();
        _IDE_TOTAL_TIME += (end_wall - _IDE_START_WALL);
        _IDE_TOTAL_CPU += (end_cpu - _IDE_START_CPU);
        _IDE_IS_RUNNING = 0;
    }
}

void _IDE_RESUME() {
    _IDE_START();
}

int _IDE_SCANF(const char* fmt, ...) {
    _IDE_PAUSE();
    va_list args;
    va_start(args, fmt);
    int r = vscanf(fmt, args);
    va_end(args);
    _IDE_RESUME();
    return r;
}

int _IDE_SCANF_S(const char* fmt, ...) {
    _IDE_PAUSE();
    va_list args;
    va_start(args, fmt);
#ifdef _MSC_VER
    int r = vscanf_s(fmt, args);
#else
    int r = vscanf(fmt, args);
#endif
    va_end(args);
    _IDE_RESUME();
    return r;
}

void _IDE_PRINT_RESULT() {
    _IDE_PAUSE();
    size_t code_heap_bytes = _IDE_MAX_HEAP >= _IDE_HEAP_BASE ? (_IDE_MAX_HEAP - _IDE_HEAP_BASE) : 0;
    double code_heap_kb = (double)code_heap_bytes / 1024.0;
    printf("\n==========================================\n");
    printf("   ALGORITHM TIME: %.9f seconds\n", _IDE_TOTAL_TIME);
    printf("   CPU TIME:       %.9f seconds\n", _IDE_TOTAL_CPU);
    printf("   STEPS:          %llu\n", (unsigned long long)_IDE_STEP_COUNT);
    printf("   CODE HEAP:      %.6f KB (%.0f bytes)\n", code_heap_kb, (double)code_heap_bytes);
    printf("   (User input time was excluded)\n");
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS_EX pmc;
    SIZE_T peak_ws = 0;
    SIZE_T base_ws = _IDE_BASE_WS;
    SIZE_T base_priv = _IDE_BASE_PRIV;
    if (GetProcessMemoryInfo(GetCurrentProcess(), (PROCESS_MEMORY_COUNTERS*)&pmc, sizeof(pmc))) {
        peak_ws = pmc.PeakWorkingSetSize;
        SIZE_T priv = pmc.PrivateUsage;
        double peak_mb = (double)peak_ws / (1024.0 * 1024.0);
        double delta_ws_kb = peak_ws >= base_ws ? (double)(peak_ws - base_ws) / 1024.0 : 0.0;
        double priv_mb = (double)priv / (1024.0 * 1024.0);
        double delta_priv_kb = priv >= base_priv ? (double)(priv - base_priv) / 1024.0 : 0.0;
        printf("   CODE MEMORY: %.6f KB (%.0f bytes)\n", delta_priv_kb, (double)(priv >= base_priv ? (priv - base_priv) : 0));
        printf("   PEAK WS:     %.2f MB (delta %.6f KB, %.0f bytes)\n", peak_mb, delta_ws_kb, (double)(peak_ws >= base_ws ? (peak_ws - base_ws) : 0));
        printf("   PRIVATE:     %.2f MB (delta %.6f KB, %.0f bytes)\n", priv_mb, delta_priv_kb, (double)(priv >= base_priv ? (priv - base_priv) : 0));
        if (_IDE_BENCHMARK) {
            printf("IDE_PEAK_MEM=%.0f\n", (double)peak_ws);
            printf("IDE_BASE_MEM=%.0f\n", (double)base_ws);
        }
    } else {
        printf("   CODE MEMORY: N/A\n");
        printf("   PEAK WS:     N/A\n");
        printf("   PRIVATE:     N/A\n");
    }
#else
    printf("   CODE MEMORY: N/A (non-Windows)\n");
    printf("   PEAK WS:     N/A (non-Windows)\n");
    printf("   PRIVATE:     N/A (non-Windows)\n");
#endif
    printf("==========================================\n");
    if (_IDE_BENCHMARK) {
        printf("IDE_TIME=%.9f\n", _IDE_TOTAL_TIME);
        printf("IDE_CPU=%.9f\n", _IDE_TOTAL_CPU);
        printf("IDE_STEPS=%llu\n", (unsigned long long)_IDE_STEP_COUNT);
    }
#ifdef _WIN32
    if (!_IDE_BENCHMARK) {
        system("pause");
    }
#endif
}
// --------------------------
"""

        code = user_code
        wrap = lambda m: f"_IDE_PAUSE(); {m.group(0)} _IDE_RESUME();"

        code = self._replace_in_code(code, r"\bscanf_s\b", "_IDE_SCANF_S", flags=0)
        code = self._replace_in_code(code, r"\bscanf\b", "_IDE_SCANF", flags=0)

        patterns = [
            r"\bstd::cin\s*>>.*?;|\bcin\s*>>.*?;",
            r"\bstd::getline\s*\(.*?\)\s*;|\bgetline\s*\(.*?\)\s*;",
            r"\bfgets\s*\(.*?\)\s*;",
            r"\bgetchar\s*\(\s*\)\s*;",
            r"\bgetc\s*\(.*?\)\s*;",
            r"\bstd::cin\s*\.\s*get\s*\(.*?\)\s*;|\bcin\s*\.\s*get\s*\(.*?\)\s*;",
            r"\bstd::cin\s*\.\s*getline\s*\(.*?\)\s*;|\bcin\s*\.\s*getline\s*\(.*?\)\s*;",
        ]

        for pattern in patterns:
            code = self._replace_in_code(code, pattern, wrap, flags=re.DOTALL)

        pattern = r"\b(int|void)\s+main\s*\((.*?)\)"
        match = self._find_code_match(code, pattern, flags=re.DOTALL)
        if not match:
            return None

        return_type = match.group(1)
        params = match.group(2).strip()
        has_args = bool(params) and params != "void"
        wrapper_sig = "int main(int argc, char** argv)" if has_args else "int main()"
        call_expr = "user_logic(argc, argv)" if has_args else "user_logic()"
        signature = code[match.start():match.end()]
        new_signature = re.sub(pattern, r"\1 user_logic(\2)", signature, count=1, flags=re.DOTALL)
        code = code[:match.start()] + new_signature + code[match.end():]

        if return_type == "void":
            wrapper_main = """
{sig} {{
    const char* ide_bench = getenv("IDE_BENCHMARK");
    if (ide_bench && ide_bench[0] == '1') {{
        _IDE_BENCHMARK = 1;
    }}
    _IDE_START();
    {call};
    _IDE_PRINT_RESULT();
    return 0;
}}
""".format(sig=wrapper_sig, call=call_expr)
        else:
            wrapper_main = """
{sig} {{
    const char* ide_bench = getenv("IDE_BENCHMARK");
    if (ide_bench && ide_bench[0] == '1') {{
        _IDE_BENCHMARK = 1;
    }}
    _IDE_START();
    int ret = {call};
    _IDE_PRINT_RESULT();
    return ret;
}}
""".format(sig=wrapper_sig, call=call_expr)

        return timer_header + code + wrapper_main

    # --- EXECUTION ---

    def run_thread(self):
        threading.Thread(target=self.compile_and_run, daemon=True).start()

    def compile_and_run(self):
        if not self.check_compiler():
            return

        self.btn_run.config(state=tk.DISABLED, text="Compiling...")
        try:
            if not self.compile_code():
                return

            if self.benchmark_var.get():
                self.run_benchmark()
            else:
                self.run_once()
        finally:
            self.btn_run.config(state=tk.NORMAL, text=RUN_BUTTON_TEXT)

    def compile_code(self):
        raw_code = self.editor_left.get(1.0, tk.END)
        return self.compile_code_from_text(raw_code, "left")

    def compile_code_from_text(self, raw_code, side):
        final_code = self.inject_smart_timer(raw_code)

        if not final_code:
            messagebox.showerror("Error", f"Could not parse main() function in {side} editor.")
            self.lbl_status.config(text="Parse Failed")
            return False

        try:
            self.autosave()
        except Exception:
            pass

        source_path = self.get_temp_source_path(side)
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(final_code)

        try:
            cmd = self.build_compile_command(source_path, self.get_temp_exe_path(side))
        except Exception as e:
            self.lbl_status.config(text="Compiler Missing")
            messagebox.showerror("Compiler Error", str(e))
            return False
        self.lbl_status.config(text=f"Compiling {side}...")
        res = subprocess.run(cmd, capture_output=True, text=True)

        if res.returncode != 0:
            self.lbl_status.config(text="Compilation Failed")
            messagebox.showerror(f"Compilation Error ({side})", res.stderr or res.stdout)
            return False

        return True

    def build_compile_command(self, source_path, exe_path):
        compiler = self.get_active_compiler()
        if not compiler:
            raise RuntimeError("Compiler not available for selected language.")

        lang = self.language_var.get()
        if lang == "C":
            cmd = [compiler, source_path, "-o", exe_path, "-std=c11"]
            if self.c_compiler_is_cpp_driver:
                cmd.insert(1, "-x")
                cmd.insert(2, "c")
            if os.name != "nt":
                cmd.append("-lm")
        else:
            cmd = [compiler, source_path, "-o", exe_path, "-std=c++17"]

        if os.name == "nt":
            cmd.append("-lpsapi")

        return cmd

    def get_temp_source_path(self, side):
        if self.language_var.get() == "C":
            return TEMP_SOURCE_FILE_C if side == "left" else TEMP_SOURCE_FILE_C_RIGHT
        return TEMP_SOURCE_FILE_CPP if side == "left" else TEMP_SOURCE_FILE_CPP_RIGHT

    def get_temp_exe_path(self, side):
        return TEMP_EXE_FILE if side == "left" else TEMP_EXE_FILE_RIGHT

    def get_source_extension(self):
        return ".c" if self.language_var.get() == "C" else ".cpp"

    def get_active_compiler(self):
        if self.language_var.get() == "C":
            return self.compiler_cmd_c
        return self.compiler_cmd_cpp

    def run_once(self):
        self.lbl_status.config(text="Running...")
        proc = self.launch_process(self.get_temp_exe_path("left"))
        if proc is None:
            self.lbl_status.config(text="Run Failed")
            return

        self.running_process = proc

        def wait_for_exit():
            try:
                proc.wait()
            except Exception:
                return
            self.root.after(0, lambda: self.lbl_status.config(text="Done"))

        threading.Thread(target=wait_for_exit, daemon=True).start()

    def launch_process(self, exe_path):
        try:
            if os.name == "nt":
                flags = subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, "CREATE_NEW_CONSOLE") else 0
                return subprocess.Popen([exe_path], creationflags=flags)
            if shutil.which("xterm"):
                return subprocess.Popen(["xterm", "-e", exe_path])
            return subprocess.Popen([exe_path])
        except Exception as e:
            messagebox.showerror("Run Error", str(e))
            return None

    def code_uses_input(self, code):
        patterns = [
            r"\bscanf_s\s*\(",
            r"\bscanf\s*\(",
            r"\bstd::cin\s*>>",
            r"\bcin\s*>>",
            r"\bstd::getline\s*\(",
            r"\bgetline\s*\(",
            r"\bfgets\s*\(",
            r"\bgetchar\s*\(",
            r"\bgetc\s*\(",
            r"\bstd::cin\s*\.\s*get",
            r"\bcin\s*\.\s*get",
            r"\bstd::cin\s*\.\s*getline",
            r"\bcin\s*\.\s*getline",
        ]
        for pattern in patterns:
            if self._find_code_match(code, pattern, flags=re.DOTALL):
                return True
        return False

    def run_benchmark(self):
        raw_code = self.editor_left.get(1.0, tk.END)
        if self.code_uses_input(raw_code):
            proceed = messagebox.askyesno(
                "Benchmark Warning",
                "Benchmark mode runs non-interactively. Programs waiting for input may hang. Continue?",
            )
            if not proceed:
                self.lbl_status.config(text="Benchmark Canceled")
                return

        try:
            runs = int(self.benchmark_runs_var.get())
        except Exception:
            runs = BENCHMARK_DEFAULT_RUNS

        if runs < 1:
            runs = BENCHMARK_DEFAULT_RUNS

        env = os.environ.copy()
        env["IDE_BENCHMARK"] = "1"

        times = []
        cpu_times = []
        mems = []
        steps = []

        for i in range(runs):
            self.lbl_status.config(text=f"Benchmark {i + 1}/{runs}...")
            res = subprocess.run(
                [self.get_temp_exe_path("left")],
                input="",
                capture_output=True,
                text=True,
                env=env,
            )

            if res.returncode != 0:
                self.lbl_status.config(text="Benchmark Failed")
                messagebox.showerror("Runtime Error", res.stderr or res.stdout)
                return

            t, mem, cpu, step_count = self.parse_ide_metrics(res.stdout + res.stderr)
            if t is None:
                self.lbl_status.config(text="Benchmark Failed")
                messagebox.showerror(
                    "Benchmark Error",
                    "Could not parse timing output. Ensure the program runs correctly.",
                )
                return

            times.append(t)
            if cpu is not None:
                cpu_times.append(cpu)
            if mem is not None:
                mems.append(mem)
            if step_count is not None:
                steps.append(step_count)

        mean_t = statistics.mean(times)
        stdev_t = statistics.pstdev(times) if len(times) > 1 else 0.0

        msg = f"Runs: {runs}\nMean time: {mean_t:.9f} s\nStd dev: {stdev_t:.9f} s"
        if cpu_times:
            mean_cpu = statistics.mean(cpu_times)
            stdev_cpu = statistics.pstdev(cpu_times) if len(cpu_times) > 1 else 0.0
            msg += f"\nMean CPU time: {mean_cpu:.9f} s\nStd dev CPU: {stdev_cpu:.9f} s"
        if mems:
            mean_mem = statistics.mean(mems) / (1024.0 * 1024.0)
            stdev_mem = statistics.pstdev(mems) / (1024.0 * 1024.0) if len(mems) > 1 else 0.0
            msg += f"\nMean memory delta: {mean_mem:.2f} MB\nStd dev memory delta: {stdev_mem:.2f} MB"
        if steps:
            mean_steps = statistics.mean(steps)
            stdev_steps = statistics.pstdev(steps) if len(steps) > 1 else 0.0
            msg += f"\nMean steps: {mean_steps:.0f}\nMax steps: {max(steps)}\nStd dev steps: {stdev_steps:.0f}"

        messagebox.showinfo("Benchmark Results", msg)
        self.lbl_status.config(text="Benchmark Done")

    def parse_ide_metrics(self, output):
        time_match = re.search(r"IDE_TIME=([0-9.]+)", output)
        cpu_match = re.search(r"IDE_CPU=([0-9.]+)", output)
        mem_match = re.search(r"IDE_PEAK_MEM=([0-9.]+)", output)
        base_match = re.search(r"IDE_BASE_MEM=([0-9.]+)", output)
        steps_match = re.search(r"IDE_STEPS=([0-9]+)", output)
        time_val = float(time_match.group(1)) if time_match else None
        cpu_val = float(cpu_match.group(1)) if cpu_match else None
        steps_val = int(steps_match.group(1)) if steps_match else None
        if mem_match:
            peak_val = float(mem_match.group(1))
            if base_match:
                base_val = float(base_match.group(1))
                mem_val = max(0.0, peak_val - base_val)
            else:
                mem_val = peak_val
        else:
            mem_val = None
        return time_val, mem_val, cpu_val, steps_val

    def run_complexity_thread(self, n_text, template_text):
        threading.Thread(
            target=self.run_complexity,
            args=(n_text, template_text),
            daemon=True,
        ).start()

    def run_complexity(self, n_text, template_text):
        if not self.check_compiler():
            return

        n_values = [
            int(v)
            for v in re.split(r"[ ,]+", n_text.strip())
            if v.strip().isdigit()
        ]
        n_values = [n for n in n_values if n > 0]

        if not n_values:
            messagebox.showerror("Complexity Error", "Please enter at least one positive N value.")
            return

        if "{N}" not in template_text:
            messagebox.showerror("Complexity Error", "Input template must include {N} placeholder.")
            return

        try:
            runs_per_n = int(self.complexity_runs_var.get())
        except Exception:
            runs_per_n = 1

        if runs_per_n < 1:
            runs_per_n = 1

        self.btn_run.config(state=tk.DISABLED, text="Running...")
        try:
            if not self.compile_code():
                return

            env = os.environ.copy()
            env["IDE_BENCHMARK"] = "1"

            times = []
            mems = []
            steps = []
            for n in n_values:
                per_times = []
                per_mems = []
                per_steps = []
                for i in range(runs_per_n):
                    self.lbl_status.config(text=f"Complexity N={n} ({i + 1}/{runs_per_n})")
                    input_data = template_text.replace("{N}", str(n))
                    res = subprocess.run(
                        [self.get_temp_exe_path("left")],
                        input=input_data,
                        capture_output=True,
                        text=True,
                        env=env,
                    )

                    if res.returncode != 0:
                        self.lbl_status.config(text="Complexity Failed")
                        messagebox.showerror("Runtime Error", res.stderr or res.stdout)
                        return

                    t, mem, _, step_count = self.parse_ide_metrics(res.stdout + res.stderr)
                    if t is None:
                        self.lbl_status.config(text="Complexity Failed")
                        messagebox.showerror(
                            "Complexity Error",
                            "Could not parse timing output. Ensure the program runs correctly.",
                        )
                        return

                    per_times.append(t)
                    if mem is not None:
                        per_mems.append(mem)
                    if step_count is not None:
                        per_steps.append(step_count)

                times.append(statistics.mean(per_times))
                if per_mems:
                    mems.append(statistics.mean(per_mems))
                else:
                    mems.append(None)
                if per_steps:
                    steps.append(max(per_steps))
                else:
                    steps.append(None)

            best_fit = self.estimate_complexity(n_values, times)
            self.update_complexity_label(best_fit)
            self.show_complexity_result(n_values, times, mems, steps, best_fit)
            self.lbl_status.config(text="Complexity Done")
        finally:
            self.btn_run.config(state=tk.NORMAL, text=RUN_BUTTON_TEXT)

    def open_complexity_window(self):
        if self._complexity_window and self._complexity_window.winfo_exists():
            self._complexity_window.lift()
            return

        win = tk.Toplevel(self.root)
        win.title("Complexity Estimator")
        win.geometry("650x500")
        self._complexity_window = win

        lbl_n = tk.Label(win, text="Input sizes (comma-separated N values):")
        lbl_n.pack(anchor="w", padx=10, pady=(10, 0))

        entry_n = tk.Entry(win, font=("Segoe UI", 10))
        entry_n.insert(0, "100, 200, 500, 1000")
        entry_n.pack(fill=tk.X, padx=10)

        lbl_runs = tk.Label(win, text="Runs per N:")
        lbl_runs.pack(anchor="w", padx=10, pady=(10, 0))

        entry_runs = tk.Entry(win, textvariable=self.complexity_runs_var, width=6, font=("Segoe UI", 10))
        entry_runs.pack(anchor="w", padx=10)

        lbl_template = tk.Label(win, text="Input template (use {N} placeholder):")
        lbl_template.pack(anchor="w", padx=10, pady=(10, 0))

        template_text = scrolledtext.ScrolledText(win, height=8, font=("Consolas", 11))
        template_text.insert(tk.END, "{N}\n")
        template_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        btn_run = tk.Button(
            win,
            text="Run Complexity",
            command=lambda: self.run_complexity_thread(entry_n.get(), template_text.get("1.0", tk.END)),
            font=("Segoe UI", 10, "bold"),
            width=16,
        )
        btn_run.pack(pady=10)

    def estimate_complexity(self, n_values, times):
        if not n_values or not times or len(n_values) != len(times):
            return None

        models = {
            "O(1)": [1.0 for _ in n_values],
            "O(n)": [float(n) for n in n_values],
            "O(n log n)": [float(n) * math.log2(n) if n > 1 else 0.0 for n in n_values],
            "O(n^2)": [float(n * n) for n in n_values],
        }

        best_fit = None
        best_sse = None

        for name, values in models.items():
            denom = sum(v * v for v in values)
            if denom <= 0:
                sse = float("inf")
            else:
                scale = sum(t * v for t, v in zip(times, values)) / denom
                preds = [scale * v for v in values]
                sse = sum((t - p) ** 2 for t, p in zip(times, preds))

            if best_sse is None or sse < best_sse:
                best_sse = sse
                best_fit = name

        return best_fit

    def update_complexity_label(self, best_fit):
        if best_fit:
            self.lbl_complexity.config(text=f"Complexity: {best_fit}")
        else:
            self.lbl_complexity.config(text="Complexity: N/A")

    def plot_complexity(self, n_values, times):
        win = tk.Toplevel(self.root)
        win.title("Complexity Plot")
        theme = THEMES.get(self.theme_var.get(), THEMES["Dark"])
        canvas = tk.Canvas(win, width=800, height=500, bg=theme["editor_bg"], highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.draw_complexity_plot(canvas, n_values, times)

    def draw_complexity_plot(self, canvas, n_values, times):
        theme = THEMES.get(self.theme_var.get(), THEMES["Dark"])
        width = int(canvas["width"])
        height = int(canvas["height"])
        margin = 60

        x_min, x_max = min(n_values), max(n_values)
        y_max = max(times) if times else 1.0
        if y_max <= 0:
            y_max = 1.0

        def map_point(x, y):
            x_norm = 0.5 if x_max == x_min else (x - x_min) / (x_max - x_min)
            y_norm = y / y_max
            px = margin + x_norm * (width - 2 * margin)
            py = height - margin - y_norm * (height - 2 * margin)
            return px, py

        axis_color = theme["toolbar_fg"]
        canvas.create_line(margin, height - margin, width - margin, height - margin, fill=axis_color)
        canvas.create_line(margin, height - margin, margin, margin, fill=axis_color)

        points = [map_point(n, t) for n, t in zip(n_values, times)]
        for i in range(len(points) - 1):
            canvas.create_line(*points[i], *points[i + 1], fill="#ff9800", width=2)
        for px, py in points:
            canvas.create_oval(px - 3, py - 3, px + 3, py + 3, fill="#ff9800", outline="")

        models = {
            "O(1)": [1.0 for _ in n_values],
            "O(n)": [float(n) for n in n_values],
            "O(n log n)": [float(n) * math.log2(n) if n > 1 else 0.0 for n in n_values],
            "O(n^2)": [float(n * n) for n in n_values],
        }

        colors = {
            "O(1)": "#9c27b0",
            "O(n)": "#4caf50",
            "O(n log n)": "#2196f3",
            "O(n^2)": "#e91e63",
        }

        best_fit = None
        best_sse = None

        for name, values in models.items():
            denom = sum(v * v for v in values)
            if denom <= 0:
                preds = [0.0 for _ in values]
                sse = float("inf")
            else:
                scale = sum(t * v for t, v in zip(times, values)) / denom
                preds = [scale * v for v in values]
                sse = sum((t - p) ** 2 for t, p in zip(times, preds))

            if best_sse is None or sse < best_sse:
                best_sse = sse
                best_fit = name

            pred_points = [map_point(n, p) for n, p in zip(n_values, preds)]
            for i in range(len(pred_points) - 1):
                canvas.create_line(
                    *pred_points[i],
                    *pred_points[i + 1],
                    fill=colors[name],
                    width=1,
                    dash=(4, 2),
                )

        canvas.create_text(margin, margin / 2, text=f"Best fit (rough): {best_fit}", fill=axis_color, anchor="w")

        legend_y = height - margin + 20
        legend_items = [
            ("Measured", "#ff9800"),
            ("O(1)", colors["O(1)"]),
            ("O(n)", colors["O(n)"]),
            ("O(n log n)", colors["O(n log n)"]),
            ("O(n^2)", colors["O(n^2)"]),
        ]

        x_cursor = margin
        for label, color in legend_items:
            canvas.create_rectangle(x_cursor, legend_y, x_cursor + 12, legend_y + 12, fill=color, outline="")
            canvas.create_text(x_cursor + 18, legend_y + 6, text=label, fill=axis_color, anchor="w")
            x_cursor += 120

    def show_complexity_result(self, n_values, times, mems, steps, best_fit):
        win = tk.Toplevel(self.root)
        win.title("Complexity Result")
        win.geometry("1000x600")

        theme = THEMES.get(self.theme_var.get(), THEMES["Dark"])
        win.configure(bg=theme["root_bg"])

        pane = tk.PanedWindow(win, orient=tk.HORIZONTAL, sashwidth=6, bg=theme["root_bg"])
        pane.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(pane, bg=theme["root_bg"])
        right = tk.Frame(pane, bg=theme["root_bg"])
        pane.add(left, stretch="always")
        pane.add(right, stretch="always")

        canvas = tk.Canvas(left, width=700, height=520, bg=theme["editor_bg"], highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.draw_complexity_plot(canvas, n_values, times)

        title = tk.Label(right, text=f"Estimated complexity: {best_fit or 'Unknown'}", font=("Segoe UI", 12, "bold"),
                         bg=theme["root_bg"], fg=theme["toolbar_fg"])
        title.pack(anchor="w", padx=10, pady=(10, 6))

        info = scrolledtext.ScrolledText(right, font=("Consolas", 10), height=20)
        info.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        lines = []
        for i, n in enumerate(n_values):
            row = f"N={n}: {times[i]:.9f}s"
            if mems[i] is not None:
                row += f", mem delta {mems[i] / (1024.0 * 1024.0):.2f} MB"
            if steps and steps[i] is not None:
                row += f", worst steps {steps[i]}"
            lines.append(row)
        header = "Timing by N:"
        if steps and any(s is not None for s in steps):
            header += "\n(steps shown are worst observed per N)"
        info.insert(tk.END, header + "\n" + "\n".join(lines))
        info.configure(state=tk.DISABLED)

    def kill_process(self):
        killed = False
        if self.running_process and self.running_process.poll() is None:
            try:
                self.running_process.terminate()
                killed = True
            except Exception:
                try:
                    self.running_process.kill()
                    killed = True
                except Exception:
                    pass

        for proc in list(self.running_processes):
            if proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass

        self.running_process = None
        self.running_processes = []
        if killed:
            self.lbl_status.config(text="Process Killed")

    def on_benchmark_toggle(self):
        if self.benchmark_var.get():
            self.lbl_status.config(text="Benchmark Mode Enabled")
        else:
            self.lbl_status.config(text="Ready")

    def on_editor_modified(self, editor):
        if editor.edit_modified():
            editor.edit_modified(False)
            self.schedule_autosave()
            self.schedule_highlight(editor)

    def schedule_autosave(self):
        if self._autosave_job:
            self.root.after_cancel(self._autosave_job)
        self._autosave_job = self.root.after(600, self.autosave)

    def autosave(self):
        self._autosave_job = None
        name = self.sanitize_project_name(self.project_name_var.get())
        ext = self.get_source_extension()
        left_path = os.path.join(PROJECTS_DIR, f"{name}{ext}")
        with open(left_path, "w", encoding="utf-8") as f:
            f.write(self.editor_left.get(1.0, tk.END))

        if self.split_var.get():
            right_path = os.path.join(PROJECTS_DIR, f"{name}_right{ext}")
            with open(right_path, "w", encoding="utf-8") as f:
                f.write(self.editor_right.get(1.0, tk.END))
            self.lbl_status.config(text=f"Auto-saved: {name}{ext} + {name}_right{ext}")
        else:
            self.lbl_status.config(text=f"Auto-saved: {name}{ext}")

    def on_project_name_change(self, *args):
        self.schedule_autosave()

    def on_language_change(self, *args):
        self.schedule_autosave()
        self.check_compiler()

    def toggle_split(self):
        panes = self.editor_pane.panes()
        if self.split_var.get():
            if str(self.right_frame) not in panes:
                self.editor_pane.add(self.right_frame, stretch="always")
        else:
            if str(self.right_frame) in panes:
                self.editor_pane.forget(self.right_frame)

    def build_snippet_sidebar(self):
        for child in self.snippet_frame.winfo_children():
            child.destroy()

        title = tk.Label(self.snippet_frame, text="Snippets", font=("Segoe UI", 11, "bold"))
        title.pack(anchor="w", padx=8, pady=(8, 4))

        list_frame = tk.Frame(self.snippet_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8)

        self.snippet_list = tk.Listbox(list_frame, height=12, activestyle="dotbox")
        scroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.snippet_list.yview)
        self.snippet_list.configure(yscrollcommand=scroll.set)
        self.snippet_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        for name in SNIPPETS.keys():
            self.snippet_list.insert(tk.END, name)

        self.snippet_list.bind("<Double-Button-1>", lambda e: self.insert_snippet())

        btn = tk.Button(
            self.snippet_frame,
            text="Insert Snippet",
            command=self.insert_snippet,
            font=("Segoe UI", 9, "bold"),
        )
        btn.pack(fill=tk.X, padx=8, pady=(6, 8))

    def set_active_editor(self, editor):
        self.active_editor = editor

    def get_active_editor(self):
        return self.active_editor if self.active_editor else self.editor_left

    def insert_snippet(self):
        if not hasattr(self, "snippet_list"):
            return
        selection = self.snippet_list.curselection()
        if not selection:
            messagebox.showinfo("Snippet", "Select a snippet to insert.")
            return

        name = self.snippet_list.get(selection[0])
        lang = self.language_var.get()
        snippet = SNIPPETS.get(name, {}).get(lang)
        if not snippet:
            messagebox.showwarning("Snippet", f"No {lang} snippet for '{name}'.")
            return

        editor = self.get_active_editor()
        editor.insert(tk.INSERT, snippet)
        editor.see(tk.INSERT)
        self.schedule_highlight(editor)

    def open_race_dialog(self):
        if not self.split_var.get():
            self.split_var.set(True)
            self.toggle_split()

        win = tk.Toplevel(self.root)
        win.title("Race Mode")
        win.geometry("600x400")

        lbl = tk.Label(win, text="Input to feed both programs (same input for left and right):")
        lbl.pack(anchor="w", padx=10, pady=(10, 0))

        input_box = scrolledtext.ScrolledText(win, height=8, font=("Consolas", 11))
        input_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        runs_frame = tk.Frame(win)
        runs_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Label(runs_frame, text="Runs per side:").pack(side=tk.LEFT)
        runs_var = tk.IntVar(value=3)
        runs_entry = tk.Entry(runs_frame, textvariable=runs_var, width=6)
        runs_entry.pack(side=tk.LEFT, padx=(6, 0))

        btn = tk.Button(
            win,
            text="Start Race",
            command=lambda: self.run_race_thread(input_box.get("1.0", tk.END), runs_var.get()),
            font=("Segoe UI", 10, "bold"),
            width=12,
        )
        btn.pack(pady=(0, 10))

    def run_race_thread(self, input_data, runs):
        threading.Thread(
            target=self.run_race,
            args=(input_data, runs),
            daemon=True,
        ).start()

    def run_race(self, input_data, runs):
        if not self.check_compiler():
            return

        left_code = self.editor_left.get(1.0, tk.END)
        right_code = self.editor_right.get(1.0, tk.END)

        if not left_code.strip() or not right_code.strip():
            messagebox.showerror("Race Error", "Both editors must have code for a race.")
            return

        try:
            runs = int(runs)
        except Exception:
            runs = 3
        if runs < 1:
            runs = 1

        self.btn_race.config(state=tk.DISABLED)
        self.lbl_status.config(text="Racing...")

        try:
            if not self.compile_code_from_text(left_code, "left"):
                return
            if not self.compile_code_from_text(right_code, "right"):
                return

            env = os.environ.copy()
            env["IDE_BENCHMARK"] = "1"

            left_times = []
            right_times = []

            for i in range(runs):
                res_left = subprocess.run(
                    [self.get_temp_exe_path("left")],
                    input=input_data,
                    capture_output=True,
                    text=True,
                    env=env,
                )
                if res_left.returncode != 0:
                    messagebox.showerror("Race Error (Left)", res_left.stderr or res_left.stdout)
                    return

                t_left, _, _, _ = self.parse_ide_metrics(res_left.stdout + res_left.stderr)
                if t_left is None:
                    messagebox.showerror("Race Error", "Could not parse timing output for left.")
                    return

                res_right = subprocess.run(
                    [self.get_temp_exe_path("right")],
                    input=input_data,
                    capture_output=True,
                    text=True,
                    env=env,
                )
                if res_right.returncode != 0:
                    messagebox.showerror("Race Error (Right)", res_right.stderr or res_right.stdout)
                    return

                t_right, _, _, _ = self.parse_ide_metrics(res_right.stdout + res_right.stderr)
                if t_right is None:
                    messagebox.showerror("Race Error", "Could not parse timing output for right.")
                    return

                left_times.append(t_left)
                right_times.append(t_right)

            mean_left = statistics.mean(left_times)
            mean_right = statistics.mean(right_times)

            winner = "Tie"
            ratio = None
            if mean_left > 0 and mean_right > 0:
                if mean_left < mean_right:
                    winner = "Left"
                    ratio = mean_right / mean_left
                elif mean_right < mean_left:
                    winner = "Right"
                    ratio = mean_left / mean_right

            msg = (
                f"Left mean:  {mean_left:.9f} s\\n"
                f"Right mean: {mean_right:.9f} s\\n"
                f"Runs per side: {runs}\\n"
            )

            if winner == "Tie":
                msg += "Result: Tie (too close to call)."
            elif ratio is None:
                msg += f"Winner: {winner} (too fast to compute ratio)."
            else:
                msg += f"Winner: {winner} side is {ratio:.2f}x faster."

            messagebox.showinfo("Race Result", msg)
        finally:
            self.btn_race.config(state=tk.NORMAL)
            self.lbl_status.config(text="Ready")

    def sanitize_project_name(self, name):
        cleaned = re.sub(r"[^A-Za-z0-9 _-]", "", name or "")
        cleaned = cleaned.strip().replace(" ", "_")
        return cleaned if cleaned else "Untitled"

    def schedule_highlight(self, editor):
        job = self._highlight_jobs.get(editor)
        if job:
            self.root.after_cancel(job)
        self._highlight_jobs[editor] = self.root.after(300, lambda e=editor: self.apply_syntax_highlighting(e))

    def apply_syntax_highlighting(self, editor):
        self._highlight_jobs[editor] = None
        text = editor.get("1.0", tk.END)

        for tag in ["comment", "string", "keyword", "type", "number", "preproc"]:
            editor.tag_remove(tag, "1.0", tk.END)

        def apply(pattern, tag, flags=0):
            for match in re.finditer(pattern, text, flags):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                editor.tag_add(tag, start, end)

        keywords = [
            "auto", "break", "case", "catch", "class", "const", "constexpr", "continue", "default",
            "delete", "do", "else", "enum", "explicit", "export", "extern", "for", "friend", "goto",
            "if", "inline", "namespace", "new", "noexcept", "operator", "private", "protected", "public",
            "register", "reinterpret_cast", "return", "sizeof", "static", "struct", "switch", "template",
            "this", "throw", "try", "typedef", "typeid", "typename", "union", "using", "virtual", "volatile",
            "while", "override", "final", "mutable", "static_cast", "dynamic_cast", "const_cast",
        ]

        types = [
            "bool", "char", "double", "float", "int", "long", "short", "signed", "unsigned", "void",
            "size_t", "wchar_t", "char16_t", "char32_t", "std", "string",
        ]

        keyword_pattern = r"\b(" + "|".join(re.escape(k) for k in keywords) + r")\b"
        type_pattern = r"\b(" + "|".join(re.escape(t) for t in types) + r")\b"

        apply(r"^[ \t]*#.*?$", "preproc", flags=re.MULTILINE)
        apply(r"\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b", "number")
        apply(keyword_pattern, "keyword")
        apply(type_pattern, "type")
        apply(r'"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\'', "string")
        apply(r"//.*?$|/\*.*?\*/", "comment", flags=re.MULTILINE | re.DOTALL)

        editor.tag_raise("comment")
        editor.tag_raise("string")

    def configure_syntax_tags(self, theme, editor):
        colors = theme["highlight"]
        editor.tag_configure("keyword", foreground=colors["keyword"])
        editor.tag_configure("type", foreground=colors["type"])
        editor.tag_configure("string", foreground=colors["string"])
        editor.tag_configure("comment", foreground=colors["comment"])
        editor.tag_configure("number", foreground=colors["number"])
        editor.tag_configure("preproc", foreground=colors["preproc"])

    def apply_theme(self, *args):
        theme = THEMES.get(self.theme_var.get(), THEMES["Dark"])
        self.root.configure(bg=theme["root_bg"])

        self.toolbar.configure(bg=theme["toolbar_bg"])
        self.options_bar.configure(bg=theme["toolbar_bg"])
        self.info_frame.configure(bg=theme["info_bg"])
        self.work_area.configure(bg=theme["root_bg"])
        self.snippet_frame.configure(bg=theme["toolbar_bg"])

        for widget in [self.lbl_status, self.lbl_runs, self.lbl_project, self.lbl_theme, self.lbl_language, self.lbl_complexity]:
            widget.configure(bg=theme["toolbar_bg"], fg=theme["toolbar_fg"])

        self.chk_bench.configure(
            bg=theme["toolbar_bg"],
            fg=theme["toolbar_fg"],
            activebackground=theme["toolbar_bg"],
            activeforeground=theme["toolbar_fg"],
        )
        self.chk_split.configure(
            bg=theme["toolbar_bg"],
            fg=theme["toolbar_fg"],
            activebackground=theme["toolbar_bg"],
            activeforeground=theme["toolbar_fg"],
        )

        self.info_label.configure(bg=theme["info_bg"], fg=theme["info_fg"])

        self.btn_run.configure(
            bg=theme["button_run_bg"],
            fg=theme["button_fg"],
            activebackground=theme["button_run_bg"],
            activeforeground=theme["button_fg"],
        )
        self.btn_kill.configure(
            bg=theme["button_kill_bg"],
            fg=theme["button_fg"],
            activebackground=theme["button_kill_bg"],
            activeforeground=theme["button_fg"],
        )
        self.btn_race.configure(
            bg=theme["toolbar_bg"],
            fg=theme["toolbar_fg"],
            activebackground=theme["toolbar_bg"],
            activeforeground=theme["toolbar_fg"],
        )
        self.btn_complexity.configure(
            bg=theme["toolbar_bg"],
            fg=theme["toolbar_fg"],
            activebackground=theme["toolbar_bg"],
            activeforeground=theme["toolbar_fg"],
        )

        if hasattr(self, "snippet_list"):
            self.snippet_list.configure(
                bg=theme["editor_bg"],
                fg=theme["editor_fg"],
                selectbackground=theme["button_run_bg"],
                selectforeground=theme["button_fg"],
            )
            for child in self.snippet_frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=theme["toolbar_bg"], fg=theme["toolbar_fg"])
                if isinstance(child, tk.Button):
                    child.configure(
                        bg=theme["toolbar_bg"],
                        fg=theme["toolbar_fg"],
                        activebackground=theme["toolbar_bg"],
                        activeforeground=theme["toolbar_fg"],
                    )

        for entry in [self.entry_runs, self.entry_project]:
            entry.configure(
                bg=theme["editor_bg"],
                fg=theme["editor_fg"],
                insertbackground=theme["insert_bg"],
            )

        self.theme_menu.configure(
            bg=theme["toolbar_bg"],
            fg=theme["toolbar_fg"],
            activebackground=theme["toolbar_bg"],
            activeforeground=theme["toolbar_fg"],
        )
        self.theme_menu["menu"].configure(bg=theme["toolbar_bg"], fg=theme["toolbar_fg"])

        self.language_menu.configure(
            bg=theme["toolbar_bg"],
            fg=theme["toolbar_fg"],
            activebackground=theme["toolbar_bg"],
            activeforeground=theme["toolbar_fg"],
        )
        self.language_menu["menu"].configure(bg=theme["toolbar_bg"], fg=theme["toolbar_fg"])

        for editor in [self.editor_left, self.editor_right]:
            editor.configure(
                bg=theme["editor_bg"],
                fg=theme["editor_fg"],
                insertbackground=theme["insert_bg"],
            )
            self.configure_syntax_tags(theme, editor)
            self.schedule_highlight(editor)

    # --- COMPILER SETUP ---

    def detect_compilers(self):
        self.compiler_cmd_cpp = shutil.which("g++") or shutil.which("clang++")
        self.compiler_cmd_c = shutil.which("gcc") or shutil.which("clang")
        self.c_compiler_is_cpp_driver = False
        if not self.compiler_cmd_c and self.compiler_cmd_cpp:
            self.compiler_cmd_c = self.compiler_cmd_cpp
            self.c_compiler_is_cpp_driver = True

    def try_use_bundled_compiler(self):
        if os.name == "nt":
            bin_names = ["g++.exe", "gcc.exe", "clang++.exe", "clang.exe"]
        else:
            bin_names = ["g++", "gcc", "clang++", "clang"]

        for bin_dir in iter_bundled_compiler_bin_candidates():
            if not os.path.isdir(bin_dir):
                continue
            if not any(os.path.exists(os.path.join(bin_dir, name)) for name in bin_names):
                continue
            path_parts = os.environ.get("PATH", "").split(os.pathsep)
            if bin_dir not in path_parts:
                os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
            self.detect_compilers()
            if self.get_active_compiler():
                return True
        return False

    def check_compiler(self):
        self.detect_compilers()

        if not self.get_active_compiler():
            if self.try_use_bundled_compiler():
                pass
            else:
                bundled = find_bundled_compiler_zip()
                if bundled:
                    self.lbl_status.config(text="Extracting Bundled Compiler...")
                    threading.Thread(target=self.extract_bundled_compiler, args=(bundled,), daemon=True).start()
                    return False
                if os.name == "nt":
                    self.lbl_status.config(text="Downloading Compiler...")
                    threading.Thread(target=self.download_compiler, daemon=True).start()
                    return False

        active = self.get_active_compiler()
        if active:
            lang = self.language_var.get()
            if lang == "C":
                note = " (fallback: using C++ driver)" if self.c_compiler_is_cpp_driver else ""
                self.lbl_status.config(text=f"Compiler Ready for C{note}")
            else:
                self.lbl_status.config(text="Compiler Ready for C++")
            return True

        self.lbl_status.config(text="No compiler found (install gcc/clang or bundle into compiler/bin)")
        return False

    def download_compiler(self):
        try:
            url = COMPILER_URLS.get(PLATFORM_KEY)
            if not url:
                self.lbl_status.config(text="No bundled compiler download for this OS")
                return
            bundled = find_bundled_compiler_zip()
            zip_p = os.path.join(BASE_DIR, "compiler.zip")
            os.makedirs(LOCAL_COMPILER_DIR, exist_ok=True)
            if bundled:
                shutil.copyfile(bundled, zip_p)
            else:
                urllib.request.urlretrieve(url, zip_p)
            with zipfile.ZipFile(zip_p, "r") as z:
                z.extractall(LOCAL_COMPILER_DIR)
            os.remove(zip_p)
            self.check_compiler()
        except Exception:
            self.lbl_status.config(text="Download Failed")

    def extract_bundled_compiler(self, zip_path):
        try:
            os.makedirs(LOCAL_COMPILER_DIR, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(LOCAL_COMPILER_DIR)
            self.check_compiler()
        except Exception:
            self.lbl_status.config(text="Bundled Compiler Extract Failed")

if __name__ == "__main__":
    root = tk.Tk()
    app = AlgoTimerIDE(root)
    root.mainloop()
