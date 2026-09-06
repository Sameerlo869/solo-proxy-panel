filename = "app.py"
with open(filename, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

target_idx = 484  # Line 485
if target_idx < len(lines):
    curr_stripped = lines[target_idx].lstrip()
    base_indent = 4
    for p in range(target_idx - 1, -1, -1):
        if lines[p].strip():
            p_line = lines[p]
            base_indent = len(p_line) - len(p_line.lstrip())
            if p_line.strip().endswith(':'):
                base_indent += 4
            break
    lines[target_idx] = " " * max(4, base_indent) + curr_stripped

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    compile("".join(lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation check error: {e}")
