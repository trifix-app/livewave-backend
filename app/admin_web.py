import json
from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import settings
from app.services import cache, upstream_client
from app.services.admin_auth import verify_admin_token

admin_web_router = APIRouter(tags=["Admin Web Portal"])


@admin_web_router.get("/admin", response_class=HTMLResponse, summary="Admin Portal Web UI")
@admin_web_router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request):
    token = request.cookies.get("admin_token")
    admin_payload = verify_admin_token(token) if token else None

    if not admin_payload:
        # Render Admin Login Page
        return _render_login_page()

    # Admin is authenticated, load dashboard data
    categories = await upstream_client.get_categories()
    channels = await upstream_client.get_all_channels()
    health = await upstream_client.check_upstream_health_detailed()

    return _render_dashboard_page(
        admin_user=admin_payload.get("sub", "admin"),
        categories=categories,
        channels=channels,
        health=health,
        cache_size=cache.size(),
    )


@admin_web_router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    token = request.cookies.get("admin_token")
    if token and verify_admin_token(token):
        return RedirectResponse(url="/admin")
    return _render_login_page()


def _render_login_page() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LiveWave TV - Admin Login</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-primary: #0a0e17;
      --card-bg: rgba(18, 24, 38, 0.85);
      --card-border: rgba(255, 255, 255, 0.1);
      --primary: #3b82f6;
      --primary-glow: rgba(59, 130, 246, 0.5);
      --accent-purple: #8b5cf6;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
    }
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: 'Plus Jakarta Sans', sans-serif;
    }
    body {
      background: radial-gradient(circle at 50% 20%, #1e1b4b 0%, #0a0e17 70%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--text-main);
      padding: 20px;
    }
    .login-container {
      width: 100%;
      max-width: 420px;
      background: var(--card-bg);
      backdrop-filter: blur(16px);
      border: 1px solid var(--card-border);
      border-radius: 24px;
      padding: 40px 32px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
    }
    .logo-badge {
      width: 58px;
      height: 58px;
      background: linear-gradient(135deg, var(--primary), var(--accent-purple));
      border-radius: 18px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 20px;
      box-shadow: 0 0 25px var(--primary-glow);
    }
    .logo-badge svg {
      width: 28px;
      height: 28px;
      fill: white;
    }
    h1 {
      font-size: 24px;
      font-weight: 800;
      text-align: center;
      letter-spacing: -0.5px;
      margin-bottom: 6px;
    }
    .subtitle {
      color: var(--text-muted);
      text-align: center;
      font-size: 13px;
      margin-bottom: 30px;
    }
    .form-group {
      margin-bottom: 18px;
    }
    label {
      display: block;
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    input {
      width: 100%;
      padding: 13px 16px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      color: white;
      font-size: 14px;
      outline: none;
      transition: all 0.2s ease;
    }
    input:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
      background: rgba(255, 255, 255, 0.08);
    }
    .btn-submit {
      width: 100%;
      padding: 14px;
      background: linear-gradient(135deg, #3b82f6, #6366f1);
      border: none;
      border-radius: 12px;
      color: white;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
      margin-top: 10px;
      transition: all 0.2s ease;
      box-shadow: 0 4px 15px rgba(59, 130, 246, 0.35);
    }
    .btn-submit:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
    }
    .credentials-hint {
      margin-top: 24px;
      padding: 12px 14px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px dashed rgba(255, 255, 255, 0.15);
      border-radius: 12px;
      font-size: 12px;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .fill-btn {
      background: rgba(59, 130, 246, 0.2);
      color: #60a5fa;
      border: none;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
    }
    .alert-error {
      display: none;
      padding: 12px;
      margin-bottom: 20px;
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.3);
      border-radius: 12px;
      color: #fca5a5;
      font-size: 13px;
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="login-container">
    <div class="logo-badge">
      <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
    </div>
    <h1>LiveWave TV</h1>
    <p class="subtitle">Admin Control Center</p>

    <div id="error-box" class="alert-error"></div>

    <form id="login-form">
      <div class="form-group">
        <label for="username">Username</label>
        <input type="text" id="username" name="username" value="admin" required autocomplete="username">
      </div>
      <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" name="password" value="admin1234" required autocomplete="current-password">
      </div>
      <button type="submit" class="btn-submit" id="submit-btn">Sign In to Dashboard</button>
    </form>

    <div class="credentials-hint">
      <span>Default: <b>admin</b> / <b>admin1234</b></span>
      <button class="fill-btn" onclick="fillDemo()">Auto-Fill</button>
    </div>
  </div>

  <script>
    function fillDemo() {
      document.getElementById('username').value = 'admin';
      document.getElementById('password').value = 'admin1234';
    }

    document.getElementById('login-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = document.getElementById('submit-btn');
      const errorBox = document.getElementById('error-box');
      errorBox.style.display = 'none';
      submitBtn.textContent = 'Verifying...';
      submitBtn.disabled = true;

      const username = document.getElementById('username').value.trim();
      const password = document.getElementById('password').value;

      try {
        const res = await fetch('/api/v1/admin/login', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({username, password})
        });

        const data = await res.json();
        if (res.ok && data.success) {
          window.location.href = '/admin';
        } else {
          errorBox.textContent = data.detail || 'Invalid username or password.';
          errorBox.style.display = 'block';
          submitBtn.textContent = 'Sign In to Dashboard';
          submitBtn.disabled = false;
        }
      } catch (err) {
        errorBox.textContent = 'Network error: ' + err.message;
        errorBox.style.display = 'block';
        submitBtn.textContent = 'Sign In to Dashboard';
        submitBtn.disabled = false;
      }
    });
  </script>
