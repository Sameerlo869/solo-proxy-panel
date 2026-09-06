with open("app.py", "r") as f:
    lines = f.readlines()

print("=== ALL TRIPLE QUOTES IN APP.PY ===")
for i, line in enumerate(lines):
    if "'''" in line:
        print(f"Line {i+1}: {line.strip()}")
