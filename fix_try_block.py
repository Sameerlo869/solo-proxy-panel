filename = "app.py"
with open(filename, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

fixed = []
for i, line in enumerate(lines):
    stripped = line.strip()
    
    # Check for orphan try: without except/finally
    if stripped == "try:":
        curr_indent = len(line) - len(line.lstrip())
        has_handler = False
        for j in range(i + 1, min(len(lines), i + 25)):
            nxt = lines[j]
            nxt_stripped = nxt.strip()
            nxt_indent = len(nxt) - len(nxt.lstrip())
            if nxt_indent == curr_indent and (nxt_stripped.startswith("except") or nxt_stripped.startswith("finally")):
                has_handler = True
                break
            if nxt_indent < curr_indent and nxt_stripped:
                break
        if not has_handler:
            line = "# [Auto-Fixed Orphan Try] " + line
            
    # Clean up any lone stray triple quotes at the bottom causing syntax breaks
    if stripped in ("'''", '"""') and i > len(lines) - 15:
        line = "# [Auto-Fixed Stray Quote] " + line

    fixed.append(line)

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(fixed)

# Test compilation immediately
try:
    with open(filename, "r", encoding="utf-8") as f:
        compile(f.read(), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly now.")
except Exception as e:
    print(f"Remaining compilation check error: {e}")
