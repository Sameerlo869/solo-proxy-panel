with open("app.py", "r") as f:
    lines = f.readlines()

print("--- CHECKING LINES 940 TO 950 ---")
for i in range(939, min(len(lines), 950)):
    print(f"{i+1}: {repr(lines[i])}")
