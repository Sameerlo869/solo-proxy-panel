filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    content = f.read()

import re

# Remove any script block or inline JS that triggers the "Token Auto-Encrypted" alert
content = re.sub(r'<script\b[^>]*>.*?(?:Token Auto-Encrypted|Check browser console).*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)

# Ensure the auto-import form explicitly posts cleanly to /api/auto-company-import without custom JS intercepts
# Let's replace the form tag to be completely clean
old_form_pattern = re.compile(r'<form\s+[^>]*action="/api/auto-company-import"[^>]*>.*?</form>', re.DOTALL | re.IGNORECASE)

clean_form = """
<div style="background: linear-gradient(135deg, #1e1e2f 0%, #12121a 100%); padding: 20px; border-radius: 12px; margin-bottom: 25px; border: 1px solid #4e73df;">
  <h4 style="color: #4e73df; margin-bottom: 8px; font-weight: 600;">⚡ Fully Automated Smart Request Importer</h4>
  <p style="color: #bbb; font-size: 13px; margin-bottom: 15px;">Apna raw HTTP request yahan paste karo. Ek click mein Tenant, Broker, Provider aur Auth Token extract hoke company seedha active list mein save ho jayegi!</p>
  
  <form action="/api/auto-company-import" method="POST">
    <textarea name="raw_data" class="form-control" rows="5" style="width: 100%; background: #0b0b10; color: #00ffcc; border: 1px solid #333; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 12px;" placeholder="Paste raw HTTP request here (GET /api/... HTTP/2...)" required></textarea>
    
    <div style="margin-top: 12px;">
      <button type="submit" class="btn btn-primary" style="background: linear-gradient(135deg, #4e73df 0%, #224abe 100%); color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600;">🚀 Auto-Parse & Save Company</button>
    </div>
  </form>
</div>
"""

if old_form_pattern.search(content):
    content = old_form_pattern.sub(clean_form, content)
    print("Replaced old intercepted form with clean direct-action form.")
else:
    # If pattern didn't match exactly, let's append or inject it safely
    content += "\n<!-- Clean Auto Importer Form -->\n" + clean_form
    print("Appended clean auto importer form.")

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

compile(content, filename, 'exec')
print("SUCCESS! app.py compiled cleanly with zero errors.")
