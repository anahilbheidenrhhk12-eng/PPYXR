"""Design system for the private PPYXR administration portal.

Standalone CSS / JavaScript served from /admin/assets.
No external fonts, CDN scripts or third-party resources are needed.
"""
import html

ICONS = {
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    "layers": '<rect x="3" y="3" width="18" height="14" rx="2"/><path d="m7 21 5-4 5 4"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v7c0 1.7 4 3 9 3s9-1.3 9-3V5M3 12v7c0 1.7 4 3 9 3s9-1.3 9-3v-7"/>',
    "upload": '<path d="M12 16V3m-5 5 5-5 5 5"/><path d="M4 16v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4"/>',
    "settings": '<path d="M12 3v2m0 14v2M4.5 4.5 6 6m12 12 1.5 1.5M3 12h2m14 0h2M4.5 19.5 6 18M18 6l1.5-1.5"/><circle cx="12" cy="12" r="4"/>',
    "bolt": '<path d="M13 2 4 13h7l-1 9 10-12h-7l0-8Z"/>',
    "search": '<circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 5 5"/>',
    "chevron": '<path d="m9 18 6-6-6-6"/>',
    "arrow": '<path d="M5 12h14m-7-7 7 7-7 7"/>',
    "download": '<path d="M12 3v12m-5-5 5 5 5-5M4 17v3h16v-3"/>',
    "trash": '<path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14M10 11v6m4-6v6"/>',
    "edit": '<path d="m13 5 6 6M4 20l5-1 11-11-5-5L4 14v6Z"/>',
    "file": '<path d="M6 2h8l5 5v15H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z"/><path d="M14 2v6h6M8 13h8M8 17h8"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="9" cy="9" r="2"/><path d="m4 17 5-5 4 4 3-3 5 5"/>',
    "check": '<path d="m4 12 5 5 11-11"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 3"/>',
    "shield": '<path d="M12 2 4 6v6c0 5 4 9 8 10 4-1 8-5 8-10V6l-8-4Z"/><path d="m8 12 3 3 5-5"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5M17.5 17.5 19 19M5 19l1.5-1.5M17.5 6.5 19 5"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "copy": '<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h2"/>',
    "plus": '<path d="M12 4v16M4 12h16"/>',
    "sparkle": '<path d="m12 2 2.2 7.8L22 12l-7.8 2.2L12 22l-2.2-7.8L2 12l7.8-2.2L12 2Z"/>',
    "filter": '<path d="M3 4h18l-7 8v6l-4 3v-9L3 4Z"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10h.01"/>',
    "external": '<path d="M13 5h6v6M19 5l-9 9"/><path d="M19 13v6H5V5h6"/>',
    "logout": '<path d="M9 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h4M15 16l4-4-4-4M8 12h11"/>',
}
def icon(name, size=18):
    shape = ICONS.get(name, ICONS["file"])
    return (
        '<svg width="' + str(size) + '" height="' + str(size)
        + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true">' + shape + '</svg>'
    )


NAV = [
    ("dashboard", "/admin/templates", "grid", "Overview", "01"),
    ("library", "/admin/templates?view=library", "layers", "Template library", "02"),
    ("upload", "/admin/templates?view=upload", "upload", "Upload center", "03"),
    ("records", "/admin/templates?view=records", "database", "Content records", "04"),
    ("settings", "/admin/templates?view=settings", "settings", "Workspace settings", "05"),
]


