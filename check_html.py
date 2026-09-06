with open("app.py", "r") as f:
    lines = f.readlines()

print("--- CURRENT HTML & QUOTE POSITIONS ---")
for i, line in enumerate(lines):
    l = line.strip()
    if "HTML" in l or l == "'''" or l.startswith("'''"):
        print(f"Line {i+1}: {l}")
