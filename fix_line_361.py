filename = "app.py"
with open(filename, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

target_idx = 360  # Line 361
if target_idx < len(lines):
    curr_stripped = lines[target_idx].lstrip()
    # Find the correct base indentation from the preceding non-empty line
    for p in range(target_idx - 1, -1, -1):
        if lines[p].strip():
            base_indent = len(lines[p]) - len(lines[p].lstrip())
            if lines[p].strip().endswith(':'):
                lines[target_idx] = " " * (base_indent + 4) + curr_stripped
            else:
                lines[target_idx] = " " * base_indent + curr_stripped
            break

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    with open(filename, "r", encoding="utf-8") as f:
        compile(f.read(), filename, 'exec')
    print("Success! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation check: {e}")
