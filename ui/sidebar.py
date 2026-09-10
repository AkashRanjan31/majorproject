"""
ui/sidebar.py
-------------
Collapsible enterprise sidebar for NeuroSense AI.

Architecture (why the previous version broke)
----------------------------------------------
st.markdown(unsafe_allow_html=True) passes content through Streamlit's
markdown renderer which:
  1. Sanitises unknown HTML tags — <div>, <script> etc. are either
     stripped or escaped to plain text, which is why the raw tag strings
     were appearing on screen.
  2. Renders into the normal content column, so a position:fixed div
     still sits inside the Streamlit stacking context and cannot escape
     the main content area.

The correct approach uses two separate mechanisms:

  A. st.components.v1.html()
     Renders an <iframe srcdoc="..."> that is completely outside
     Streamlit's sanitiser.  The iframe is given height=0 / visibility
     hidden so it takes no visual space.  Its JavaScript reaches into
     the PARENT document (window.parent.document) to inject the sidebar
     <div> directly into <body> — bypassing every Streamlit restriction.

  B. st.markdown("<style>...</style>", unsafe_allow_html=True)
     <style> tags ARE allowed by Streamlit's sanitiser, so all CSS
     (sidebar shell, transitions, main-content offset) is injected this
     way and applies to the parent document normally.

Navigation bridge
-----------------
JS writes the chosen page into window.parent.location hash
(window.parent.location.hash = "#page=Dashboard").  Python reads it
back with st.query_params on the next rerun.  This is 100% reliable
because query_params survive reruns and require no hidden widgets.

Collapse bridge
---------------
Collapse state lives in st.session_state["sidebar_collapsed"].
The toggle button inside the iframe calls
window.parent.postMessage({type:"ns_toggle"}, "*").
A message listener in the PARENT document (also injected by the iframe)
flips a CSS class on <body> immediately (for instant visual feedback)
and then updates window.parent.location.hash to include the new state,
which Python picks up on the next rerun.
"""

from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components

# ── SVG icon paths (Lucide 0.263 — stroke-based, viewBox 0 0 24 24) ──────────
_ICONS: dict[str, str] = {
    "layout-dashboard": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    "activity":         '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "bar-chart-3":      '<rect x="3" y="12" width="4" height="9" rx="1"/><rect x="10" y="7" width="4" height="14" rx="1"/><rect x="17" y="3" width="4" height="18" rx="1"/>',
    "trending-up":      '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    "history":          '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>',
    "file-bar-chart":   '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="18" x2="8" y2="12"/><line x1="12" y1="18" x2="12" y2="15"/><line x1="16" y1="18" x2="16" y2="13"/>',
    "brain-circuit":    '<path d="M12 4.5a2.5 2.5 0 0 0-4.96-.46 2.5 2.5 0 0 0-1.98 3 2.5 2.5 0 0 0-1.32 4.24C3.99 12.53 4.5 13.5 5 14"/><path d="M8 14v4a2 2 0 0 0 2 2h4"/><path d="M12 4.5a2.5 2.5 0 0 1 4.96-.46 2.5 2.5 0 0 1 1.98 3 2.5 2.5 0 0 1 1.32 4.24C20.01 12.53 19.5 13.5 19 14"/><path d="M16 14v4a2 2 0 0 1-2 2"/><line x1="12" y1="14" x2="12" y2="22"/><circle cx="12" cy="14" r="2"/>',
    "settings":         '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    "shield-check":     '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/>',
    "info":             '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
    "chevron-left":     '<polyline points="15 18 9 12 15 6"/>',
    "chevron-right":    '<polyline points="9 18 15 12 9 6"/>',
}

def _svg(icon_key: str, size: int = 20) -> str:
    """Return an inline SVG element for the given Lucide icon key."""
    paths = _ICONS.get(icon_key, '<circle cx="12" cy="12" r="10"/>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" '
        f'style="flex-shrink:0;display:block">'
        f'{paths}</svg>'
    )