</body>
</html>"""


def _render_dashboard_page(
    admin_user: str,
    categories: list,
    channels: list,
    health: dict,
    cache_size: int,
) -> str:
    channels_json = json.dumps(channels)
    categories_json = json.dumps(categories)
    mirrors_json = json.dumps(health.get("tested_mirrors", []))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LiveWave TV - Admin Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <!-- HLS.js for direct in-browser stream playback -->
  <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
  <style>
    :root {{
      --bg: #090d16;
      --card: #111827;
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #3b82f6;
      --accent: #8b5cf6;
      --green: #10b981;
      --red: #ef4444;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}
    body {{ background-color: var(--bg); color: var(--text); min-height: 100vh; padding: 24px; }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 28px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--card-border);
    }}
    .brand {{ display: flex; align-items: center; gap: 14px; }}
    .brand-logo {{
      width: 44px; height: 44px;
      background: linear-gradient(135deg, var(--primary), var(--accent));
      border-radius: 12px;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
    }}
    .brand-logo svg {{ width: 22px; height: 22px; fill: white; }}
    .brand h1 {{ font-size: 20px; font-weight: 800; }}
    .brand span {{ font-size: 12px; color: var(--text-muted); }}
    .header-actions {{ display: flex; align-items: center; gap: 12px; }}
    .btn {{
      padding: 9px 16px; border-radius: 10px; font-size: 13px; font-weight: 600;
      border: 1px solid var(--card-border); cursor: pointer; transition: all 0.2s;
      background: rgba(255, 255, 255, 0.06); color: white; display: inline-flex; align-items: center; gap: 6px;
    }}
    .btn:hover {{ background: rgba(255, 255, 255, 0.12); }}
    .btn-primary {{ background: var(--primary); border-color: var(--primary); }}
    .btn-primary:hover {{ background: #2563eb; }}
    .btn-danger {{ background: rgba(239, 68, 68, 0.2); border-color: rgba(239, 68, 68, 0.4); color: #fca5a5; }}
    .btn-danger:hover {{ background: rgba(239, 68, 68, 0.35); }}

    /* Metrics Grid */
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }}
    .metric-card {{
      background: var(--card);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 20px;
    }}
    .metric-title {{ font-size: 12px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; }}
    .metric-val {{ font-size: 26px; font-weight: 800; margin-top: 8px; }}
    .metric-subtitle {{ font-size: 12px; color: var(--green); margin-top: 4px; display: flex; align-items: center; gap: 4px; }}

    /* Section layout */
    .section {{
      background: var(--card);
      border: 1px solid var(--card-border);
      border-radius: 18px;
      padding: 22px;
      margin-bottom: 28px;
    }}
    .section-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
    }}
    .section-title {{ font-size: 17px; font-weight: 700; }}

    /* Table */
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }}
    th {{ color: var(--text-muted); font-weight: 600; padding: 12px; border-bottom: 1px solid var(--card-border); }}
    td {{ padding: 14px 12px; border-bottom: 1px solid rgba(255, 255, 255, 0.04); vertical-align: middle; }}
    tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}

    .badge {{
      display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;
    }}
    .badge-green {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge-blue {{ background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }}
    .badge-red {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}

    /* Video Player Modal */
    .modal {{
      display: none; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.85);
      backdrop-filter: blur(8px); z-index: 1000; align-items: center; justify-content: center; padding: 20px;
    }}
    .modal.open {{ display: flex; }}
    .modal-box {{
      width: 100%; max-width: 720px; background: #111827; border: 1px solid var(--card-border);
      border-radius: 20px; overflow: hidden; box-shadow: 0 25px 50px rgba(0,0,0,0.8);
    }}
    .modal-header {{
      display: flex; justify-content: space-between; align-items: center; padding: 16px 20px;
      border-bottom: 1px solid var(--card-border);
    }}
    .modal-body {{ padding: 20px; }}
    video {{ width: 100%; aspect-ratio: 16/9; background: black; border-radius: 12px; outline: none; }}
  </style>
</head>
<body>
  <!-- Header -->
  <div class="header">
    <div class="brand">
      <div class="brand-logo">
        <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
      </div>
      <div>
        <h1>LiveWave TV Admin</h1>
        <span>Live Stream Management & System Status</span>
      </div>
    </div>
    <div class="header-actions">
      <span class="badge badge-blue">Admin: {admin_user}</span>
      <button class="btn" onclick="flushCache()">⚡ Flush Cache ({cache_size})</button>
      <button class="btn btn-danger" onclick="logout()">Sign Out</button>
    </div>
  </div>

  <!-- Metrics Grid -->
  <div class="metrics-grid">
    <div class="metric-card">
      <div class="metric-title">System Status</div>
      <div class="metric-val" style="color: var(--green);">Operational</div>
      <div class="metric-subtitle">FastAPI v1.1.0 • Live TV Engine</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Live Channels</div>
      <div class="metric-val">{len(channels)}</div>
      <div class="metric-subtitle">Across {len(categories)} categories</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Memory Cache</div>
      <div class="metric-val" id="metric-cache">{cache_size} entries</div>
      <div class="metric-subtitle">TTL: {settings.cache_ttl_seconds}s expiry</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Upstream Gateway</div>
      <div class="metric-val" style="font-size: 16px; margin-top: 14px; word-break: break-all;">
        {"Active Mirror" if health.get("upstream_available") else "Authorized Fallback"}
      </div>
      <div class="metric-subtitle">Failover & DRM-free HLS Active</div>
    </div>
  </div>

  <!-- Upstream Mirrors Monitor -->
  <div class="section">
    <div class="section-header">
      <div class="section-title">Yacine TV Upstream Mirrors Health</div>
      <button class="btn btn-primary" onclick="testMirrors()">🔄 Probe Mirrors Live</button>
    </div>
    <table>
      <thead>
        <tr>
          <th>Mirror URL</th>
          <th>Status</th>
          <th>HTTP Code</th>
          <th>Latency</th>
          <th>Decryption Status</th>
        </tr>
      </thead>
      <tbody id="mirrors-body">
        <!-- Rendered by JS -->
      </tbody>
    </table>
  </div>

  <!-- Channel Management -->
  <div class="section">
    <div class="section-header">
      <div class="section-title">Channel Catalog & Live Player Preview</div>
      <div style="display: flex; gap: 10px;">
        <input type="text" id="channel-search" placeholder="Filter channels..." oninput="filterChannels()" style="padding: 8px 12px; background: rgba(255,255,255,0.05); border: 1px solid var(--card-border); border-radius: 8px; color: white; outline: none; font-size: 13px;">
      </div>
    </div>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Category</th>
          <th>Format</th>
          <th>Stream URL</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody id="channels-body">
        <!-- Rendered by JS -->
      </tbody>
    </table>
  </div>

  <!-- Video Player Preview Modal -->
  <div class="modal" id="player-modal">
    <div class="modal-box">
      <div class="modal-header">
        <h3 id="modal-channel-title">Channel Stream Preview</h3>
        <button class="btn" onclick="closePlayerModal()">✕ Close</button>
      </div>
      <div class="modal-body">
        <video id="hls-video" controls autoplay playsinline></video>
        <div id="stream-diagnostics" style="margin-top: 12px; font-size: 12px; color: var(--text-muted);"></div>
      </div>
    </div>
  </div>

  <script>
    const channelsData = {channels_json};
    const categoriesData = {categories_json};
    const mirrorsData = {mirrors_json};
    let hlsInstance = null;

    function renderMirrors() {{
      const tbody = document.getElementById('mirrors-body');
      tbody.innerHTML = '';
      mirrorsData.forEach(m => {{
        const row = document.createElement('tr');
        row.innerHTML = `
          <td style="font-family: monospace; color: #60a5fa;">${{m.mirror}}</td>
          <td>${{m.reachable ? '<span class="badge badge-green">Connected</span>' : '<span class="badge badge-red">Unreachable / Parked</span>'}}</td>
          <td>${{m.status_code || 'Timeout'}}</td>
          <td>${{m.latency_ms}} ms</td>
          <td>${{m.reachable ? 'Valid Base64 XOR Payload' : 'Defunct or Sedo HTML'}}</td>
        `;
        tbody.appendChild(row);
      }});
    }}

    function renderChannels(list = channelsData) {{
      const tbody = document.getElementById('channels-body');
      tbody.innerHTML = '';
      list.forEach(c => {{
        const cat = categoriesData.find(k => k.id === c.category_id);
        const catName = cat ? cat.name : 'Channel';
        const row = document.createElement('tr');
        row.innerHTML = `
          <td><b>#${{c.id}}</b></td>
          <td>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span class="badge badge-blue">${{catName}}</span>
              <b>${{c.name}}</b>
            </div>
          </td>
          <td>${{catName}}</td>
          <td><span class="badge badge-green">HLS (.m3u8)</span></td>
          <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: monospace; font-size: 11px; color: var(--text-muted);">${{c.stream_url || 'N/A'}}</td>
          <td>
            <button class="btn btn-primary" style="padding: 5px 10px; font-size: 11px;" onclick="playStream('${{c.name}}', '${{c.stream_url}}')">▶ Play Stream</button>
            <button class="btn" style="padding: 5px 10px; font-size: 11px;" onclick="probeChannelHealth(${{c.id}})">⚡ Ping</button>
          </td>
        `;
        tbody.appendChild(row);
      }});
    }}

    function filterChannels() {{
      const q = document.getElementById('channel-search').value.toLowerCase();
      const filtered = channelsData.filter(c => c.name.toLowerCase().includes(q) || (c.description && c.description.toLowerCase().includes(q)));
      renderChannels(filtered);
    }}

    function playStream(name, url) {{
      document.getElementById('modal-channel-title').textContent = name + ' (Live HLS)';
      document.getElementById('stream-diagnostics').textContent = 'Stream: ' + url;
      const modal = document.getElementById('player-modal');
      const video = document.getElementById('hls-video');
      modal.classList.add('open');

      if (hlsInstance) {{
        hlsInstance.destroy();
      }}

      if (Hls.isSupported()) {{
        hlsInstance = new Hls();
        hlsInstance.loadSource(url);
        hlsInstance.attachMedia(video);
        hlsInstance.on(Hls.Events.MANIFEST_PARSED, function() {{
          video.play();
        }});
      }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
        video.src = url;
        video.play();
      }}
    }}

    function closePlayerModal() {{
      const modal = document.getElementById('player-modal');
      const video = document.getElementById('hls-video');
      video.pause();
      if (hlsInstance) {{
        hlsInstance.destroy();
        hlsInstance = null;
      }}
      modal.classList.remove('open');
    }}

    async function probeChannelHealth(id) {{
      try {{
        const res = await fetch(`/api/v1/channels/${{id}}/status`);
        const data = await res.json();
        alert(`Channel #${{id}} Stream Probe:\\n• Reachable: ${{data.is_reachable}}\\n• Latency: ${{data.latency_ms}}ms\\n• HTTP Status: ${{data.http_status}}\\n• HLS Format: ${{data.is_hls}}`);
      }} catch (e) {{
        alert('Stream probe request failed: ' + e);
      }}
    }}

    async function testMirrors() {{
      try {{
        const res = await fetch('/api/v1/admin/mirrors/test');
        const data = await res.json();
        mirrorsData.length = 0;
        data.tested_mirrors.forEach(m => mirrorsData.push(m));
        renderMirrors();
        alert('Mirror test complete! Active mirror: ' + (data.active_mirror || 'None'));
      }} catch (e) {{
        alert('Failed to probe mirrors: ' + e);
      }}
    }}

    async function flushCache() {{
      try {{
        const res = await fetch('/api/v1/admin/cache/flush', {{method: 'POST'}});
        const data = await res.json();
        document.getElementById('metric-cache').textContent = '0 entries';
        alert(data.message);
      }} catch (e) {{
        alert('Cache flush failed: ' + e);
      }}
    }}

    async function logout() {{
      await fetch('/api/v1/admin/logout', {{method: 'POST'}});
      window.location.href = '/admin/login';
    }}

    renderMirrors();
    renderChannels();
  </script>
</body>
</html>"""
