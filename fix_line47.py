filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    lines = f.readlines()

if len(lines) >= 47:
    print(f"Before fix line 47: {repr(lines[46])}")
    # Match indentation with the context of line 46
    prev_line = lines[45]
    prev_indent = len(prev_line) - len(prev_line.lstrip(' '))
    stripped = lines[46].lstrip(' ')
    
    if prev_line.strip().endswith(':'):
        lines[46] = ' ' * (prev_indent + 4) + stripped
    else:
        lines[46] = ' ' * prev_indent + stripped
        
    print(f"After fix line 47: {repr(lines[46])}")

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    compile("".join(lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly.")
except Exception as e:
    print(f"Compilation Error: {e}")