# ── page registry ─────────────────────────────────────────────────────────────
# (label, icon-key, section, shortcode)
_PAGES: list[tuple[str, str, str, str]] = [
    ("Dashboard",      "layout-dashboard", "MAIN",   "M"),
    ("Live Monitor",   "activity",         "MAIN",   "M"),
    ("Analytics",      "bar-chart-3",      "MAIN",   "M"),
    ("Fatigue Trends", "trending-up",      "MAIN",   "M"),
    ("History",        "history",          "DATA",   "D"),
    ("Reports",        "file-bar-chart",   "DATA",   "D"),
    ("Model",          "brain-circuit",    "AI",     "A"),
    ("Settings",       "settings",         "SYSTEM", "S"),
    ("Privacy",        "shield-check",     "SYSTEM", "S"),
    ("About",          "info",             "SYSTEM", "S"),
]

_KNOWN_PAGES = {p[0] for p in _PAGES}


# ── CSS injected into the parent Streamlit document ───────────────────────────
# st.markdown allows <style> tags — this is the correct way to style
# elements that live in the parent document (the sidebar div we inject).

_SIDEBAR_CSS = """
<style>
/* ── sidebar variables ── */
:root {
  --ns-w:     270px;
  --ns-wc:    72px;
  --ns-dur:   280ms;
  --ns-ease:  cubic-bezier(.4,0,.2,1);
  --ns-bg:    linear-gradient(180deg,#080f1c 0%,#07111F 100%);
  --ns-bd:    rgba(255,255,255,0.06);
}

/* ── hide native Streamlit sidebar chrome ── */
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
  display: none !important;
  width: 0 !important;
  min-width: 0 !important;
}

/* ── remove overflow/transform that creates stacking contexts ── */
/* Streamlit's app container must NOT clip fixed children */
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
.appview-container {
  overflow: visible !important;
  transform: none !important;
}

/* ── sidebar shell ── */
#ns-sidebar {
  position: fixed;
  top: 0; left: 0; bottom: 0;
  width: var(--ns-w);
  background: var(--ns-bg);
  border-right: 1px solid var(--ns-bd);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width var(--ns-dur) var(--ns-ease);
  box-shadow: 4px 0 32px rgba(0,0,0,.55);
  font-family: 'Inter', -apple-system, sans-serif;
  /* Ensure sidebar is never clipped by parent overflow */
  clip-path: none !important;
}
#ns-sidebar.ns-collapsed {
  width: var(--ns-wc);
}

/* ── scrollable nav area ── */
#ns-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: .4rem .45rem;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,.07) transparent;
}
#ns-nav::-webkit-scrollbar { width: 3px; }
#ns-nav::-webkit-scrollbar-thumb { background: rgba(255,255,255,.08); border-radius: 3px; }

/* ── logo row ── */
.ns-logo {
  display: flex;
  align-items: center;
  gap: .65rem;
  padding: .9rem .65rem 1rem;
  border-bottom: 1px solid var(--ns-bd);
  margin-bottom: .35rem;
  overflow: hidden;
  white-space: nowrap;
  flex-shrink: 0;
}
.ns-logo-icon {
  width: 36px; height: 36px;
  border-radius: 10px;
  flex-shrink: 0;
  background: linear-gradient(135deg,#1d4ed8,#6d28d9);
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  box-shadow: 0 2px 8px rgba(29,78,216,.35);
}
.ns-brand {
  overflow: hidden;
  white-space: nowrap;
  transition: opacity var(--ns-dur) var(--ns-ease),
              max-width var(--ns-dur) var(--ns-ease);
  max-width: 200px;
  opacity: 1;
}
#ns-sidebar.ns-collapsed .ns-brand {
  opacity: 0;
  max-width: 0;
  pointer-events: none;
}
.ns-brand-name { font-size: .9rem; font-weight: 800; color: #F8FAFC; line-height: 1.2; }
.ns-brand-sub  { font-size: .56rem; color: #94A3B8; letter-spacing: .05em; }

/* ── section labels ── */
.ns-section {
  font-size: .5rem;
  font-weight: 700;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: #64748B;
  padding: .55rem .55rem .15rem;
  white-space: nowrap;
  overflow: hidden;
  transition: opacity var(--ns-dur) var(--ns-ease),
              max-height var(--ns-dur) var(--ns-ease),
              padding var(--ns-dur) var(--ns-ease);
  max-height: 40px;
  opacity: 1;
}
#ns-sidebar.ns-collapsed .ns-section {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
  pointer-events: none;
}

/* ── nav items ── */
.ns-item {
  display: flex;
  align-items: center;
  gap: .6rem;
  padding: .48rem .6rem;
  border-radius: 11px;
  font-size: .81rem;
  font-weight: 500;
  color: #94A3B8;
  cursor: pointer;
  border: 1px solid transparent;
  margin-bottom: .06rem;
  white-space: nowrap;
  overflow: hidden;
  transition: background .15s, color .15s, border-color .15s,
              padding var(--ns-dur) var(--ns-ease),
              justify-content var(--ns-dur) var(--ns-ease);
  position: relative;
  user-select: none;
}
.ns-item:hover {
  background: rgba(37,99,235,.1);
  color: #93c5fd;
  border-color: rgba(37,99,235,.18);
}
.ns-item.ns-active {
  background: linear-gradient(135deg,rgba(37,99,235,.22),rgba(139,92,246,.12));
  color: #93c5fd;
  border-color: rgba(37,99,235,.32);
  border-left: 3px solid #2563EB;
  font-weight: 700;
}
#ns-sidebar.ns-collapsed .ns-item {
  padding: .48rem 0;
  justify-content: center;
  border-left-color: transparent !important;
}
#ns-sidebar.ns-collapsed .ns-item.ns-active {
  background: rgba(37,99,235,.18);
  border-color: rgba(37,99,235,.28);
}

/* ── icon ── */
.ns-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #64748B;
  transition: color var(--ns-dur) var(--ns-ease);
}
.ns-icon svg {
  width: 20px;
  height: 20px;
  display: block;
}
.ns-item:hover .ns-icon  { color: #60a5fa; }
.ns-item.ns-active .ns-icon { color: #3b82f6; }

/* ── label ── */
.ns-label {
  overflow: hidden;
  max-width: 160px;
  opacity: 1;
  transition: opacity var(--ns-dur) var(--ns-ease),
              max-width var(--ns-dur) var(--ns-ease);
}
#ns-sidebar.ns-collapsed .ns-label {
  opacity: 0;
  max-width: 0;
  pointer-events: none;
}

/* ── tooltip (collapsed only) ── */
.ns-tip {
  position: fixed;
  left: calc(var(--ns-wc) + 10px);
  background: #162032;
  color: #F8FAFC;
  font-size: .72rem;
  font-weight: 600;
  padding: .28rem .7rem;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,.12);
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  transition: opacity .15s;
  z-index: 10001;
  box-shadow: 0 4px 16px rgba(0,0,0,.5);
}
#ns-sidebar.ns-collapsed .ns-item:hover .ns-tip {
  opacity: 1;
}

/* ── toggle button ── */
#ns-toggle {
  position: fixed;
  top: 20px;
  left: calc(var(--ns-w) - 12px);
  width: 24px; height: 24px;
  border-radius: 50%;
  background: #0d1b2e;
  border: 1px solid rgba(255,255,255,.12);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  z-index: 10002;
  color: #94A3B8;
  transition: left var(--ns-dur) var(--ns-ease),
              background .15s, color .15s, border-color .15s;
  user-select: none;
}
#ns-toggle:hover {
  background: #1e293b;
  color: #f1f5f9;
  border-color: rgba(255,255,255,.22);
}
#ns-toggle svg { display: block; }
body.ns-collapsed #ns-toggle {
  left: calc(var(--ns-wc) - 12px);
}

/* ── footer ── */
.ns-footer {
  font-size: .6rem;
  color: #475569;
  padding: .75rem .75rem;
  border-top: 1px solid var(--ns-bd);
  white-space: nowrap;
  overflow: hidden;
  flex-shrink: 0;
  transition: opacity var(--ns-dur) var(--ns-ease);
  opacity: 1;
}
.ns-footer-row { line-height: 1.85; }
#ns-sidebar.ns-collapsed .ns-footer {
  opacity: 0;
  pointer-events: none;
}

/* ── main content offset ── */
/* Target every wrapper Streamlit uses so nothing sits behind the sidebar */
[data-testid="stAppViewContainer"],
.appview-container {
  padding-left: var(--ns-w) !important;
  transition: padding-left var(--ns-dur) var(--ns-ease) !important;
  box-sizing: border-box !important;
  min-width: 0 !important;
  width: 100% !important;
}
body.ns-collapsed [data-testid="stAppViewContainer"],
body.ns-collapsed .appview-container {
  padding-left: var(--ns-wc) !important;
}

/* Keep stMain itself at full width inside the padded container */
[data-testid="stMain"],
section.main {
  margin-left: 0 !important;
  width: 100% !important;
  min-width: 0 !important;
  transition: none !important;
}

.block-container {
  max-width: 100% !important;
  width: 100% !important;
  min-width: 0 !important;
}

/* ── tablet ── */
@media (max-width: 1024px) and (min-width: 769px) {
  :root { --ns-w: 220px; }
  [data-testid="stAppViewContainer"],
  .appview-container {
    padding-left: var(--ns-w) !important;
  }
  body.ns-collapsed [data-testid="stAppViewContainer"],
  body.ns-collapsed .appview-container {
    padding-left: var(--ns-wc) !important;
  }
}

/* ── mobile ── */
@media (max-width: 768px) {
  #ns-sidebar {
    transform: translateX(calc(-1 * var(--ns-w)));
    transition: transform var(--ns-dur) var(--ns-ease),
                width var(--ns-dur) var(--ns-ease);
    width: var(--ns-w) !important;
  }
  #ns-sidebar.ns-mobile-open {
    transform: translateX(0);
  }
  /* No padding offset on mobile — sidebar overlays content */
  [data-testid="stAppViewContainer"],
  .appview-container {
    padding-left: 0 !important;
  }
  body.ns-collapsed [data-testid="stAppViewContainer"],
  body.ns-collapsed .appview-container {
    padding-left: 0 !important;
  }
  #ns-toggle {
    left: 12px !important;
    top: 12px;
  }
  #ns-sidebar.ns-mobile-open ~ #ns-toggle {
    left: calc(var(--ns-w) - 13px) !important;
  }
  #ns-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.6);
    z-index: 9998;
    backdrop-filter: blur(2px);
  }
  body.ns-mobile-open #ns-overlay {
    display: block;
  }
}
</style>
"""


