with open("app.py", "r") as f:
    lines = f.readlines()

print("--- CHECKING LINES 1110 TO 1118 ---")
for i in range(1109, min(len(lines), 1118)):
    print(f"{i+1}: {repr(lines[i])}")
