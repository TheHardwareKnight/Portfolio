async function hashPassword(password) {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
}

const LOGIN_PAGE = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>Control Panel — Login</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #0a0a0a; color: #f0ede6;
      font-family: 'Space Mono', monospace;
      display: flex; align-items: center; justify-content: center;
      min-height: 100vh;
    }
    .box { border: 1px solid #222; padding: 2.5rem; width: 360px; background: #141414; }
    h1 { color: #e8ff47; font-size: 1rem; letter-spacing: 0.2em; margin-bottom: 2rem; }
    input {
      width: 100%; background: #0a0a0a; border: 1px solid #333;
      color: #f0ede6; padding: 0.75rem 1rem; font-family: inherit;
      font-size: 0.9rem; margin-bottom: 1rem; outline: none;
    }
    input:focus { border-color: #e8ff47; }
    button {
      width: 100%; background: #e8ff47; color: #0a0a0a;
      border: none; padding: 0.75rem; font-family: inherit;
      font-size: 0.9rem; font-weight: 700; cursor: pointer;
      letter-spacing: 0.1em;
    }
    button:hover { background: #d4eb3a; }
    .error { color: #ff4747; font-size: 0.8rem; margin-top: 1rem; }
  </style>
</head>
<body>
  <div class="box">
    <h1>// CONTROL PANEL</h1>
    <input type="password" id="pw" placeholder="Password" />
    <button onclick="login()">ENTER</button>
    <div class="error" id="err"></div>
  </div>
  <script>
    async function hashPw(password) {
      const enc = new TextEncoder().encode(password);
      const buf = await crypto.subtle.digest("SHA-256", enc);
      return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2,"0")).join("");
    }
    async function login() {
      const pw = document.getElementById("pw").value;
      const hash = await hashPw(pw);
      const res = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hash })
      });
      if (res.ok) {
        window.location.href = "/dashboard";
      } else {
        document.getElementById("err").textContent = "Incorrect password.";
      }
    }
    document.getElementById("pw").addEventListener("keydown", e => {
      if (e.key === "Enter") login();
    });
  </script>
</body>
</html>`;

const DASHBOARD_PAGE = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>Control Panel</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #0a0a0a; color: #f0ede6; font-family: 'Space Mono', monospace; padding: 2rem; }
    h1 { color: #e8ff47; font-size: 1rem; letter-spacing: 0.2em; margin-bottom: 2rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; margin-bottom: 1rem; }
    .card { border: 1px solid #222; background: #141414; padding: 1.5rem; }
    .label { color: #555; font-size: 0.75rem; letter-spacing: 0.1em; margin-bottom: 0.5rem; text-transform: uppercase; }
    .value { font-size: 1.1rem; color: #e8ff47; }
    .value.normal { color: #f0ede6; }
    #log { max-height: 300px; overflow-y: auto; }
    .entry { border-bottom: 1px solid #1a1a1a; padding: 0.5rem 0; font-size: 0.8rem; color: #888; }
    .entry span { color: #555; margin-right: 1rem; }
    .status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #e8ff47; margin-right: 0.5rem; animation: pulse 2s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
    .logout { float: right; background: none; border: 1px solid #333; color: #555; padding: 0.4rem 0.8rem; font-family: inherit; font-size: 0.75rem; cursor: pointer; letter-spacing: 0.1em; }
    .logout:hover { border-color: #ff4747; color: #ff4747; }
  </style>
</head>
<body>
  <h1><span class="status-dot"></span>// CONTROL PANEL <button class="logout" onclick="logout()">LOGOUT</button></h1>
  <div class="grid">
    <div class="card">
      <div class="label">Status</div>
      <div class="value" id="status">Waiting...</div>
    </div>
    <div class="card">
      <div class="label">Last Seen</div>
      <div class="value normal" id="lastseen">—</div>
    </div>
    <div class="card">
      <div class="label">Latest Payload</div>
      <pre class="value normal" id="latest" style="font-size:0.8rem;white-space:pre-wrap;">—</pre>
    </div>
  </div>
  <div class="card">
    <div class="label">Event Log</div>
    <div id="log"><div class="entry">No events yet.</div></div>
  </div>
  <script>
    async function fetchData() {
      const res = await fetch("/data");
      if (res.status === 401) { window.location.href = "/"; return; }
      const json = await res.json();
      document.getElementById("status").textContent = json.latest ? "Connected" : "No data yet";
      document.getElementById("lastseen").textContent = json.lastSeen || "—";
      document.getElementById("latest").textContent = json.latest ? JSON.stringify(json.latest, null, 2) : "—";
      const log = document.getElementById("log");
      if (json.log && json.log.length > 0) {
        log.innerHTML = json.log.slice().reverse().map(e =>
          '<div class="entry"><span>' + e.time + '</span>' + e.msg + '</div>'
        ).join("");
      }
    }
    async function logout() {
      await fetch("/logout");
      window.location.href = "/";
    }
    fetchData();
    setInterval(fetchData, 5000);
  </script>
</body>
</html>`;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const cookie = request.headers.get("Cookie") || "";
    const authed = cookie.includes("auth=1");

    // Login endpoint
    if (url.pathname === "/login" && request.method === "POST") {
      const body = await request.json();
      const correctHash = await hashPassword("ehs508");
      if (body.hash === correctHash) {
        return new Response("OK", {
          headers: {
            "Set-Cookie": "auth=1; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=86400"
          }
        });
      }
      return new Response("Unauthorized", { status: 401 });
    }

    // Logout
    if (url.pathname === "/logout") {
      return new Response("", {
        headers: {
          "Set-Cookie": "auth=; Path=/; HttpOnly; Secure; Max-Age=0",
          "Location": "/"
        },
        status: 302
      });
    }

    // Dashboard (protected)
    if (url.pathname === "/dashboard") {
      if (!authed) return Response.redirect(new URL("/", request.url).href, 302);
      return new Response(DASHBOARD_PAGE, { headers: { "Content-Type": "text/html" } });
    }

    // Pi data ingest — uses token auth so the Pi doesn't need a cookie
    if (url.pathname === "/ingest" && request.method === "POST") {
      const token = request.headers.get("X-Pi-Token");
      const correctToken = await hashPassword("ehs508");
      if (token !== correctToken) return new Response("Unauthorized", { status: 401 });

      const data = await request.json();
      const stored = await env.CONTROL_KV.get("pidata");
      const existing = stored ? JSON.parse(stored) : { latest: null, log: [], lastSeen: null };

      existing.latest = data;
      existing.lastSeen = new Date().toISOString();
      existing.log = existing.log || [];
      existing.log.push({ time: new Date().toISOString(), msg: JSON.stringify(data) });
      if (existing.log.length > 50) existing.log = existing.log.slice(-50);

      await env.CONTROL_KV.put("pidata", JSON.stringify(existing));
      return new Response("OK");
    }

    // Data fetch for dashboard
    if (url.pathname === "/data") {
      if (!authed) return new Response("Unauthorized", { status: 401 });
      const stored = await env.CONTROL_KV.get("pidata");
      const data = stored ? JSON.parse(stored) : { latest: null, log: [], lastSeen: null };
      return new Response(JSON.stringify(data), {
        headers: { "Content-Type": "application/json" }
      });
    }

    // Root — redirect to dashboard if already logged in
    if (authed && url.pathname === "/") {
      return Response.redirect(new URL("/dashboard", request.url).href, 302);
    }

    return new Response(LOGIN_PAGE, { headers: { "Content-Type": "text/html" } });
  }
};