def _build_sidebar_html(current_page: str, collapsed: bool) -> str:
    """Build the complete sidebar inner HTML string."""
    collapsed_cls = "ns-collapsed" if collapsed else ""

    nav_parts: list[str] = []
    last_section = ""
    for label, icon_key, section, _ in _PAGES:
        if section != last_section:
            nav_parts.append(f'<div class="ns-section">{section}</div>')
            last_section = section
        active_cls = " ns-active" if label == current_page else ""
        safe_label = label.replace("'", "\\'")
        icon_svg = _svg(icon_key, 20)
        nav_parts.append(
            f'<div class="ns-item{active_cls}" onclick="nsNav(\'{safe_label}\')" title="{label}">'
            f'<span class="ns-icon">{icon_svg}</span>'
            f'<span class="ns-label">{label}</span>'
            f'<span class="ns-tip">{label}</span>'
            f'</div>'
        )

    nav_html = "\n".join(nav_parts)

    logo_svg = _svg("brain-circuit", 18)

    toggle_icon = _svg("chevron-left", 14) if not collapsed else _svg("chevron-right", 14)

    return f"""
<div id="ns-sidebar" class="{collapsed_cls}">
  <div class="ns-logo">
    <div class="ns-logo-icon">{logo_svg}</div>
    <div class="ns-brand">
      <div class="ns-brand-name">NeuroSense AI</div>
      <div class="ns-brand-sub">Mental Fatigue Detection</div>
    </div>
  </div>
  <div id="ns-nav">{nav_html}</div>
  <div class="ns-footer">
    <div class="ns-footer-row">NeuroSense AI v2.0</div>
    <div class="ns-footer-row">Powered by XGBoost</div>
    <div class="ns-footer-row">Local AI · SQLite</div>
    <div style="margin-top:.6rem">
      <button onclick="nsLaunchWidget()" style="
        width:100%;padding:.42rem .6rem;border-radius:9px;
        background:linear-gradient(135deg,#1d4ed8,#6d28d9);
        color:#fff;font-size:.72rem;font-weight:700;
        border:none;cursor:pointer;letter-spacing:.03em;
        transition:opacity .15s;
      " onmouseover="this.style.opacity='.8'" onmouseout="this.style.opacity='1'">
        🧠 Floating Widget
      </button>
    </div>
  </div>
</div>
<div id="ns-toggle" onclick="nsToggle()" title="Toggle sidebar">{toggle_icon}</div>
<div id="ns-overlay" onclick="nsMobileClose()"></div>
"""


