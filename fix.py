with open("app.py", "r") as f:
    lines = f.readlines()

# Line 1114 is index 1113
idx = 1113
if idx < len(lines):
    print(f"Current Line {idx+1}: {repr(lines[idx])}")
    if "'''" in lines[idx] and not lines[idx].strip().startswith("#"):
        lines[idx] = "# " + lines[idx]
        print(f"Line {idx+1} successfully commented out!")
    else:
        print("Line 1114 is already commented or does not contain triple quotes.")

with open("app.py", "w") as f:
    f.writelines(lines)
