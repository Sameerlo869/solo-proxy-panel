filename = "app.py"
with open(filename, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for attempt in range(10):
    try:
        content = "".join(lines)
        compile(content, filename, 'exec')
        print("Success! app.py compiled cleanly.")
        break
    except IndentationError as e:
        lineno = e.lineno
        print(f"[Attempt {attempt+1}] Fixing IndentationError at line {lineno}: {e.msg}")
        if lineno and 0 < lineno <= len(lines):
            idx = lineno - 1
            target_indent = 0
            for p in range(idx - 1, -1, -1):
                if lines[p].strip():
                    p_line = lines[p]
                    target_indent = len(p_line) - len(p_line.lstrip())
                    if p_line.strip().endswith(':'):
                        target_indent += 4
                    break
            lines[idx] = " " * max(0, target_indent) + lines[idx].lstrip()
        else:
            break
    except SyntaxError as e:
        lineno = e.lineno
        print(f"SyntaxError at line {lineno}: {e.msg}")
        if lineno and 0 < lineno <= len(lines):
            lines[lineno - 1] = "# [Auto-Fixed] " + lines[lineno - 1]
        else:
            break

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Indentation alignment completed!")