def _build_injector_js(current_page: str, collapsed: bool) -> str:
    """
    Build the JavaScript that runs inside the hidden iframe.
    It injects the sidebar HTML + CSS into window.parent.document,
    then sets up all event handlers on the parent document.
    """
    sidebar_html = _build_sidebar_html(current_page, collapsed)
    sidebar_html_escaped = (
        sidebar_html
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )
    collapsed_js = "true" if collapsed else "false"

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<script>
(function() {{
  var P = window.parent;
  var D = P.document;

  ['ns-sidebar','ns-toggle','ns-overlay'].forEach(function(id) {{
    var el = D.getElementById(id);
    if (el) el.remove();
  }});

  var tmp = D.createElement('div');
  tmp.innerHTML = `{sidebar_html_escaped}`;
  while (tmp.firstChild) D.body.appendChild(tmp.firstChild);

  var isCollapsed = {collapsed_js};
  if (isCollapsed) D.body.classList.add('ns-collapsed');
  else D.body.classList.remove('ns-collapsed');

  function findBridgeInput(ariaLabel) {{
    var inputs = D.querySelectorAll('input[type="text"]');
    for (var i = 0; i < inputs.length; i++) {{
      if (inputs[i].getAttribute('aria-label') === ariaLabel) return inputs[i];
    }}
    return null;
  }}

  function writeToInput(inp, value) {{
    var nativeSetter = Object.getOwnPropertyDescriptor(P.HTMLInputElement.prototype, 'value').set;
    nativeSetter.call(inp, value);
    inp.dispatchEvent(new P.Event('input', {{bubbles: true}}));
    inp.dispatchEvent(new P.KeyboardEvent('keydown', {{key:'Enter',code:'Enter',keyCode:13,bubbles:true}}));
  }}

  function writeToBridge(ariaLabel, value, maxTries) {{
    maxTries = maxTries || 8;
    var inp = findBridgeInput(ariaLabel);
    if (inp) {{ writeToInput(inp, value); return; }}
    if (maxTries > 0) setTimeout(function() {{ writeToBridge(ariaLabel, value, maxTries - 1); }}, 100);
  }}

  P.nsNav = function(page) {{
    D.querySelectorAll('.ns-item').forEach(function(el) {{
      el.classList.remove('ns-active');
      if (el.getAttribute('onclick') === "nsNav('" + page + "')") el.classList.add('ns-active');
    }});
    if (P.innerWidth <= 768) P.nsMobileClose();
    writeToBridge('ns_page_input', page);
  }};

  P.nsToggle = function() {{
    var sb = D.getElementById('ns-sidebar');
    var btn = D.getElementById('ns-toggle');
    if (!sb) return;
    var nowCollapsed = sb.classList.toggle('ns-collapsed');
    D.body.classList.toggle('ns-collapsed', nowCollapsed);
    if (btn) btn.innerHTML = nowCollapsed
      ? '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" style="display:block"><polyline points="9 18 15 12 9 6"/></svg>'
      : '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" style="display:block"><polyline points="15 18 9 12 15 6"/></svg>';
    writeToBridge('ns_collapse_input', nowCollapsed ? '__collapsed__' : '__expanded__');
  }};

  P.nsMobileClose = function() {{
    var sb = D.getElementById('ns-sidebar');
    if (sb) sb.classList.remove('ns-mobile-open');
    D.body.classList.remove('ns-mobile-open');
  }};

  P.nsLaunchWidget = function() {{
    writeToBridge('ns_widget_input', '__launch__');
  }};

  function hideWidgets() {{
    ['ns_page_input', 'ns_collapse_input', 'ns_widget_input'].forEach(function(ariaLabel) {{
      var inp = findBridgeInput(ariaLabel);
      if (!inp) return;
      var container = inp.closest('[data-testid="stTextInput"]');
      if (container) {{
        container.style.cssText = 'position:absolute;width:1px;height:1px;overflow:hidden;opacity:0;pointer-events:none;top:-9999px;left:-9999px;';
      }}
    }});
  }}
  hideWidgets();
  setTimeout(hideWidgets, 200);
  setTimeout(hideWidgets, 600);

}})();
</script>
</body>
</html>
"""


def render_sidebar() -> str:
    """
    Render the collapsible sidebar and return the active page name.

    Uses st.components.v1.html to inject the sidebar into the parent
    document, bypassing Streamlit's HTML sanitiser entirely.

    Returns:
        str: Currently active page name.
    """
    # ── session state ─────────────────────────────────────────────────────────
    if "sidebar_collapsed" not in st.session_state:
        st.session_state.sidebar_collapsed = False
    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"

    collapsed: bool = st.session_state.sidebar_collapsed
    current_page: str = st.session_state.page

    # ── bridge widgets ──────────────────────────────────────────────────────
    # Both widgets use no value= so Streamlit preserves whatever JS wrote.
    # State is initialised once via session_state defaults below.
    # NEVER write to these keys after the widgets are instantiated —
    # Streamlit raises StreamlitAPIException if you do.

    # Nav bridge — initialise to current page on first load only
    if "_ns_page_bridge" not in st.session_state:
        st.session_state["_ns_page_bridge"] = current_page
    nav_input = st.text_input(
        "ns_page_input",
        key="_ns_page_bridge",
        label_visibility="hidden",
    )

    # Collapse bridge
    if "_ns_collapse_bridge" not in st.session_state:
        st.session_state["_ns_collapse_bridge"] = ""
    collapse_input = st.text_input(
        "ns_collapse_input",
        key="_ns_collapse_bridge",
        label_visibility="hidden",
    )

    # Widget launch bridge
    if "_ns_widget_bridge" not in st.session_state:
        st.session_state["_ns_widget_bridge"] = ""
    widget_input = st.text_input(
        "ns_widget_input",
        key="_ns_widget_bridge",
        label_visibility="hidden",
    )

    _last_page      = st.session_state.get("_ns_page_last", "")
    _last_collapsed = st.session_state.get("_ns_collapse_last", "")
    _last_widget    = st.session_state.get("_ns_widget_last", "")

    # ── process bridge values ─────────────────────────────────────────────────
    selected_page = current_page

    # Navigation bridge: only act on a new page signal from JS.
    nav_val = (nav_input or "").strip()
    if nav_val in _KNOWN_PAGES and nav_val != _last_page:
        st.session_state["_ns_page_last"] = nav_val
        selected_page = nav_val

    # Collapse bridge: only act on a fresh signal, never re-fire on reruns.
    collapse_val = (collapse_input or "").strip()
    if collapse_val in ("__collapsed__", "__expanded__") and collapse_val != _last_collapsed:
        st.session_state["_ns_collapse_last"] = collapse_val
        if collapse_val == "__collapsed__":
            st.session_state.sidebar_collapsed = True
            collapsed = True
        else:
            st.session_state.sidebar_collapsed = False
            collapsed = False

    # Widget launch bridge
    widget_val = (widget_input or "").strip()
    if widget_val == "__launch__" and widget_val != _last_widget:
        st.session_state["_ns_widget_last"] = widget_val
        import subprocess, sys
        from pathlib import Path
        widget_path = str(Path(__file__).resolve().parents[1] / "floating_widget.py")
        subprocess.Popen(
            [sys.executable, widget_path],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )

    # ── inject CSS into parent document ──────────────────────────────────────
    # st.markdown allows <style> tags — this is the correct injection path
    # for CSS that needs to target the parent document's elements.
    st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)

    # ── inject sidebar HTML + JS via iframe ───────────────────────────────────
    # st.components.v1.html renders an <iframe srcdoc="..."> which:
    #   - Is NOT sanitised by Streamlit's markdown renderer
    #   - Can access window.parent.document to inject into the real page
    #   - height=0 means it takes no visual space in the layout
    injector = _build_injector_js(selected_page, collapsed)
    components.html(injector, height=0, scrolling=False)

    return selected_page
