with open("app.py", "r") as f:
    lines = f.readlines()

print("--- LINES 850 TO 950 ---")
for i in range(849, min(len(lines), 950)):
    print(f"{i+1}: {lines[i]}", end="")
