with open("app.py", "r") as f:
    lines = f.readlines()

print(f"Total lines before: {len(lines)}")
print(f"Removing line 1114: {repr(lines[1113])}")

# Remove index 1113 (which is line 1114)
del lines[1113]

with open("app.py", "w") as f:
    f.writelines(lines)

print(f"Total lines after: {len(lines)}")
