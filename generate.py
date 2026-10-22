"""
Sacred-timeline README generator for github.com/MarufxAlchemist

Writes assets/hero.svg, telemetry.svg, timeline.svg, orbit.svg, heartbeat.svg.
Live numbers (repos, stars, followers, contributions, weekly commits, streaks)
come from the GitHub GraphQL API when GH_TOKEN / GITHUB_TOKEN is set; otherwise
FALLBACK values are used.

Edit the CONTENT section below, then run:  python generate.py
"""
import datetime as dt
import json
import os
import random
import urllib.request
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets")

# ============================== CONTENT ==============================
USER = "MarufxAlchemist"
UPTIME_SINCE = dt.date(2023, 12, 9)

EYEBROW = "// incoming transmission · pune → nanjing"
FIRST, LAST = "MARUF", "NADAF"
TAGLINE = ["research software engineer · builder",
           "B.Tech CSE · 4th year · gamma-ray bursts"]
BOOT = [("ok", "mounting /universe"),
        ("ok", "loading gamma-ray catalog"),
        ("ok", "mac-mini online"),
        ("..", "waiting for next GRB")]

IDENTITY = [("OS", "Win · macOS · Linux"),
            ("Host", "PVPIT · B.Tech 4th yr"),
            ("Role", "Research SWE @ NJU"),
            ("Focus", "Gamma-ray bursts"),
            ("Uptime", "{uptime}")]
CONTACT = [("Mail", "maruffnadaf@gmail.com"),
           ("Web", "marufnadaf.vercel.app"),
           ("In", "in/maruf-nadaf"),
           ("IG", "mxruf.tf")]

# Sacred timeline. Years sit on the main line; branches leave and either
# merge back, stay active, or get pruned.
YEARS = ["2023", "2024", "2025", "2026", "2027"]
YOU_ARE_HERE = "2027"
# (label lines, segment index 0-3, side 'up'/'down', kind, lane)
BRANCHES = [
    (["Telegram Scraper"], 0, "up", "merged", 1),
    (["Science Day", "volunteer"], 0, "down", "pruned", 1),
    (["SIH"], 1, "up", "pruned", 2),
    (["Loreshire"], 1, "down", "merged", 2),
    (["Korat SEO"], 2, "up", "merged", 1),
    (["Monte-Carlo", "simulation"], 2, "down", "merged", 1),
    (["UIDAI"], 3, "up", "pruned", 2),
    (["ADAS / DMS"], 3, "up", "active", 1),
    (["Transient event", "detection · NJU"], 3, "down", "active", 1),
    (["GPS tracking system"], 3, "down", "pruned", 3),
]

# Skills in orbit: (name, ring 1-3, start angle in degrees)
SKILLS = [("Python", 1, 0), ("C++", 1, 180),
          ("PyTorch", 2, 60), ("TypeScript", 2, 240),
          ("Docker", 3, 20), ("AWS", 3, 140), ("Kafka", 3, 260)]
# Project constellation: (name, x, y, size, highlight)
PROJECTS = [("Loreshire", 70, 120, 4, False), ("AstroSentinel", 175, 55, 6, True),
            ("Risk Engine", 262, 100, 4, False), ("ADAS DMS", 230, 160, 3.5, False),
            ("Transient Detection", 95, 185, 3.5, False)]
CONSTELLATION_LINKS = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]

FALLBACK = {"repos": 13, "stars": 11, "followers": 6, "contribs": 726,
            "streak": 1, "best": 7, "weekly": [1, 2, 1, 3, 5, 2, 7, 8, 5, 3, 6, 2]}

# ============================== PALETTE ==============================
BG, PANEL, BORDER = "#060d0a", "#0a130f", "#1a2a21"
TEXT, SUB, DIM = "#d9e8de", "#8aa596", "#4a6656"
GREEN, MERGE, GOLD, PRUNED = "#2fd28a", "#1f9e68", "#d6b04c", "#6e8a7a"
MONO = "'JetBrains Mono','DejaVu Sans Mono',Menlo,Consolas,'Liberation Mono',monospace"
W = 840


