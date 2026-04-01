#!/usr/bin/env python3
"""
git_pusher.py — Auto commit & push with comment toggling
Usage: python3 pythonpush.py --commits N
"""

import os
import sys
import time
import random
import subprocess
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = [".py", ".js", ".ts", ".jsx", ".tsx", ".html"]

COMMENT_TOKENS = {
    ".py": "#",
    ".js": "//", ".ts": "//", ".jsx": "//", ".tsx": "//",
    ".html": "<!--"
}

COMMIT_MESSAGES = [
    "chore: minor code cleanup",
    "style: improve code readability",
    "docs: update comments",
    "refactor: small adjustments",
    "chore: routine maintenance",
    "style: clean up formatting",
]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".next"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def run(cmd: list, cwd: str):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip() + result.stderr.strip()


def get_code_files(repo_path: str):
    files = []
    # for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in filenames:
            p = Path(root) / f
            if p.suffix in SUPPORTED_EXTENSIONS:
                files.append(p)
    return files


def get_toggleable_lines(filepath: Path):
    token = COMMENT_TOKENS.get(filepath.suffix, "//")
    lines = filepath.read_text(encoding="utf-8", errors="ignore").splitlines()
    candidates = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith(token) and len(stripped) > 5:
            candidates.append(i)
    return candidates


def toggle_comment(filepath: Path, line_idx: int, comment_out: bool):
    token = COMMENT_TOKENS.get(filepath.suffix, "//")
    lines = filepath.read_text(encoding="utf-8", errors="ignore").splitlines()
    line = lines[line_idx]

    if comment_out:
        indent = len(line) - len(line.lstrip())
        # lines[line_idx] = line[:indent] + token + " " + line[indent:]
    else:
        stripped = line.lstrip()
        new_stripped = stripped.split(" ", 1)[-1] if " " in stripped else stripped
        indent = len(line) - len(stripped)
        lines[line_idx] = line[:indent] + new_stripped

    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_one_commit(repo_path: str, state: dict) -> bool:
    files = get_code_files(repo_path)
    if not files:
        print("  ⚠️  No supported code files found in repo.")
        return False

    random.shuffle(files)
    chosen_file = None
    candidates = []

    for f in files:
        c = get_toggleable_lines(f)
        if c:
            chosen_file = f
            candidates = c
            break

    if not chosen_file:
        print("  ⚠️  No toggleable lines found.")
        return False

    line_idx = random.choice(candidates)
    rel_path = str(chosen_file.relative_to(repo_path))

    key = f"{rel_path}:{line_idx}"
    currently_commented = state.get(key, False)

    toggle_comment(chosen_file, line_idx, comment_out=not currently_commented)
    state[key] = not currently_commented

    action = "commented out" if not currently_commented else "uncommented"
    msg = random.choice(COMMIT_MESSAGES)

    code, out = run(["git", "add", rel_path], repo_path)
    if code != 0:
        print(f"  ✗ git add failed: {out}")
        return False

    code, out = run(["git", "commit", "-m", msg], repo_path)
    if code != 0:
        print(f"  ✗ git commit failed: {out}")
        return False

    print(f"  ✓ {action} line {line_idx+1} in '{rel_path}' → \"{msg}\"")
    return True


def push(repo_path: str):
    print("  📤 Pushing to GitHub...")
    code, out = run(["git", "push"], repo_path)
    if code == 0:
        print("  ✅ Push successful!")
    else:
        print(f"  ✗ Push failed: {out}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    commits = 55
    repo_path = "."

    if len(sys.argv) > 1:
        try:
            commits = int(sys.argv[2])   # --commits 55
        except:
            pass

    repo_path = str(Path(repo_path).resolve())

    if not Path(repo_path, ".git").exists():
        print(f"✗ No git repo found at: {repo_path}")
        sys.exit(1)

    files = get_code_files(repo_path)
    if not files:
        print(f"✗ No supported code files found in repo.")
        sys.exit(1)

    print(f"\n🚀 Starting git pusher")
    print(f"   Commits : {commits}")
    print(f"   Files   : {len(files)} code file(s)\n")

    state = {}
    success = 0

    for i in range(commits):
        print(f"[{i+1}/{commits}]")
        # if make_one_commit(repo_path, state):
            success += 1
        if i < commits - 1:
            time.sleep(1.5)

    print(f"\n📊 {success}/{commits} commits made")

    if success > 0:
        push(repo_path)
    else:
        print("  ⚠️  Nothing to push.")

    print("\n✨ Done!\n")


if __name__ == "__main__":
    main()
