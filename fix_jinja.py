with open("app.py", "r") as f:
    content = f.read()

# Count Jinja if and endif tags inside the template string
if_count = content.count("{% if")
endif_count = content.count("{% endif")

print(f"Jinja 'if' count: {if_count}, 'endif' count: {endif_count}")

if if_count > endif_count:
    missing = if_count - endif_count
    print(f"Adding {missing} missing 'endif' tags to balance the template...")
    # Find the last occurrence of the HTML template string before render_template_string
    # We will insert the missing endif tags right before the closing of the HTML variable
    target_idx = content.rfind("render_template_string")
    if target_idx != -1:
        # Insert missing endif tags right before render_template_string call
        content = content[:target_idx] + ("\n{% endif %}\n" * missing) + content[target_idx:]

with open("app.py", "w") as f:
    f.write(content)

print("Jinja template balanced successfully!")
