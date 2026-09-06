filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    lines = f.readlines()

if len(lines) >= 87:
    print(f"Before fix line 87: {repr(lines[86])}")
    # Make _limits = {} a global variable with 0 indentation
    lines[86] = lines[86].lstrip()
    print(f"After fix line 87: {repr(lines[86])}")

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    compile("".join(lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly.")
except Exception as e:
    print(f"Compilation Error: {e}")
