import traceback

# Unconditional top-level assignment to satisfy Vercel's static parser
application = None

try:
    from app import app
    application = app
except Exception as e:
    tb_str = traceback.format_exc()
    def application(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-Type', 'text/html')]
        start_response(status, response_headers)
        html = f"""
        <div style="background:#111; color:#ff5555; padding:20px; font-family:monospace; border-radius:8px; margin:20px;">
            <h3>🔥 Import-Time / Cold Start Crash Traceback:</h3>
            <pre style="white-space: pre-wrap; word-wrap: break-word;">{tb_str}</pre>
        </div>
        """
        return [html.encode('utf-8')]
