filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    content = f.read()

import re

# Remove any script block containing the annoying alert/console log
content = re.sub(r'<script\b[^>]*>.*?(?:Token Auto-Encrypted|Check browser console).*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

compile(content, filename, 'exec')
print("SUCCESS! Alert script removed cleanly.")
