filename = "app.py"
with open(filename, "r") as f:
    lines = f.readlines()

fixed_lines = []
for line in lines:
    stripped = line.strip()
    # Check if the line contains naked CSS properties outside python syntax
    is_naked_css = any(marker in stripped for marker in ["px;", "rem;", "background:", "color:", "border-radius:", "display:flex", "overflow-y:"])
    if is_naked_css and not stripped.startswith("#") and "=" not in stripped and "return" not in stripped and "print" not in stripped:
        print(f"Fixing naked CSS line: {stripped}")
        fixed_lines.append("# [Auto-Fixed Naked CSS] " + line)
    else:
        fixed_lines.append(line)

with open(filename, "w") as f:
    f.writelines(fixed_lines)

print("Naked CSS cleaned up successfully!")