def page(title, body, active="dashboard"):
    title_safe = html.escape(title or "Admin")
    if active == "login":
        content = (
            '<div class="login-wrap"><div class="login-aside">'
            '<div class="logomark logomark-lg">D<span>.</span></div>'
            '<div class="login-sup">DIGI PRO STUDIO</div>'
            '<h1>One workspace.<br><em>Every template.</em></h1>'
            '<p>Organize your designs, map editable text, manage content '
            'and prepare branded creative outputs in one secure workspace.</p>'
            '<div class="login-features"><span>' + icon("layers") + ' Creative library</span>'
            '<span>' + icon("database") + ' PostgreSQL content</span>'
            '<span>' + icon("shield") + ' Private access</span></div>'
            '<div class="login-bottom">DIGI PRO &nbsp; / &nbsp; INTERNAL WORKSPACE</div>'
            '</div><div class="login-form-wrap"><div class="login-form-top">'
            '<span class="online-dot"></span> SECURE ADMIN ACCESS</div>'
            + body + '<div class="login-footer">Protected workspace · Private session</div>'
            '</div></div>'
        )
    else:
        links = "".join(
            '<a class="nav-link' + (" active" if key == active else "")
            + '" href="' + href + '" aria-label="' + label + '">'
            '<span class="nav-icon">' + icon(glyph) + '</span>'
            '<span class="nav-label">' + label + '</span>'
            '<span class="nav-count">' + count + '</span></a>'
            for key, href, glyph, label, count in NAV
        )
        content = (
            '<div class="app-shell"><aside class="sidebar" id="appSidebar">'
            '<a href="/admin/templates" class="brand"><div class="logomark">D<span>.</span></div>'
            '<div class="brandtext"><strong>DIGI PRO</strong><small>CREATIVE STUDIO</small></div></a>'
            '<div class="side-separator"></div><div class="nav-label-small">WORKSPACE</div>'
            '<nav class="side-nav">' + links + '</nav>'
            '<div class="sidebar-bottom">'
            '<div class="sidebar-callout"><span class="callout-icon">' + icon("sparkle") + '</span>'
            '<strong>Creative engine</strong>'
            '<p>Editable SVG layouts and structured content, under your control.</p>'
            '<a href="/admin/templates?view=upload">Add a template ' + icon("arrow", 13) + '</a></div>'
            '<div class="side-user"><span class="avatar">DP</span>'
            '<div><strong>Workspace admin</strong><small>Owner access</small></div>'
            '<span class="user-verified">' + icon("shield", 16) + '</span></div>'
            '</div></aside>'
            '<div class="sidebar-overlay" data-sidebar-close></div>'
            '<div class="workspace"><header class="topbar">'
            '<div class="topbar-left"><button type="button" class="icon-btn mobile-menu" '
            'data-sidebar-toggle aria-label="Open navigation">' + icon("menu") + '</button>'
            '<div class="breadcrumbs"><span>Workspace</span>' + icon("chevron", 14)
            + '<strong>' + title_safe + '</strong></div></div>'
            '<div class="topbar-right"><span class="environment-tag"><i></i> Production</span>'
            '<button type="button" class="icon-btn" data-theme-toggle title="Toggle appearance" '
            'aria-label="Toggle appearance">' + icon("sun") + '</button>'
            '<a class="topbar-avatar" href="/admin/templates?view=settings" title="Settings">DP</a>'
            '</div></header><main class="page-content">' + body + '</main>'
            '<footer class="main-footer"><span>© DIGI PRO · CREATIVE STUDIO</span>'
            '<span>Private workspace · Railway / PostgreSQL</span></footer></div></div>'
        )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="theme-color" content="#10131f">'
        '<title>' + title_safe + ' · DIGI PRO STUDIO</title>'
        '<link rel="stylesheet" href="/admin/assets/styles.css">'
        '<link rel="stylesheet" href="/admin/assets/raster.css">'
        '<script defer src="/admin/assets/app.js"></script>'
        '</head><body>' + content + '</body></html>'
    ).encode("utf-8")


