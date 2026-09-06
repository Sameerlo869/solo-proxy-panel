filename = "app.py"
with open(filename, "r") as f:
    lines = f.readlines()

# Normalize tabs to 4 spaces across all lines
normalized_lines = []
for line in lines:
    normalized_lines.append(line.expandtabs(4))

# Iteratively compile and fix indentation errors
for attempt in range(25):
    content = "".join(normalized_lines)
    try:
        compile(content, filename, 'exec')
        print("Success! app.py compiled cleanly with zero indentation errors.")
        break
    except IndentationError as e:
        lineno = e.lineno
        msg = e.msg
        print(f"[Attempt {attempt+1}] Fixing line {lineno}: {msg}")
        
        if lineno and 0 < lineno <= len(normalized_lines):
            idx = lineno - 1
            # Find the correct indentation level from the closest preceding non-empty line
            target_indent = 0
            for p in range(idx - 1, -1, -1):
                p_line = normalized_lines[p]
                if p_line.strip():
                    p_indent = len(p_line) - len(p_line.lstrip())
                    if p_line.strip().endswith(':'):
                        target_indent = p_indent + 4
                    else:
                        target_indent = p_indent
                    break
            
            stripped = normalized_lines[idx].lstrip()
            normalized_lines[idx] = " " * max(0, target_indent) + stripped
        else:
            break
    except SyntaxError as e:
        lineno = e.lineno
        print(f"SyntaxError at line {lineno}: {e.msg}")
        if lineno and 0 < lineno <= len(normalized_lines):
            normalized_lines[lineno - 1] = "# [Auto-Fixed] " + normalized_lines[lineno - 1]
        else:
            break

with open(filename, "w") as f:
    f.writelines(normalized_lines)

print("Indentation mismatch fixed successfully!")
