with open("app.py", "r") as f:
    lines = f.readlines()

print("--- CHECKING LINES 340 TO 350 ---")
for i in range(339, min(len(lines), 350)):
    print(f"{i+1}: {repr(lines[i])}")
