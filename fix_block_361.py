filename = "app.py"
with open(filename, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

# Find the enclosing indentation from preceding lines
enclosing_indent = 4
for p in range(358, -1, -1):
    line_str = lines[p]
    if any(kw in line_str for kw in ["def ", "for ", "if ", "try:", "with "]):
        enclosing_indent = (len(line_str) - len(line_str.lstrip())) + 4
        break

print(f"Standardizing block around line 361 with indent: {enclosing_indent}")

# Fix lines 358 to 368 to have proper consistent indentation
for idx in range(355, min(len(lines), 370)):
    stripped = lines[idx].lstrip()
    if stripped:
        # If it's part of the statement body, give it proper indentation
        lines[idx] = " " * enclosing_indent + stripped

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    with open(filename, "r", encoding="utf-8") as f:
        compile(f.read(), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero indentation errors.")
except Exception as e:
    print(f"Compilation check error: {e}")
