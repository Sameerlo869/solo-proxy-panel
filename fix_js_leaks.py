filename = "app.py"
with open(filename, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

fixed_lines = []
for line in lines:
    stripped = line.strip()
    
    # Check if line contains JavaScript backticks, template strings, or raw checkmark symbols in python scope
    is_leaked_js = (
        "`" in line or 
        "${" in line or 
        "âœ“" in line or 
        "✓" in line or
        "resDiv.innerHTML" in line or
        "autoIngestRaw" in line
    ) and not stripped.startswith("#") and "def " not in stripped and "import " not in stripped and "app.route" not in stripped

    if is_leaked_js:
        print(f"Commenting out leaked JS line: {stripped}")
        fixed_lines.append("# [Auto-Fixed Leaked JS] " + line)
    else:
        fixed_lines.append(line)

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(fixed_lines)

print("Leaked JS lines cleaned up successfully!")
