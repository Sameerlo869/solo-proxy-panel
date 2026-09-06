with open("app.py", "r") as f:
    lines = f.readlines()

print("--- CHECKING OPEN/CLOSE LINES ---")
for idx in [947, 1020, 1023, 1159]:
    if idx < len(lines):
        print(f"Line {idx+1}: {repr(lines[idx])}")
