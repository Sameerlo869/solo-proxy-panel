with open("app.py", "r") as f:
    content = f.read()

# Remove any occurrences inside main blocks or indented lines
lines = content.split('\n')
new_lines = []

# Ensure proper imports and top-level app declaration are right at the top
new_lines.append("from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for")
new_lines.append("app = Flask(__name__)")
new_lines.append("app.secret_key = 'solo_proxy_secret'\n")

for line in lines:
    # Skip old conflicting declarations or main blocks wrapping app
    if "app = Flask" in line or "application = Flask" in line:
        continue
    if "if __name__ == '__main__':" in line:
        # Stop or skip main block if it tries to run app locally on vercel
        break
    new_lines.append(line)

with open("app.py", "w") as f:
    f.write('\n'.join(new_lines))

print("Scope cleaned and top-level app enforced!")
