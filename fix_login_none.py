filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("--- Checking around line 109 ---")
for idx in range(100, min(len(lines), 116)):
    print(f"Line {idx+1}: {repr(lines[idx])}")

# Find login function and ensure db falls back to {} if None
for i, line in enumerate(lines):
    if "def login():" in line:
        for j in range(i, min(i + 10, len(lines))):
            if "db = GistDB.load()" in lines[j]:
                lines[j] = lines[j].replace("GistDB.load()", "GistDB.load() or {}")
                print(f"Patched line {j+1}: {repr(lines[j])}")

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    compile("".join(lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
