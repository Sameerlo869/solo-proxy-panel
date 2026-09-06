with open("app.py", "r") as f:
    lines = f.readlines()

fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    fixed_lines.append(line)
    stripped = line.strip()
    
    # Check if a control statement ends with ':' and requires an indented block
    if stripped in ("try:", "except:", "else:", "finally:") or stripped.startswith(("except ", "elif ", "if ", "for ", "while ", "def ", "class ")):
        curr_indent = len(line) - len(line.lstrip())
        
        # Look ahead for the next non-empty line
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            fixed_lines.append(lines[j])
            j += 1
            
        if j < len(lines):
            next_line = lines[j]
            next_indent = len(next_line) - len(next_line.lstrip())
            # If the next line is not indented more than the header, insert a `pass`
            if next_indent <= curr_indent:
                indent_str = " " * (curr_indent + 4)
                fixed_lines.append(f"{indent_str}pass\n")
        i = j - 1
    i += 1

with open("app.py", "w") as f:
    f.writelines(fixed_lines)

print("Indentation error fixed successfully!")
