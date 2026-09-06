filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("--- Checking around line 292 ---")
for idx in range(285, min(len(lines), 300)):
    print(f"Line {idx+1}: {repr(lines[idx])}")

if len(lines) >= 292:
    target_idx = 291  # Line 292
    prev_indent = 4
    for k in range(target_idx - 1, -1, -1):
        if lines[k].strip() != "":
            prev_indent = len(lines[k]) - len(lines[k].lstrip(' '))
            if lines[k].strip().endswith(':'):
                prev_indent += 4
            break
    
    stripped = lines[target_idx].lstrip(' ')
    lines[target_idx] = ' ' * max(4, prev_indent) + stripped
    print(f"Adjusted line {target_idx+1} indentation.")

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    compile("".join(lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
