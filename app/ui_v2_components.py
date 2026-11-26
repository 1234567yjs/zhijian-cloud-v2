"""Visual-only components and document metadata for the local prototype."""

from html import escape
from pathlib import Path
from urllib.parse import quote

import streamlit as st


CSS = Path(__file__).with_name("ui_v2.css")
HEART = (
    '<path d="M6 17c-4-6 3-12 8-6l2 2 2-2c5-6 12 0 8 6l-10 9-7-6"/>'
    '<path d="M3 17h7l2-4 3 8 2-4h4"/>'
)
ICONS = {
    "heart": HEART,
    "quick": '<rect x="8" y="5" width="16" height="23" rx="3"/><path d="M12 9h8m-8 7h8m-8 5h5"/>',
    "comprehensive": '<rect x="4" y="4" width="10" height="10" rx="2"/><rect x="18" y="4" width="10" height="10" rx="2"/><rect x="4" y="18" width="10" height="10" rx="2"/><rect x="18" y="18" width="10" height="10" rx="2"/>',
}
HERO_ART = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 330 184" fill="none" color="#64cbb9">
  <g stroke="#326175" stroke-width="1">
    <path d="M18 39H312M18 72H312M18 105H312M18 138H312"/>
    <path d="M48 20V158M93 20V158M138 20V158M183 20V158M228 20V158M273 20V158"/>
    <circle cx="180" cy="91" r="69"/><circle cx="180" cy="91" r="83" stroke-dasharray="2 7"/>
  </g>
  <path d="M179 51c-17-20-43-20-54 0-10 17-2 35 10 48l45 42 45-42c12-13 20-31 10-48-11-20-37-20-54 0l-1 1z"
    stroke="#87d1c5" stroke-width="2.5"/>
  <path d="M21 99h103l11-16 11 29 13-43 13 54 14-24h124" stroke="currentColor" stroke-width="3"
    stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="21" cy="99" r="4" fill="currentColor"/><circle cx="310" cy="99" r="4" fill="currentColor"/>