STYLE = r"""
:root{
 color-scheme:dark;--bg:#0c0f18;--surface:#111522;--surface2:#171c2c;
 --panel:#151a29;--panel-hi:#1b2234;--input:#101625;--border:#262e42;
 --text:#eef1ff;--sub:#a0a9bf;--muted:#77839d;--accent:#8377ff;--accent-hi:#998dff;
 --accent-low:#25234f;--green:#44d2ab;--yellow:#f0bd74;--red:#f08996;
 --shadow:0 22px 80px rgba(0,0,0,.23);--round:18px
}
:root[data-theme="light"]{
 color-scheme:light;--bg:#f4f5f9;--surface:#fff;--surface2:#f8f9fd;
 --panel:#fff;--panel-hi:#f4f5fc;--input:#fff;--border:#e5e8f0;
 --text:#15182c;--sub:#5d6680;--muted:#7c869e;--accent:#6059e7;--accent-hi:#4c46cd;
 --accent-low:#e9e7ff;--green:#13956a;--yellow:#b47525;--red:#d64456;
 --shadow:0 22px 70px rgba(30,42,92,.07)
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif;font-size:14px;line-height:1.5}
a{color:inherit;text-decoration:none}
button,input,select{font:inherit}
button{cursor:pointer}
strong{font-weight:680}
svg{flex-shrink:0}
h1,h2,h3,p{margin:0}
h1{font-size:clamp(25px,2.4vw,34px);letter-spacing:-.9px;line-height:1.2}
h2{font-size:19px;letter-spacing:-.4px}
h3{font-size:15px}
p{color:var(--sub)}
small,.muted{color:var(--muted)}
.app-shell{display:flex;min-height:100vh}
.sidebar{width:254px;flex:0 0 254px;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;padding:26px 15px 17px;position:sticky;top:0;height:100vh;z-index:20}
.brand{display:flex;align-items:center;gap:12px;padding:0 13px}
.logomark{height:42px;width:42px;border-radius:13px;background:linear-gradient(145deg,#9183ff,#5349d8);display:grid;place-items:center;color:#fff;font-weight:850;font-size:24px;box-shadow:0 7px 24px #6458eb45}
.logomark span{color:#d5ceff;margin-left:-4px}
.brandtext{display:flex;flex-direction:column;line-height:1.15;gap:6px}
.brandtext strong{font-size:15px;font-weight:850;letter-spacing:.9px}
.brandtext small{font-size:9px;letter-spacing:2.15px;font-weight:800;color:var(--muted)}
.side-separator{height:1px;background:var(--border);margin:25px 9px 25px}
.nav-label-small{font-size:10px;letter-spacing:1.7px;font-weight:800;color:var(--muted);padding:0 15px 14px}
.side-nav{display:flex;flex-direction:column;gap:5px}
.nav-link{display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:12px;color:var(--sub);transition:.18s}
.nav-link:hover{background:var(--panel-hi);color:var(--text)}
.nav-link.active{background:var(--accent-low);color:var(--accent-hi);font-weight:750}
.nav-link.active:before{content:"";position:absolute;left:15px;width:3px;height:22px;border-radius:8px;background:var(--accent)}
.nav-icon{display:grid;place-items:center}.nav-label{flex:1;font-size:13px}
.nav-count{color:var(--muted);font-size:10px;font-weight:700;opacity:.75}
.sidebar-bottom{margin-top:auto;display:grid;gap:22px}
.sidebar-callout{padding:18px;border-radius:16px;background:linear-gradient(145deg,#292748,#1b2039);border:1px solid #3d365e;display:grid;gap:9px}
.callout-icon{color:#b3adff}
.sidebar-callout strong{font-size:13px;color:#fff}
.sidebar-callout p{font-size:11.5px;color:#b4afce;line-height:1.5}
.sidebar-callout a{font-weight:750;font-size:11px;color:#c1baff;display:flex;align-items:center;gap:6px}
.side-user{border-top:1px solid var(--border);padding:18px 8px 0;display:flex;align-items:center;gap:10px}
.avatar,.topbar-avatar{display:grid;place-items:center;width:35px;height:35px;border-radius:10px;background:#393258;color:#d8d3ff;font-size:11px;font-weight:800}
.side-user div:nth-child(2){flex:1;display:grid;gap:2px}
.side-user strong{font-size:12px}
.side-user small{font-size:11px}
.user-verified{color:var(--green)}
.workspace{display:flex;flex-direction:column;flex:1;min-width:0}
.topbar{height:75px;border-bottom:1px solid var(--border);padding:0 clamp(22px,3vw,50px);display:flex;align-items:center;justify-content:space-between;gap:12px;background:var(--bg)}
.topbar-left,.topbar-right{display:flex;align-items:center;gap:16px}
.breadcrumbs{display:flex;align-items:center;gap:10px;color:var(--muted);font-size:12px}
.breadcrumbs strong{color:var(--text);font-weight:730}
.topbar-right{gap:12px}
.environment-tag{border:1px solid var(--border);background:var(--surface);padding:8px 11px;border-radius:30px;font-size:11px;color:var(--sub);display:flex;align-items:center;gap:7px;font-weight:650}
.environment-tag i,.online-dot{height:7px;width:7px;display:inline-block;border-radius:100%;background:var(--green);box-shadow:0 0 0 3px rgba(68,210,171,.12)}
.icon-btn{width:36px;height:36px;display:grid;place-items:center;color:var(--sub);border:1px solid var(--border);background:var(--surface);border-radius:10px}
.icon-btn:hover{color:var(--text);border-color:var(--accent)}
.topbar-avatar{border-radius:50%;width:34px;height:34px}
.mobile-menu{display:none}
.page-content{width:100%;max-width:1620px;margin:0 auto;padding:35px clamp(20px,3vw,50px) 56px;flex:1}
.main-footer{padding:18px clamp(20px,3vw,50px);border-top:1px solid var(--border);display:flex;gap:12px;justify-content:space-between;font-size:10px;letter-spacing:1px;color:var(--muted)}
.heading-row{display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;margin-bottom:27px}
.eyebrow{font-size:10px;letter-spacing:2px;font-weight:850;color:var(--accent-hi);text-transform:uppercase;margin-bottom:9px}
.heading-row h1 em{font-style:normal;background:linear-gradient(90deg,#c0aaff,#7a9bff);background-clip:text;-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.heading-row p{margin-top:9px;max-width:700px;line-height:1.6}
.heading-actions{display:flex;gap:10px;flex-wrap:wrap}
.btn,button:not(.icon-btn):not(.ghost):not(.danger):not(.toolbar-button){display:inline-flex;align-items:center;justify-content:center;gap:8px;border:1px solid transparent;border-radius:10px;padding:11px 16px;background:var(--accent);color:#fff;font-size:12px;font-weight:800;min-height:41px;transition:.18s;white-space:nowrap}
.btn:hover,button:not(.icon-btn):hover{filter:brightness(1.08)}
.btn-secondary,.btn.btn-secondary{background:var(--surface2);color:var(--text);border-color:var(--border)}
.btn-ghost,.btn.btn-ghost{background:transparent;color:var(--sub);border-color:var(--border)}
.btn-danger,button.danger{background:#572c38;color:#ffadb7;border-color:#854453}
button.ghost{background:transparent;color:var(--sub);border:1px solid var(--border);border-radius:10px;padding:10px 15px;font-size:12px;font-weight:720}
.badge{display:inline-flex;align-items:center;gap:6px;border-radius:100px;font-size:10px;font-weight:800;padding:5px 9px;background:var(--surface2);border:1px solid var(--border);color:var(--sub);white-space:nowrap}
.badge.purple{background:var(--accent-low);border-color:transparent;color:var(--accent-hi)}
.badge.green{background:rgba(68,210,171,.11);border-color:rgba(68,210,171,.20);color:var(--green)}
.badge.warning{color:var(--yellow);background:rgba(240,189,116,.10);border-color:transparent}
.stats-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin-bottom:23px}
.stat-card{position:relative;background:var(--surface);border:1px solid var(--border);border-radius:var(--round);padding:21px;display:grid;gap:12px;min-height:139px;overflow:hidden}
.stat-card::after{content:"";position:absolute;top:-40px;right:-50px;width:110px;height:110px;background:radial-gradient(circle,rgba(131,119,255,.10),transparent 70%)}
.stat-top{display:flex;justify-content:space-between;align-items:center;color:var(--muted);font-size:12px;font-weight:650}
.stat-icon{display:grid;place-items:center;width:33px;height:33px;border-radius:10px;background:var(--accent-low);color:var(--accent-hi)}
.stat-value{font-size:31px;line-height:1;letter-spacing:-1px;font-weight:850;color:var(--text)}
.stat-footer{font-size:10px;color:var(--muted)}
.panel,.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--round);padding:23px}
.card{margin-bottom:18px}
.panel-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:19px;flex-wrap:wrap}
.panel-head p{font-size:12px;margin-top:4px}
.panel-head a{color:var(--accent-hi);font-weight:700;font-size:12px}
.two-columns{display:grid;grid-template-columns:minmax(0,1.42fr) minmax(315px,.92fr);gap:18px;margin-bottom:23px}
.quick-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.quick-item{border:1px solid var(--border);border-radius:13px;padding:15px;background:var(--surface2);display:grid;gap:12px;transition:.15s}
.quick-item:hover{border-color:var(--accent);transform:translateY(-1px)}
.quick-item span:first-child{color:var(--accent-hi)}
.quick-item strong{display:block;font-size:12px}
.quick-item small{font-size:11px;margin-top:4px;display:block}
.mini-steps{display:grid;gap:16px}
.mini-step{display:flex;align-items:flex-start;gap:12px}
.step-num{height:26px;width:26px;border:1px solid var(--border);background:var(--surface2);border-radius:9px;display:grid;place-items:center;color:var(--accent-hi);font-weight:800;font-size:11px;flex-shrink:0}
.mini-step strong{font-size:12px}
.mini-step p{font-size:11px;margin-top:3px;line-height:1.5}
.section-header{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:25px 0 15px;flex-wrap:wrap}
.section-header p{font-size:12px;margin-top:4px}
.control-row{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-bottom:20px}
.control-row input,.control-row select{margin:0!important}
.searchbox{display:flex;align-items:center;gap:9px;border:1px solid var(--border);background:var(--surface);border-radius:10px;padding:0 13px;min-width:235px;flex:1;max-width:440px;color:var(--muted)}
.searchbox:focus-within{border-color:var(--accent)}
.searchbox input{border:none!important;background:transparent!important;padding:11px 0!important;min-height:39px;outline:0;box-shadow:none!important}
.select-small{max-width:170px;min-height:42px;padding:9px 12px!important}
.template-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.template-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--round);overflow:hidden;transition:.18s;min-width:0}
.template-card:hover{border-color:#6961bd;box-shadow:0 12px 34px rgba(0,0,0,.13);transform:translateY(-2px)}
.template-art{height:173px;background:#1e2334;position:relative;display:flex;align-items:center;justify-content:center;overflow:hidden}
.template-art img{height:100%;width:100%;object-fit:contain}
.template-art .format-icon{height:62px;width:62px;border-radius:18px;display:grid;place-items:center;color:#b1abff;background:#49426b}
.template-art .format-icon svg{height:32px;width:32px}
.template-art .format-label{position:absolute;top:13px;left:13px;padding:5px 9px;background:rgba(20,24,42,.83);border:1px solid rgba(255,255,255,.1);color:#fff;border-radius:8px;font-size:10px;font-weight:800;letter-spacing:.9px}
.template-content{padding:18px}
.template-name{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block}
.template-meta{display:flex;align-items:center;gap:10px;color:var(--muted);font-size:10.5px;margin:10px 0 14px}
.template-meta .dot{width:3px;height:3px;background:var(--muted);border-radius:50%}
.template-actions{display:flex;gap:8px;border-top:1px solid var(--border);padding-top:14px}
.template-actions .btn{padding:8px 11px;font-size:11px;min-height:34px}
.template-actions form{margin-left:auto}
.template-actions button{min-height:34px!important;padding:8px 10px!important}
.template-grid.list-view{grid-template-columns:1fr}
.template-grid.list-view .template-card{display:flex;align-items:stretch}
.template-grid.list-view .template-art{width:180px;height:auto;flex-shrink:0}
.template-grid.list-view .template-content{flex:1}
.empty-state{background:var(--surface);border:1px dashed var(--border);border-radius:16px;padding:45px 20px;text-align:center;color:var(--muted);grid-column:1/-1}
.empty-state svg{color:var(--accent);margin-bottom:15px}
.empty-state strong{display:block;color:var(--text);font-size:15px;margin-bottom:6px}
.dropzone{padding:28px 20px;border:1.5px dashed #514c85;border-radius:16px;background:linear-gradient(145deg,rgba(107,91,207,.11),transparent 70%);text-align:center;display:grid;justify-items:center;gap:11px;cursor:pointer;transition:.18s}
.dropzone.is-dragging,.dropzone:hover{border-color:var(--accent);background:var(--accent-low)}
.dropzone .drop-icon{width:54px;height:54px;background:#343055;color:#c1b9ff;border-radius:16px;display:grid;place-items:center}
.dropzone strong{color:var(--text);font-size:14px}
.dropzone p{font-size:12px}
.dropzone input[type=file]{position:absolute;opacity:0;width:1px;height:1px;pointer-events:none}
.dropzone .file-name{font-size:12px;color:var(--accent-hi);font-weight:700;word-break:break-all}
.form-row{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.field{margin-bottom:15px}
label{display:block;font-size:11px;font-weight:750;color:var(--sub);margin-bottom:8px}
input[type=text],input[type=password],input[type=email],input[type=file],input[type=number],select,textarea{display:block;width:100%;padding:12px 13px;border:1px solid var(--border);border-radius:10px;background:var(--input);color:var(--text);outline:0;transition:.15s;font-size:12px}
input:focus,select:focus,textarea:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(131,119,255,.08)}
input::placeholder{color:var(--muted)}
select{cursor:pointer}
input[type=checkbox]{accent-color:var(--accent)}
.checkline{display:flex;gap:8px;align-items:center;color:var(--sub);font-size:12px}
.checkline input{width:auto}
.form-actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:18px}
.note{padding:12px 15px;border:1px solid rgba(131,119,255,.22);background:var(--accent-low);color:var(--sub);border-radius:12px;font-size:12px;margin-bottom:16px}
.note.error{border-color:rgba(240,137,150,.4);background:rgba(240,137,150,.11);color:var(--red)}
.note.success{border-color:rgba(68,210,171,.35);background:rgba(68,210,171,.08);color:var(--green)}
.row{display:flex;justify-content:space-between;gap:16px;align-items:center;padding:15px 0;border-bottom:1px solid var(--border)}
.row:last-child{border-bottom:0}
.row p{margin-top:6px;font-size:12px}
.actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.actions .btn{font-size:11px;min-height:35px;padding:8px 12px}
.inline{display:inline}
.preview{display:block;width:100%;max-height:520px;min-height:160px;object-fit:contain;margin:auto;background:#fff;border-radius:12px;padding:16px;border:1px solid #eff0f5}
.editor-grid{display:grid;grid-template-columns:minmax(300px,1.05fr) minmax(380px,1fr);gap:19px;align-items:start}
.preview-panel{position:sticky;top:98px}
.preview-stage{display:flex;align-items:center;justify-content:center;background:repeating-conic-gradient(#e6e8ef 0% 25%,#fff 0% 50%) 50%/24px 24px;border-radius:13px;padding:20px;min-height:270px}
.preview-stage img{max-height:500px;max-width:100%;object-fit:contain}
.layer-row{padding:15px;border-radius:12px;border:1px solid var(--border);margin:10px 0;display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:center}
.layer-row:hover{border-color:#655a9b;background:var(--surface2)}
.layer-row .layer-text{color:var(--sub);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.layer-row .layer-number{font-size:10px;color:var(--muted);margin-bottom:4px;display:block}
.layer-row select{margin:0}
.toolbar{display:flex;gap:9px;align-items:center;flex-wrap:wrap}
.toolbar-button{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--border);background:var(--surface);border-radius:9px;color:var(--sub);padding:9px 11px;font-size:11px;font-weight:700}
.toolbar-button:hover{border-color:var(--accent);color:var(--accent-hi)}
.data-table{width:100%;border-collapse:collapse}
.data-table th{text-align:left;font-size:10px;font-weight:850;letter-spacing:1px;color:var(--muted);text-transform:uppercase;padding:14px 12px;border-bottom:1px solid var(--border)}
.data-table td{padding:14px 12px;border-bottom:1px solid var(--border);font-size:12px;color:var(--sub)}
.data-table tr:hover td{background:var(--surface2)}
.data-table .name-cell{font-weight:700;color:var(--text)}
.data-table tbody tr:last-child td{border:0}
.table-scroll{overflow-x:auto}
.settings-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:17px}
.setting{padding:16px 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;gap:12px}
.setting:last-child{border-bottom:0}
.setting strong{font-size:12px}
.setting small{font-size:12px;display:block;margin-top:4px}
.setting code{font-size:11px;color:var(--accent-hi);word-break:break-all}
.main-footer{margin-top:auto}
.login-wrap{min-height:100vh;display:grid;grid-template-columns:minmax(360px,1fr) minmax(400px,1fr)}
.login-aside{background:radial-gradient(ellipse at 60% 25%,#3d3274,#171c37 60%,#10131f);padding:clamp(35px,7vw,95px);display:flex;flex-direction:column;align-items:flex-start;justify-content:center;position:relative;overflow:hidden}
.login-aside:after{content:"";position:absolute;right:-160px;top:-160px;height:500px;width:500px;border:1px solid rgba(255,255,255,.07);border-radius:50%;box-shadow:0 0 0 55px rgba(255,255,255,.015),0 0 0 110px rgba(255,255,255,.013);pointer-events:none}
.logomark-lg{width:60px;height:60px;font-size:32px;margin-bottom:35px}
.login-sup{color:#b5aaff;font-weight:800;letter-spacing:3px;font-size:10px;margin-bottom:17px}
.login-aside h1{font-size:clamp(42px,5vw,68px);font-weight:820;letter-spacing:-2.5px;max-width:540px;line-height:1.08;color:#fff}
.login-aside h1 em{font-style:normal;color:#b6aaff}
.login-aside>p{max-width:490px;margin-top:24px;color:#b8bdd7;font-size:15px;line-height:1.8}
.login-features{display:flex;flex-wrap:wrap;gap:12px;margin-top:38px}
.login-features span{display:flex;align-items:center;gap:8px;padding:10px 12px;border:1px solid #696185;border-radius:10px;color:#eee9ff;font-size:11px}
.login-bottom{position:absolute;bottom:45px;color:#8a85ad;letter-spacing:2px;font-size:10px}
.login-form-wrap{max-width:540px;width:100%;margin:auto;padding:40px clamp(30px,5vw,65px)}
.login-form-top{font-size:10px;letter-spacing:1.7px;font-weight:800;color:var(--sub);display:flex;align-items:center;gap:9px;margin-bottom:55px}
.login-form-wrap h1{font-size:32px;letter-spacing:-1px}
.login-form-wrap> .card,.login-form-wrap>section.card{border:0;background:transparent;padding:0;margin-top:28px}
.login-form-wrap input{padding:15px 15px;font-size:13px}
.login-form-wrap button{width:100%;padding:14px!important;font-size:13px!important;margin-top:8px}
.login-footer{font-size:11px;color:var(--muted);margin-top:55px}
.sidebar-overlay{display:none}
[data-hide]{display:none!important}
@media(max-width:1320px){.stats-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.template-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.two-columns{grid-template-columns:1fr}.editor-grid{grid-template-columns:1fr}.preview-panel{position:static}}
@media(max-width:900px){.sidebar{position:fixed;transform:translateX(-102%);transition:.2s}.sidebar-open .sidebar{transform:translateX(0)}.sidebar-open .sidebar-overlay{display:block;position:fixed;inset:0;background:#060a17ad;z-index:18}.mobile-menu{display:grid}.topbar{padding:0 22px}.page-content{padding:27px 22px 50px}.login-wrap{grid-template-columns:1fr}.login-aside{min-height:340px;padding:40px}.login-aside h1{font-size:40px}.login-aside>p{font-size:13px}.login-bottom{display:none}.login-form-wrap{max-width:530px}}
@media(max-width:620px){.stats-grid,.template-grid,.quick-grid,.settings-grid,.form-row{grid-template-columns:1fr}.panel,.card{padding:18px}.heading-row{align-items:flex-start}.heading-actions{width:100%}.heading-actions .btn{flex:1}.template-grid.list-view .template-art{width:120px}.layer-row{grid-template-columns:1fr}.main-footer{flex-direction:column}.environment-tag{display:none}.breadcrumbs span{display:none}.login-aside{min-height:275px}.login-aside h1{font-size:33px}.login-features{gap:7px}.login-features span{font-size:10px}}
"""

