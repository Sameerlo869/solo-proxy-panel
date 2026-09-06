filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    lines = f.readlines()

if len(lines) >= 19:
    print(f"Before fix line 19: {repr(lines[18])}")
    # Strip leading spaces from line 19
    lines[18] = lines[18].lstrip()
    print(f"After fix line 19: {repr(lines[18])}")

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    compile("".join(lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly.")
except Exception as e:
    print(f"Compilation Error: {e}")