</svg>
"""


def svg_image(svg, css_class=""):
    # Render trusted original vectors as local images. st.html sanitizes inline SVG.
    return f'<img class="{css_class}" src="data:image/svg+xml,{quote(svg)}" alt="" aria-hidden="true">'


def icon(name, stroke="#0b6f66"):
    return svg_image(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none" '
        f'stroke="{stroke}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'
    )


def favicon():
    return "data:image/svg+xml," + quote(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" '
        f'rx="7" fill="#0b6f66"/><g fill="none" stroke="white" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round">{HEART}</g></svg>')


def document_metadata(lang):
    # This script only applies fixed metadata to this app's own document.
    code = "zh-CN" if lang == "zh" else "en"
    st.html(f"""<script>
        (() => {{
            const root = document.documentElement;
            root.lang = "{code}";
            root.setAttribute("translate", "no");
            root.classList.add("notranslate");
            if (!document.querySelector('head meta[name="google"][content="notranslate"]')) {{
                const meta = document.createElement("meta");
                meta.name = "google"; meta.content = "notranslate";
                document.head.appendChild(meta);
            }}
        }})();
    </script>""", unsafe_allow_javascript=True)


def show_startup(t, version):
    """Mount the expendable overlay once; CSS always expires it."""
    st.html(
        f'<div class="z-startup" id="z-startup" lang="zh-CN" translate="no"><div class="z-startup-inner">'
        f'<div class="z-icon">{icon("heart", "#73e0cd")}</div><div class="z-startup-brand">知健 · ZhiJian</div>'
        f'<p>{escape(t("让健康评估更简单，让风险解释更清晰", "Simpler health assessment, clearer explanations."))}</p>'
        f'<small role="status">{escape(t("正在加载知健", "Loading ZhiJian"))} · {escape(version)}</small>'
        f'<button type="button" id="z-startup-skip">{escape(t("立即进入", "Enter now"))}</button></div></div>'
        """<script>
          (() => {
            const splash = document.getElementById("z-startup");
            if (!splash) return;
            splash.querySelector("button")?.addEventListener("click", () => { splash.hidden = true; }, {once:true});
            const listener = (event) => {
                if (event.key === "Escape") { splash.hidden = true; }
            };
            splash.addEventListener("keydown", listener);
          })();
        </script>""",
        unsafe_allow_javascript=True,
    )


def jump_to_top():
    st.html("""<script>requestAnimationFrame(() => {
      const main = document.querySelector('[data-testid="stMain"]');
      if (main) main.scrollTop = 0;
      window.scrollTo(0, 0);
    });</script>""", unsafe_allow_javascript=True)


def title(heading, caption=None):
    description = f"<p>{escape(caption)}</p>" if caption else ""
    st.html(f'<div class="z-section-title"><h2>{escape(heading)}</h2>{description}</div>')


def brand(version, build_id):
    st.html(f'<div class="z-brand" translate="no" data-build-id="{escape(build_id)}">'
            f'<span class="z-logo">{icon("heart", "#ffffff")}</span>'
            f'<div><b>知健</b><small>ZhiJian {escape(version)}</small></div></div>')


def hero(t):
    line_one = t("成人糖代谢异常风险评估", "Adult dysglycemia risk assessment")
    line_two = t("与个体化健康管理", "and personalized health management")
    summary = t("提供简易与综合评估，呈现模型解释、健康管理关注事项和独立安全提醒。",
                "Quick and comprehensive assessments with model explanations, health-management considerations, and independent safety notices.")
    st.html(f'<section class="z-hero"><div><h1><span>{escape(line_one)}</span> <span>{escape(line_two)}</span></h1>'
            f'<p>{escape(summary)}</p></div>{svg_image(HERO_ART, "z-hero-art")}</section>')


def step_progress(labels, complete, reviewed):
    current = len(labels) - 1
    if not reviewed:
        current = next((index for index, done in enumerate(complete) if not done), current)
    items = []
    for index, label in enumerate(labels):
        marker = "✓" if index < len(complete) and complete[index] else str(index + 1)
        selected = ' aria-current="step"' if current == index else ""
        items.append(f'<li{selected}><span class="z-step-dot">{marker}</span>{escape(label)}</li>')
    return '<ol class="z-progress">' + "".join(items) + "</ol>"


def score_meter(probability, label):
    percent = 100 * probability
    st.html(f'<div class="z-score" aria-label="{escape(label)}"><div>'
            f'<strong>{percent:.1f}%</strong><span>{escape(label)}</span></div>'
            f'<div aria-hidden="true"><div class="z-meter"><span style="width:{percent:.8f}%"></span></div>'
            '<div class="z-scale"><small>0%</small><small>100%</small></div></div></div>')


def shap_chart(explanation, names, chart_label, down, up):
    """Serialise the exact contribution values, using a shared symmetric scale."""
    maximum = max((abs(value) for _, value in explanation), default=0.0) or 1.0
    rows = []
    for feature, value in explanation:
        direction = "negative" if value < 0 else "positive"
        width = 50 * abs(value) / maximum
        name = escape(names.get(feature, feature))
        rows.append(
            f'<div class="z-shap-row" data-shap-value="{value!r}"><span class="z-factor">{name}</span>'
            f'<span class="z-shap-plot" aria-hidden="true"><i class="z-shap-bar {direction}" style="width:{width:.8f}%"></i></span>'
            f'<span class="z-shap-value">{value:+.4f}</span></div>'
        )
    return (f'<figure class="z-chart" aria-label="{escape(chart_label)}"><figcaption class="z-chart-key">'
            f'<b>− {escape(down)}</b><span>0 · log-odds</span><b>+ {escape(up)}</b></figcaption>'
            + "".join(rows) + "</figure>")
