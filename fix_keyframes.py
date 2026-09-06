filename = "app.py"
with open(filename, "r") as f:
    lines = f.readlines()

fixed_lines = []
for line in lines:
    stripped = line.strip()
    
    # Catch any leaked CSS selectors, properties, or keyframes in global python scope
    is_leaked_css = (
        stripped.startswith("@keyframes") or
        stripped.startswith("@media") or
        stripped.startswith("from{") or
        stripped.startswith("to{") or
        ((stripped.startswith(".") or stripped.startswith("#") or stripped.startswith("body") or stripped.startswith("input") or stripped.startswith("button") or stripped.startswith("textarea") or stripped.startswith("div")) and "{" in stripped) or
        ("opacity:" in stripped) or
        ("transform:" in stripped) or
        ("transition:" in stripped) or
        ("box-shadow:" in stripped)
    ) and not stripped.startswith("#") and "=" not in stripped and "return" not in stripped and "print" not in stripped and "def " not in stripped and "import " not in stripped

    if is_leaked_css:
        print(f"Commenting out leaked CSS/Keyframes: {stripped}")
        fixed_lines.append("# [Auto-Fixed Leaked CSS/Keyframes] " + line)
    else:
        fixed_lines.append(line)

with open(filename, "w") as f:
    f.writelines(fixed_lines)

print("Leaked CSS & Keyframes cleaned up completely!")
