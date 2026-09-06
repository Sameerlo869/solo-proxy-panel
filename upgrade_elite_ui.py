filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    content = f.read()

import re

elite_dashboard_code = r"""
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Solo Proxy Panel - Elite Automation</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap');
        :root {
            --bg: #090d16;
            --card-bg: rgba(30, 41, 59, 0.7);
            --border: rgba(56, 189, 248, 0.2);
            --primary: #38bdf8;
            --accent: #00ffcc;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
        }
        body {
            background-color: var(--bg);
            background-image: radial-gradient(circle at 10% 20%, rgba(56, 189, 248, 0.08) 0%, transparent 40%),
                              radial-gradient(circle at 90% 80%, rgba(0, 255, 204, 0.05) 0%, transparent 40%);
            color: var(--text);
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 30px 15px;
            min-height: 100vh;
        }
        .container { max-width: 1000px; margin: auto; animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1); }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulseGlow {
            0% { box-shadow: 0 0 15px rgba(56, 189, 248, 0.15); }
            50% { box-shadow: 0 0 30px rgba(56, 189, 248, 0.4), inset 0 0 15px rgba(0, 255, 204, 0.1); }
            100% { box-shadow: 0 0 15px rgba(56, 189, 248, 0.15); }
        }
        .glass-card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 25px;
            animation: pulseGlow 4s infinite ease-in-out;
            transition: transform 0.3s ease, border-color 0.3s ease;
        }
        .glass-card:hover {
            border-color: rgba(56, 189, 248, 0.5);
            transform: translateY(-2px);
        }
        h2, h3, h4 { color: var(--primary); font-weight: 700; letter-spacing: -0.025em; }
        textarea {
            width: 100%;
            background: #030712;
            color: var(--accent);
            border: 1px solid #1e293b;
            padding: 15px;
            border-radius: 10px;
            font-family: 'Fira Code', monospace;
            font-size: 13px;
            resize: vertical;
            box-sizing: border-box;
            transition: all 0.3s ease;
        }
        textarea:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.25);
        }
        .btn-elite {
            background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 12px rgba(56, 189, 248, 0.3);
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .btn-elite:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(56, 189, 248, 0.5);
            background: linear-gradient(135deg, #0ea5e9 0%, #0369a1 100%);
        }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 14px 16px; border-bottom: 1px solid rgba(51, 65, 85, 0.5); text-align: left; font-size: 14px; }
        th { color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.05em; }
        tr { transition: background 0.2s ease; }
        tr:hover { background: rgba(56, 189, 248, 0.03); }
        .badge { padding: 6px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; display: inline-flex; align-items: center; gap: 5px; }
        .badge-active { background: rgba(6, 95, 70, 0.4); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }
        .badge-inactive { background: rgba(127, 29, 29, 0.4); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.3); }
        .spinner {
            width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%; border-top-color: #fff; animation: spin 0.8s linear infinite; display: none;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        #toast {
            position: fixed; bottom: 20px; right: 20px; background: #065f46; color: #34d399;
            padding: 12px 24px; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            border: 1px solid #34d399; font-weight: 600; display: none; animation: slideUp 0.3s ease; z-index: 1000;
        }
        @keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    </style>
</head>
<body>
    <div class="container">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
            <div>
                <h2 style="margin: 0; font-size: 24px; background: linear-gradient(to right, #38bdf8, #00ffcc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">⚡ Solo Proxy Panel</h2>
                <p style="margin: 5px 0 0 0; color: var(--text-muted); font-size: 13px;">Next-Gen Autonomous Enterprise Automation</p>
            </div>
            <div class="badge badge-active">System Online 🟢</div>
        </div>

        <div class="glass-card">
            <h3>🚀 Autonomous Smart Request Importer</h3>
            <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 15px;">Paste your raw HTTP request below. The engine will instantly parse headers, tokens, tenants, and brokers, activating the company pipeline autonomously with zero manual input.</p>
            
            <form id="autoForm" onsubmit="submitAutoImport(event)">
                <textarea name="raw_data" rows="5" placeholder="GET /api/minterprise/v1/... HTTP/2&#10;host: turtlemintloans.com&#10;x-broker: turtlemint..." required></textarea>
                <div style="margin-top: 15px; display: flex; align-items: center; gap: 15px;">
                    <button type="submit" class="btn-elite" id="submitBtn">
                        <span>Execute Full Automation</span>
                        <div class="spinner" id="btnSpinner"></div>
                    </button>
                    <span id="statusMsg" style="font-size: 13px; color: var(--accent); font-family: 'Fira Code', monospace;"></span>
                </div>
            </form>
        </div>

        <div class="glass-card">
            <h3 style="margin-bottom: 15px;">📋 Active Company Infrastructure</h3>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Broker / Enterprise</th>
                            <th>Tenant</th>
                            <th>Active Provider</th>
                            <th>Pipeline Status</th>
                            <th>Token Health</th>
                            <th>Live Actions</th>
                        </tr>
                    </thead>
                    <tbody id="companyTableBody">
                        {% if db and db.get('companies') %}
                            {% for code, comp in db.get('companies', {}).items() %}
                            <tr id="row-{{ code }}">
                                <td><b>{{ comp.get('broker_id', code) }}</b></td>
                                <td><code style="color: var(--primary);">{{ comp.get('tenant_id', '-') }}</code></td>
                                <td>{{ comp.get('active_provider', '-') }}</td>
                                <td>
                                    <span class="badge {% if comp.get('status', 'active') == 'active' %}badge-active{% else %}badge-inactive{% endif %}">
                                        ● {{ comp.get('status', 'active').upper() }}
                                    </span>
                                </td>
                                <td>{{ comp.get('token_status', 'Valid & Active 🟢') }}</td>
                                <td>
                                    <button onclick="toggleCompany('{{ code }}')" class="btn-elite" style="padding: 6px 12px; font-size: 11px; background: #334155;">Toggle</button>
                                    <button onclick="checkToken('{{ code }}')" class="btn-elite" style="padding: 6px 12px; font-size: 11px; background: #065f46;">Health Check</button>
                                </td>
                            </tr>
                            {% endfor %}
                        {% else %}
                            <tr id="emptyRow">
                                <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 30px;">No companies in pipeline. Paste a raw request above to auto-deploy!</td>
                            </tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div id="toast">Company successfully auto-imported & deployed! 🚀</div>

    <script>
    async function submitAutoImport(e) {
        e.preventDefault();
        const form = e.target;
        const textarea = form.querySelector('textarea');
        const btn = document.getElementById('submitBtn');
        const spinner = document.getElementById('btnSpinner');
        const statusMsg = document.getElementById('statusMsg');

        btn.disabled = true;
        spinner.style.display = 'inline-block';
        statusMsg.innerText = 'Extracting headers & deploying tokens...';

        try {
            const response = await fetch('/api/auto-company-import', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ raw_data: textarea.value })
            });
            const result = await response.json();
            
            if (result.status) {
                showToast(result.msg);
                textarea.value = '';
                statusMsg.innerText = '✨ Autonomous deploy complete!';
                setTimeout(() => { location.reload(); }, 800);
            } else {
                statusMsg.innerText = '❌ Error: ' + result.msg;
            }
        } catch (err) {
            statusMsg.innerText = '❌ Network error during auto-import.';
        } finally {
            btn.disabled = false;
            spinner.style.display = 'none';
        }
    }

    async function toggleCompany(code) {
        await fetch('/api/company/toggle/' + code, { method: 'POST' });
        location.reload();
    }

    async function checkToken(code) {
        await fetch('/api/company/check/' + code, { method: 'POST' });
        location.reload();
    }

    function showToast(msg) {
        const toast = document.getElementById('toast');
        toast.innerText = msg;
        toast.style.display = 'block';
        setTimeout(() => { toast.style.display = 'none'; }, 3000);
    }
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    try:
        db = GistDB.load() or {}
        return render_template_string(HTML_TEMPLATE, db=db)
    except Exception as e:
        return f"Dashboard Error: {str(e)}", 500
"""

# Replace old HTML template and dashboard route cleanly
content = re.sub(r'HTML_TEMPLATE\s*=\s*'''.*?'''', '', content, flags=re.DOTALL)
content = re.sub(r'def dashboard\(\):(.*?)(?=\ndef |\n@app.route|\Z)', '', content, flags=re.DOTALL)

if "if __name__ == '__main__':" in content:
    content = content.replace("if __name__ == '__main__':", elite_dashboard_code + "\n\nif __name__ == '__main__':")
else:
    content += "\n" + elite_dashboard_code

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

compile(content, filename, 'exec')
print("SUCCESS! Elite Glassmorphic UI & Async Automation injected successfully.")