SCRIPT = r"""
(function(){
'use strict';
var html = document.documentElement;
try{var theme=localStorage.getItem('digipro-theme');if(theme==='light'||theme==='dark'){html.dataset.theme=theme;}}catch(e){}
function all(sel){return Array.prototype.slice.call(document.querySelectorAll(sel));}
all('[data-theme-toggle]').forEach(function(b){b.addEventListener('click',function(){var next=html.dataset.theme==='light'?'dark':'light';html.dataset.theme=next;try{localStorage.setItem('digipro-theme',next);}catch(e){}});});
all('[data-sidebar-toggle]').forEach(function(b){b.addEventListener('click',function(){document.body.classList.add('sidebar-open');});});
all('[data-sidebar-close]').forEach(function(b){b.addEventListener('click',function(){document.body.classList.remove('sidebar-open');});});
all('form[data-confirm]').forEach(function(form){form.addEventListener('submit',function(e){if(!confirm(form.dataset.confirm||'Confirm this action?'))e.preventDefault();});});
var list=document.querySelector('[data-template-grid]');
if(list){
 var search=document.querySelector('[data-search]'),filter=document.querySelector('[data-filter]'),sort=document.querySelector('[data-sort]');
 var cards=all('[data-template-card]'),empty=document.querySelector('[data-search-empty]');
 function refresh(){
   var term=(search&&search.value||'').toLowerCase().trim();
   var kind=filter&&filter.value||'all';
   var visible=0;
   cards.forEach(function(c){
     var match=(!term||(c.dataset.name||'').toLowerCase().indexOf(term)>-1)&&
       (kind==='all'||c.dataset.type===kind);
     c.hidden=!match;c.style.display=match?'':'none';if(match)visible++;
   });
   if(empty)empty.style.display=visible?'none':'block';
   if(sort){
     var ordered=cards.slice().sort(function(a,b){
       if(sort.value==='name')return (a.dataset.name||'').localeCompare(b.dataset.name||'');
       if(sort.value==='size')return Number(b.dataset.size||0)-Number(a.dataset.size||0);
       return Number(b.dataset.modified||0)-Number(a.dataset.modified||0);
     });
     ordered.forEach(function(c){list.appendChild(c);});
   }
 }
 [search,filter,sort].forEach(function(el){if(el)el.addEventListener(el===search?'input':'change',refresh);});
 refresh();
 all('[data-view-toggle]').forEach(function(el){el.addEventListener('click',function(){
   list.classList.toggle('list-view');el.setAttribute('aria-pressed',list.classList.contains('list-view')?'true':'false');
 });});
}
all('[data-dropzone]').forEach(function(zone){
 var input=zone.querySelector('input[type=file]');
 if(!input)return;
 var feedback=zone.querySelector('[data-filename]');
 zone.addEventListener('click',function(e){if(e.target!==input)input.click();});
 zone.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();input.click();}});
 ['dragenter','dragover'].forEach(function(ev){zone.addEventListener(ev,function(e){e.preventDefault();zone.classList.add('is-dragging');});});
 ['dragleave','drop'].forEach(function(ev){zone.addEventListener(ev,function(e){e.preventDefault();zone.classList.remove('is-dragging');});});
 zone.addEventListener('drop',function(e){if(e.dataTransfer&&e.dataTransfer.files.length){input.files=e.dataTransfer.files;changed();}});
 input.addEventListener('change',changed);
 function changed(){if(input.files.length&&feedback){var f=input.files[0];feedback.textContent=f.name+' · '+(f.size/1024/1024).toFixed(2)+' MB';}}
});
all('[data-mapping-clear]').forEach(function(el){el.addEventListener('click',function(){all('select[name^=layer_]').forEach(function(s){s.value='';});});});
all('[data-mapping-suggest]').forEach(function(el){el.addEventListener('click',function(){all('select[name^=layer_]').forEach(function(s){s.value=s.dataset.suggestion||'';});});});
var layerSearch=document.querySelector('[data-layer-search]');
if(layerSearch){layerSearch.addEventListener('input',function(){var term=layerSearch.value.toLowerCase();all('[data-layer-row]').forEach(function(el){el.style.display=(el.dataset.text||'').toLowerCase().indexOf(term)>-1?'':'none';});});}
})();
"""