# ============================== DATA ==============================
def gql(query, token):
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": query}).encode(),
                                 headers={"Authorization": f"bearer {token}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if "errors" in out:
        raise RuntimeError(out["errors"])
    return out["data"]


def fetch():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("no token -> fallback data")
        return dict(FALLBACK)
    s = {"stars": 0}
    cursor = None
    while True:
        after = f', after: "{cursor}"' if cursor else ""
        u = gql(f'''{{ user(login: "{USER}") {{ followers {{ totalCount }}
          repositories(first: 100, ownerAffiliations: OWNER{after}) {{ totalCount
            pageInfo {{ hasNextPage endCursor }} nodes {{ stargazerCount }} }} }} }}''', token)["user"]
        s["followers"] = u["followers"]["totalCount"]
        s["repos"] = u["repositories"]["totalCount"]
        s["stars"] += sum(n["stargazerCount"] for n in u["repositories"]["nodes"])
        if not u["repositories"]["pageInfo"]["hasNextPage"]:
            break
        cursor = u["repositories"]["pageInfo"]["endCursor"]
    days = []
    total = 0
    today = dt.date.today()
    for year in range(UPTIME_SINCE.year, today.year + 1):
        c = gql(f'''{{ user(login: "{USER}") {{ contributionsCollection(
              from: "{year}-01-01T00:00:00Z", to: "{year}-12-31T23:59:59Z") {{
              contributionCalendar {{ totalContributions
                weeks {{ contributionDays {{ date contributionCount }} }} }} }} }} }}''', token)
        cal = c["user"]["contributionsCollection"]["contributionCalendar"]
        total += cal["totalContributions"]
        for wk in cal["weeks"]:
            for d in wk["contributionDays"]:
                dd = dt.date.fromisoformat(d["date"])
                if dd <= today:
                    days.append((dd, d["contributionCount"]))
    days.sort()
    s["contribs"] = total
    # streaks
    best = cur = 0
    for _, n in days:
        cur = cur + 1 if n > 0 else 0
        best = max(best, cur)
    streak = 0
    for i, (d, n) in enumerate(reversed(days)):
        if n > 0:
            streak += 1
        elif i == 0:      # today may still be empty
            continue
        else:
            break
    s["streak"], s["best"] = streak, best
    # last 12 weeks (rolling 7-day buckets ending today)
    counts = {d: n for d, n in days}
    weekly = []
    for wk in range(11, -1, -1):
        end = today - dt.timedelta(days=7 * wk)
        weekly.append(sum(counts.get(end - dt.timedelta(days=k), 0) for k in range(7)))
    s["weekly"] = weekly
    return s


def uptime():
    t = dt.date.today()
    y, m, d = t.year - UPTIME_SINCE.year, t.month - UPTIME_SINCE.month, t.day - UPTIME_SINCE.day
    if d < 0:
        m -= 1
        d += (t.replace(day=1) - dt.timedelta(days=1)).day
    if m < 0:
        y -= 1
        m += 12
    return f"{y}y {m}m {d}d"


# ============================== SVG HELPERS ==============================
def esc(s):
    return escape(s, quote=False)


def doc(h, body, extra_css=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="{MONO}">
<style>
text{{white-space:pre}}
.t{{fill:{TEXT}}}.s{{fill:{SUB}}}.d{{fill:{DIM}}}.g{{fill:{GREEN}}}.au{{fill:{GOLD}}}.p{{fill:{PRUNED}}}
@keyframes show{{to{{opacity:1}}}}
@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
@keyframes twinkle{{0%,100%{{opacity:.25}}50%{{opacity:1}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}
{extra_css}
</style>
<rect x="0.5" y="0.5" width="{W-1}" height="{h-1}" rx="14" fill="{BG}" stroke="{BORDER}"/>
{body}
</svg>'''


def header(num, title, y=34):
    x_line = 24 + (len(num) + len(title) + 2) * 7.3 + 10
    return (f'<text x="24" y="{y}" font-size="12"><tspan class="au">{num}</tspan>'
            f'<tspan class="s">  {esc(title)}</tspan></text>'
            f'<line x1="{x_line:.0f}" y1="{y-4}" x2="{W-24}" y2="{y-4}" stroke="{BORDER}"/>')


def panel(x, y, w, h, title=None):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{PANEL}" stroke="{BORDER}"/>'
    if title:
        s += f'<text x="{x+16}" y="{y+24}" font-size="12" class="au">{esc(title)}</text>'
    return s


def stars(n, x0, y0, x1, y1, seed, avoid=None):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        if avoid and avoid[0] < x < avoid[2] and avoid[1] < y < avoid[3]:
            continue
        r = rnd.choice([0.8, 1, 1, 1.3, 1.6])
        col = rnd.choice([BORDER, BORDER, "#24412f", GREEN, GOLD] if i % 5 else [GREEN])
        dur = rnd.uniform(2.5, 6)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{col}" '
                   f'style="animation:twinkle {dur:.1f}s ease-in-out {rnd.uniform(0, 4):.1f}s infinite"/>')
    return "".join(out)


# ============================== HERO ==============================
TONE_STOPS = [(0.0, (46, 120, 86)), (0.22, (80, 175, 125)), (0.45, (160, 215, 185)),
              (0.7, (222, 240, 230)), (1.0, (252, 255, 253))]


def tone_hex(t, fade):
    for (a, ca), (b, cb) in zip(TONE_STOPS, TONE_STOPS[1:]):
        if t <= b:
            k = (t - a) / (b - a)
            c = [ca[i] + (cb[i] - ca[i]) * k for i in range(3)]
            break
    bg = (6, 13, 10)
    c = [bg[i] + (c[i] - bg[i]) * fade for i in range(3)]
    return "#%02x%02x%02x" % tuple(int(v) for v in c)


def hero():
    art = open(os.path.join(HERE, "portrait.txt")).read().split("\n")
    tones = open(os.path.join(HERE, "portrait_tone.txt")).read().split("\n")
    cols = max(len(r) for r in art)
    fs, lh = 7.5, 9.0
    cw = fs * 0.602
    pw = cols * cw
    px = W - pw - 26
    py = 30
    rows = len(art)
    fade_start = int(rows * 0.70)
    lines = []
    for r, row in enumerate(art):
        row = row.ljust(cols)
        trow = tones[r].ljust(cols)
        fade = 1.0 if r < fade_start else max(0.15, 1 - (r - fade_start) / (rows - fade_start) * 0.85)
        spans, cur, buf = [], None, ""
        for ch, tc in zip(row, trow):
            col = None if ch == " " else tone_hex(int(tc) / 9 if tc != " " else 0.5, fade)
            if col != cur and buf:
                spans.append((cur, buf))
                buf = ""
            cur = col
            buf += ch
        if buf:
            spans.append((cur, buf))
        inner = "".join(f'<tspan fill="{c}">{esc(b)}</tspan>' if c else esc(b) for c, b in spans)
        y = py + (r + 1) * lh
        lines.append(f'<text x="{px:.1f}" y="{y:.1f}" font-size="{fs}" font-weight="700" textLength="{pw:.1f}" '
                     f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{inner}</text>')
    # accretion disk below the portrait
    disk = ["  ·   .░▒▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒░.   ·  ",
            "░▒▓█████████▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█████████▓▒░",
            "        ▀▀▀▀▀▀▀▀▀▀▀▀▀   ●   ▀▀▀▀▀▀▀▀▀▀▀▀▀        "]
    dlen = max(len(d) for d in disk)
    dfs = 8.5
    dw = dlen * dfs * 0.602
    dx = px + (pw - dw) / 2
    dy0 = py + (rows + 1.6) * lh
    disk_svg = []
    for i, d in enumerate(disk):
        spans, cur, buf = [], None, ""
        for ch in d.ljust(dlen):
            col = GOLD if ch in "░▒▓█" else (DIM if ch in "▀·." else (GREEN if ch == "●" else None))
            if col != cur and buf:
                spans.append((cur, buf)); buf = ""
            cur = col; buf += ch
        spans.append((cur, buf))
        inner = "".join(f'<tspan fill="{c}">{esc(b)}</tspan>' if c else esc(b) for c, b in spans)
        disk_svg.append(f'<text x="{dx:.1f}" y="{dy0 + i*10.5:.1f}" font-size="{dfs}" textLength="{dw:.1f}" '
                        f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{inner}</text>')
    H = int(dy0 + 3 * 10.5 + 22)

    # left column
    lx = 40
    left = [f'<text x="{lx}" y="118" font-size="12" class="d">{esc(EYEBROW)}</text>',
            f'<text x="{lx}" y="192" font-size="62" font-weight="700" class="g" letter-spacing="4">{FIRST}</text>',
            f'<text x="{lx}" y="260" font-size="62" font-weight="700" class="t" letter-spacing="4">{LAST}</text>',
            f'<rect x="{lx + len(LAST)*41.3 + 6:.0f}" y="214" width="24" height="50" fill="{GOLD}" style="animation:blink 1.1s step-end infinite"/>']
    for i, t in enumerate(TAGLINE):
        left.append(f'<text x="{lx}" y="{304 + i*20}" font-size="13" class="s">{esc(t)}</text>')
    by = 392
    for i, (st, msg) in enumerate(BOOT):
        delay = 0.6 + i * 0.6
        stc = "g" if st == "ok" else "au"
        left.append(f'<text x="{lx}" y="{by + i*21}" font-size="13" style="opacity:0;animation:show .01s linear {delay:.1f}s forwards">'
                    f'<tspan class="d">[ </tspan><tspan class="{stc}">{st}</tspan><tspan class="d"> ]</tspan>'
                    f'<tspan class="t"> {esc(msg)}</tspan></text>')
    last_len = len(f"[ .. ] {BOOT[-1][1]}")
    cy = by + (len(BOOT) - 1) * 21
    left.append(f'<rect x="{lx + last_len*7.83 + 4:.0f}" y="{cy-11}" width="8" height="14" fill="{GREEN}" '
                f'style="opacity:0;animation:show .01s linear {0.6 + len(BOOT)*0.6:.1f}s forwards, blink 1s step-end {0.6 + len(BOOT)*0.6:.1f}s infinite"/>')
    left.insert(0, f'<text x="{lx}" y="{by - 26}" font-size="13"><tspan class="d">$</tspan><tspan class="t"> ./boot --user maruf</tspan></text>')

    body = (stars(70, 10, 10, W - 10, H - 10, 7, avoid=(px - 10, py, px + pw, py + rows * lh))
            + "".join(left)
            + f'<defs><clipPath id="reveal"><rect x="{px-4:.0f}" y="{py}" width="{pw+8:.0f}" height="0">'
              f'<animate attributeName="height" from="0" to="{H}" dur="2.6s" begin="0.2s" fill="freeze"/></rect></clipPath></defs>'
            + f'<g clip-path="url(#reveal)">' + "".join(lines) + "".join(disk_svg) + "</g>"
            + f'<rect x="{px-4:.0f}" y="{py}" width="{pw+8:.0f}" height="2" fill="{GREEN}" opacity="0">'
              f'<animate attributeName="y" from="{py}" to="{H-20}" dur="2.6s" begin="0.2s" fill="freeze"/>'
              f'<animate attributeName="opacity" values="0;.8;.8;0" keyTimes="0;.05;.9;1" dur="2.6s" begin="0.2s" fill="freeze"/></rect>')
    return doc(H, body)


# ============================== TELEMETRY ==============================
def kv_lines(x, y, items, keyw):
    out = []
    for i, (k, v) in enumerate(items):
        v = v.replace("{uptime}", uptime())
        dots = "." * (keyw - len(k) - 1)
        out.append(f'<text x="{x}" y="{y + i*22}" font-size="12" xml:space="preserve">'
                   f'<tspan class="au">{esc(k)}</tspan><tspan class="d"> {dots} </tspan>'
                   f'<tspan class="g">{esc(v)}</tspan></text>')
    return "".join(out)


def telemetry(s):
    H = 222
    pw = (W - 48 - 28) / 3
    xs = [24 + i * (pw + 14) for i in range(3)]
    y = 50
    body = header("01", "telemetry")
    body += panel(xs[0], y, pw, 152, "identity") + kv_lines(xs[0] + 16, y + 52, IDENTITY, 8)
    body += panel(xs[1], y, pw, 152, "contact") + kv_lines(xs[1] + 16, y + 52, CONTACT, 6)
    body += panel(xs[2], y, pw, 152, "github")
    stats = [(s["repos"], "repos"), (s["stars"], "stars"), (s["contribs"], "contributions"), (s["followers"], "followers")]
    for i, (n, lbl) in enumerate(stats):
        cx = xs[2] + 16 + (i % 2) * (pw / 2)
        cy = y + 66 + (i // 2) * 54
        body += (f'<text x="{cx:.0f}" y="{cy}" font-size="28" font-weight="700" class="g">{n:,}</text>'
                 f'<text x="{cx:.0f}" y="{cy+18}" font-size="11" class="d">{lbl}</text>')
    return doc(H, body)


# ============================== TIMELINE ==============================
def timeline():
    H = 400
    body = header("02", "sacred timeline")
    px, py, pwid, ph = 24, 50, W - 48, 330
    body += panel(px, py, pwid, ph)
    x0, x1 = 64, W - 74
    my = py + 150
    seg = (x1 - x0) / (len(YEARS) - 1)
    nodes = [x0 + i * seg for i in range(len(YEARS))]
    lanes_up = {1: 42, 2: 82, 3: 112}
    lanes_dn = {1: 44, 2: 78, 3: 112}
    parts = []
    labels = []
    # count branches per segment to stagger start points
    for idx, (lab, si, side, kind, lane) in enumerate(BRANCHES):
        a, b = nodes[si], nodes[si + 1]
        # outer branches leave first so lines never cross
        same = sorted([br for br in BRANCHES if br[1] == si and br[2] == side], key=lambda br: -br[4])
        k = same.index((lab, si, side, kind, lane))
        start = a + 26 + k * 16 + (6 if side == "down" else 0)
        dy = -(lanes_up[lane]) if side == "up" else lanes_dn[lane]
        yb = my + dy
        c = 16
        if kind == "merged":
            end = b - 26 if si < 3 else b - 30
            d = (f"M{start:.0f} {my} C{start+c:.0f} {my} {start+c:.0f} {yb} {start+2*c:.0f} {yb} "
                 f"L{end-2*c:.0f} {yb} C{end-c:.0f} {yb} {end-c:.0f} {my} {end:.0f} {my}")
            stroke = f'stroke="{MERGE}" stroke-width="2"'
            lx = start + 2 * c
        else:
            if kind == "active":
                end = b - 36
            else:
                end = start + 2 * c + max(70, len(max(lab, key=len)) * 4)
                if lane == 3 and side == "down":
                    end = start + 150
            if lane == 3 and kind == "pruned" and side == "down":
                d = f"M{start:.0f} {my} L{start:.0f} {yb-10} Q{start:.0f} {yb} {start+10:.0f} {yb} L{end:.0f} {yb}"
            else:
                d = f"M{start:.0f} {my} C{start+c:.0f} {my} {start+c:.0f} {yb} {start+2*c:.0f} {yb} L{end:.0f} {yb}"
            if kind == "active":
                stroke = f'stroke="{GREEN}" stroke-width="2"'
            else:
                stroke = f'stroke="{DIM}" stroke-width="1.6" stroke-dasharray="4 4"'
            lx = start + 2 * c if not (lane == 3 and side == "down") else start + 14
        delay = 0.8 + 0.25 * idx
        parts.append(f'<g style="opacity:0;animation:show .5s ease {delay:.2f}s forwards"><path d="{d}" fill="none" {stroke}/>')
        if kind == "pruned":
            ex = end + 6
            parts.append(f'<path d="M{ex-5:.0f} {yb-5} L{ex+5:.0f} {yb+5} M{ex+5:.0f} {yb-5} L{ex-5:.0f} {yb+5}" stroke="{SUB}" stroke-width="2"/>')
        if kind == "active":
            parts.append(f'<circle cx="{end+5:.0f}" cy="{yb}" r="5" fill="{PANEL}" stroke="{GREEN}" stroke-width="2" '
                         f'style="animation:pulse 1.8s ease-in-out infinite"/>')
        cls = "p" if kind == "pruned" else "t"
        if lane == 3 and side == "down":
            ly = yb + 20
        elif side == "up":
            ly = yb - 10 - 15 * (len(lab) - 1)
        else:
            ly = yb + 20
        for j, t in enumerate(lab):
            parts.append(f'<text x="{lx:.0f}" y="{ly + j*15:.0f}" font-size="12" class="{cls}">{esc(t)}</text>')
        parts.append("</g>")
    total = x1 - x0
    main = (f'<path d="M{x0} {my} L{x1} {my}" stroke="{GREEN}" stroke-width="3" fill="none" '
            f'stroke-dasharray="{total}" stroke-dashoffset="{total}">'
            f'<animate attributeName="stroke-dashoffset" from="{total}" to="0" dur="1.4s" begin="0.1s" fill="freeze"/></path>')
    nd = ""
    for i, (x, yr) in enumerate(zip(nodes, YEARS)):
        if yr == YOU_ARE_HERE:
            nd += (f'<circle cx="{x:.0f}" cy="{my}" r="6" fill="{GOLD}"/>'
                   f'<circle cx="{x:.0f}" cy="{my}" r="13" fill="none" stroke="{GOLD}" stroke-width="2" style="animation:pulse 2.2s ease-in-out infinite"/>'
                   f'<text x="{x:.0f}" y="{my+30}" font-size="13" text-anchor="middle" class="au" font-weight="700">{yr}</text>'
                   f'<text x="{x+22:.0f}" y="{my-20}" font-size="12" text-anchor="end" class="au">you are here</text>')
        else:
            nd += (f'<circle cx="{x:.0f}" cy="{my}" r="9" fill="{PANEL}" stroke="{GREEN}" stroke-width="2.5"/>'
                   f'<text x="{x:.0f}" y="{my+30}" font-size="13" text-anchor="middle" class="s">{yr}</text>')
    # legend
    ly = py + ph - 20
    lg = (f'<path d="M{px+20} {ly-4} H{px+48}" stroke="{MERGE}" stroke-width="2"/>'
          f'<text x="{px+56}" y="{ly}" font-size="12" class="s">merged back</text>'
          f'<path d="M{px+170} {ly-4} H{px+192}" stroke="{GREEN}" stroke-width="2"/>'
          f'<circle cx="{px+197}" cy="{ly-4}" r="4" fill="{PANEL}" stroke="{GREEN}" stroke-width="2"/>'
          f'<text x="{px+210}" y="{ly}" font-size="12" class="s">active</text>'
          f'<path d="M{px+290} {ly-4} H{px+316}" stroke="{DIM}" stroke-width="1.6" stroke-dasharray="4 4"/>'
          f'<path d="M{px+320} {ly-8} L{px+328} {ly} M{px+328} {ly-8} L{px+320} {ly}" stroke="{SUB}" stroke-width="2"/>'
          f'<text x="{px+338}" y="{ly}" font-size="12" class="s">pruned</text>'
          f'<text x="{px+pwid-74}" y="{ly}" font-size="12" text-anchor="end" class="d">timeline integrity:</text>'
          f'<text x="{px+pwid-20}" y="{ly}" font-size="12" text-anchor="end" class="g">stable</text>')
    body += "".join(parts) + main + nd + lg
    return doc(H, body)


# ============================== ORBIT + CONSTELLATION ==============================
def orbit():
    H = 340
    y = 50
    pw = (W - 48 - 14) / 2
    body = header("03", "orbit and constellation")
    body += panel(24, y, pw, 272, "skills in orbit")
    cx, cy = 24 + pw / 2, y + 142
    radii = {1: 44, 2: 72, 3: 100}
    body += "".join(f'<circle cx="{cx:.0f}" cy="{cy}" r="{r}" fill="none" stroke="#1f3328"/>' for r in radii.values())
    body += f'<circle cx="{cx:.0f}" cy="{cy}" r="7" fill="{GOLD}"/><circle cx="{cx:.0f}" cy="{cy}" r="12" fill="none" stroke="{GOLD}" stroke-opacity=".35"/>'
    periods = {1: 24, 2: 40, 3: 60}
    import math
    for name, ring, ang in SKILLS:
        r = radii[ring]
        per = periods[ring]
        a = math.radians(ang)
        sx, sy = cx + r * math.cos(a), cy + r * math.sin(a)
        dx, dy = -2 * r * math.cos(a), -2 * r * math.sin(a)
        path = f"M0 0 A{r} {r} 0 1 1 {dx:.1f} {dy:.1f} A{r} {r} 0 1 1 0 0"
        body += (f'<g transform="translate({sx:.1f} {sy:.1f})"><g><circle r="5" fill="{GREEN}"/>'
                 f'<text x="9" y="4" font-size="12" class="t">{esc(name)}</text>'
                 f'<animateMotion dur="{per}s" repeatCount="indefinite" path="{path}"/></g></g>')
    body += f'<text x="{24+16}" y="{y+260}" font-size="11" class="d">inner ring = daily drivers</text>'

    x2 = 24 + pw + 14
    body += panel(x2, y, pw, 272, "project constellation")
    ox, oy = x2 + 20, y + 40
    pts = [(ox + p[1], oy + p[2]) for p in PROJECTS]
    for a, b in CONSTELLATION_LINKS:
        body += (f'<line x1="{pts[a][0]:.0f}" y1="{pts[a][1]:.0f}" x2="{pts[b][0]:.0f}" y2="{pts[b][1]:.0f}" '
                 f'stroke="#24412f" stroke-dasharray="3 4"/>')
    body += stars(26, x2 + 10, y + 34, x2 + pw - 10, y + 250, 3)
    for (name, _, _, size, hl), (px, py) in zip(PROJECTS, pts):
        body += f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{size}" fill="{GREEN}"/>'
        if hl:
            body += f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{size+7}" fill="none" stroke="{GOLD}" stroke-width="1.5" style="animation:pulse 2.4s ease-in-out infinite"/>'
        body += f'<text x="{px + size + 8:.0f}" y="{py + 4:.0f}" font-size="12" class="t">{esc(name)}</text>'
    body += f'<text x="{x2+16}" y="{y+260}" font-size="11" class="d">brightest star = flagship project</text>'
    return doc(H, body)


# ============================== HEARTBEAT ==============================
def heartbeat(s):
    H = 150
    y = 50
    body = header("04", "heartbeat")
    body += panel(24, y, W - 48, 84)
    wk = s["weekly"]
    mx = max(wk) or 1
    bx, base, bw, gap, hmax = 44, y + 66, 26, 10, 46
    for i, n in enumerate(wk):
        h = max(2, n / mx * hmax)
        col = GOLD if i == len(wk) - 1 else GREEN
        body += (f'<rect x="{bx + i*(bw+gap)}" y="{base - h:.1f}" width="{bw}" height="{h:.1f}" rx="2" fill="{col}">'
                 f'<animate attributeName="height" from="0" to="{h:.1f}" dur=".8s" begin="{0.1 + i*0.06:.2f}s" fill="freeze"/>'
                 f'<animate attributeName="y" from="{base}" to="{base - h:.1f}" dur=".8s" begin="{0.1 + i*0.06:.2f}s" fill="freeze"/></rect>')
    body += f'<text x="{bx}" y="{base + 14}" font-size="11" class="d">commits per week · last 12 weeks</text>'
    chips = [(f"streak {s['streak']}d", SUB, BORDER), (f"best {s['best']}d", SUB, BORDER), ("timeline stable", GREEN, GREEN)]
    x = W - 44
    for label, fg, br in reversed(chips):
        wdt = len(label) * 7.3 + 20
        x -= wdt
        body += (f'<rect x="{x:.0f}" y="{y+30}" width="{wdt:.0f}" height="26" rx="5" fill="none" stroke="{br}"/>'
                 f'<text x="{x + wdt/2:.0f}" y="{y+47}" font-size="12" text-anchor="middle" fill="{fg}">{esc(label)}</text>')
        x -= 10
    return doc(H, body)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    try:
        stats = fetch()
    except Exception as e:
        print("stats fetch failed, using fallback:", e)
        stats = dict(FALLBACK)
    files = {"hero.svg": hero(), "telemetry.svg": telemetry(stats), "timeline.svg": timeline(),
             "orbit.svg": orbit(), "heartbeat.svg": heartbeat(stats)}
    for name, svg in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(svg)
    print("wrote", ", ".join(files), "|", {k: v for k, v in stats.items() if k != "weekly"})
