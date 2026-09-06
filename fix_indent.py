import re

with open("app.py", "r") as f:
    content = f.read()

# Find the auto_ingest_request function and fix its indentation
pattern = r'(@app\.route\("/admin/auto-ingest".*?def auto_ingest_request\(\):.*?)(?=\n@app\.route|\Z)'
match = re.search(pattern, content, re.DOTALL)
if match:
    func_block = match.group(1)
    # Split into lines, fix indentation of the body (lines after the def line)
    lines = func_block.splitlines()
    # Find the def line index
    def_line_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('def auto_ingest_request():'):
            def_line_idx = i
            break
    if def_line_idx is not None:
        # Re-indent all lines after def line to have 4 spaces (or 1 tab equivalent)
        new_lines = []
        for i, line in enumerate(lines):
            if i <= def_line_idx:
                new_lines.append(line)
            else:
                # If line is empty or only whitespace, keep as is? Better to add 4 spaces.
                if line.strip() == '':
                    new_lines.append('    ' + line)  # but if empty, we can keep as is
                else:
                    # Remove existing leading spaces and add 4 spaces
                    stripped = line.lstrip()
                    new_lines.append('    ' + stripped)
        new_block = '\n'.join(new_lines)
        content = content.replace(func_block, new_block)
        with open("app.py", "w") as f:
            f.write(content)
        print("✅ Indentation fixed!")
    else:
        print("❌ Def line not found.")
else:
    print("❌ Function not found.")
