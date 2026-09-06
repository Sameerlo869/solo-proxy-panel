import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Remove the widget from wherever it was incorrectly placed inside Jinja blocks
if "<!-- Smart Quick Auto-Ingest Widget -->" in content:
    content = re.sub(r"\s*<!-- Smart Quick Auto-Ingest Widget -->.*?</script>", "", content, flags=re.DOTALL)

# 2. Clean up any leftover temporary error handler if still present
if "def handle_server_exception" in content:
    content = re.sub(r"@app\.errorhandler\(Exception\).*?return.*?\n\n", "", content, flags=re.DOTALL)

# 3. Proper clean widget to safely inject right before </body> (outside any Jinja logic blocks)
proper_widget = """
    <!-- Smart Quick Auto-Ingest Widget -->
    <div class="glass card" style="margin-bottom: 25px; border-color: var(--neon); margin-top: 20px;">
        <div style="font-size:16px; color:var(--neon); margin-bottom:10px;"><i class="fa-solid fa-wand-magic-sparkles"></i> Instant Raw Request Auto-Catcher</div>
        <p style="font-size:12px; color:#a0a0a0; margin-bottom:10px;">Yahan apni raw cURL ya HTTP request paste karo. Tenant, Broker, Token aur Path sab apne aap extract hokar database mein save ho jayega!</p>
        <textarea id="rawRequestInput" rows="4" placeholder="Paste raw HTTP request or cURL here..." style="width:100%; padding:10px; background:rgba(0,0,0,0.4); border:1px solid var(--border); color:#fff; border-radius:6px; outline:none; margin-bottom:10px;"></textarea>
        <button class="btn" onclick="autoIngestRaw()"><i class="fa-solid fa-bolt"></i> Auto-Parse & Save Instantly</button>
        <div id="ingestResult" style="margin-top:10px; font-size:13px; font-family:monospace;"></div>
    </div>
    
    <script>
    async function autoIngestRaw() {
        const rawText = document.getElementById("rawRequestInput").value;
        const resDiv = document.getElementById("ingestResult");
        if(!rawText) {
            resDiv.innerHTML = "<span style='color:#d9534f;'>Please paste a request first!</span>";
            return;
        }
        resDiv.innerHTML = "<span style='color:var(--neon);'>Processing & extracting...</span>";
        
        try {
            let response = await fetch("/admin/auto-ingest", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ raw_text: rawText })
            });
            let data = await response.json();
            if(data.status) {
                resDiv.innerHTML = `<span style='color:#5cb85c;'>✓ Success! Saved path: <b>${data.extracted.path}</b> (Tenant: ${data.extracted.tenant}, Token: ${data.extracted.has_token ? "Captured" : "None"})</span>`;
                setTimeout(() => location.reload(), 1500);
            } else {
                resDiv.innerHTML = `<span style='color:#d9534f;'>Error: ${data.error}</span>`;
            }
        } catch(e) {
            resDiv.innerHTML = `<span style='color:#d9534f;'>Request failed: ${e}</span>`;
        }
    }
    </script>
"""

# Safely inject right before </body>
content = content.replace("</body>", proper_widget + "\n</body>")

with open("app.py", "w") as f:
    f.write(content)

print("Template syntax fixed successfully!")
