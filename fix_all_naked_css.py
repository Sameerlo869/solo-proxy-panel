filename = "app.py"
with open(filename, "r") as f:
    lines = f.readlines()

fixed_lines = []
css_keywords = [
    "display:", "animation:", "background:", "color:", "border-radius:", 
    "padding:", "margin:", "overflow-y:", "position:", "flex:", 
    "font-", "box-shadow:", "cursor:", "transition:", "{display:", "{flex:"
]

for line in lines:
    stripped = line.strip()
    
    # Check if the line looks like a naked CSS selector or property block
    is_css_rule = (
        ((stripped.startswith(".") or stripped.startswith("#") or stripped.startswith("body") or stripped.startswith("div") or stripped.startswith("*")) and "{" in stripped)
        or any(kw in stripped for kw in css_keywords)
    ) and not stripped.startswith("#") and "=" not in stripped and "return" not in stripped and "print" not in stripped and "def " not in stripped and "import " not in stripped

    if is_css_rule:
        print(f"Commenting out leaked CSS line: {stripped}")
        fixed_lines.append("# [Auto-Fixed Leaked CSS] " + line)
    else:
        fixed_lines.append(line)

with open(filename, "w") as f:
    f.writelines(fixed_lines)

print("All leaked CSS lines cleaned up completely!")
