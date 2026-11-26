"""ZhiJian 2.0.1, public competition demo for preset fictional cases."""

from html import escape
import json
from pathlib import Path
import sys

import streamlit as st


ROOT = Path(__file__).resolve().parent
APP = ROOT / "app"
sys.path[:0] = [str(APP), str(ROOT / "src")]
from activity_features import DOMAINS as ACTIVITY_DOMAINS
from assessment_v2 import AGE_EVIDENCE, THRESHOLDS, evaluate
from eligibility import eligibility_message
from input_validation import input_message
import ui_v2_components as ui
import ui_v2_copy as copy


st.set_page_config(page_title="知健 2.0 | ZhiJian", page_icon=ui.favicon(), layout="wide")


def open_page(page, mode=None):
    st.session_state["z_page"] = page
    st.session_state.pop("z_report", None)
    if mode is not None:
        st.session_state["z_mode"] = mode
    st.session_state["z_scroll"] = True


def change_language():
    if st.session_state.get("z_page") == "report":
        open_page("assessment")


try:
    config = json.loads((APP / "demo_cases.json").read_text(encoding="utf-8"))
    if config.get("synthetic_only") is not True or set(config["cases"]) != set(copy.CASES):
        raise ValueError("unexpected research-case bundle")
    st.html(f"<style>{ui.CSS.read_text(encoding='utf-8')}</style>")
except (OSError, ValueError, KeyError, TypeError):
    st.error("暂时无法打开研究原型。请刷新页面，或联系维护人员。 The research prototype could not open. Refresh or contact the maintainer.")
    st.stop()

page = st.session_state.get("z_page", "home")
mode = st.session_state.get("z_mode", "quick")
case_id = st.session_state.get("z_case", "ordinary")
with st.container(key="z-top"):
    brand_col, lang_col = st.columns([4, 1], vertical_alignment="center")
    with brand_col:
        ui.brand(copy.VERSION, copy.BUILD_ID)
    with lang_col:
        language = st.selectbox("语言 / Language", ("简体中文", "English"), key="z_language",
                                on_change=change_language, label_visibility="collapsed")
zh = language == "简体中文"
lang = "zh" if zh else "en"


def t(chinese, english):
    return chinese if zh else english


def pick(pair):
    return pair[0 if zh else 1]


ui.document_metadata(lang)
if "z_startup_shown" not in st.session_state:
    st.session_state["z_startup_shown"] = True
    ui.show_startup(t)
if st.session_state.pop("z_scroll", False):
    ui.jump_to_top()


def reason_message(code):
    if code in copy.REASONS:
        return pick(copy.REASONS[code])
    if code == "age" or code.startswith(("diabetes_", "pregnancy_")):
        return eligibility_message(code, lang)
    return input_message(code, lang)


def model_evidence():
    st.write(t("历史研究使用 NHANES 2013–2014 的4,648人，按同一受试者配对比较，结果未经抽样加权。",
               "The historical comparison paired both models on the same 4,648 NHANES 2013–2014 participants. Estimates are unweighted."))
    st.write(t("AUROC：综合 A 为0.76390，简易 B 为0.76499。A−B 为−0.00110（95%区间 −0.00467 至 0.00256）。未观察到综合模型的总体区分增益，也未证明两模型等效。",
               "AUROC was 0.76390 for comprehensive A and 0.76499 for quick B. A−B was −0.00110 (95% interval −0.00467 to 0.00256). The study found no overall discrimination gain and did not establish equivalence."))
    st.write(t("适用性仍需进一步研究。研究结果不能用于诊断，也未完成中国人群或临床验证。",
               "Applicability needs further study. The prototype is for research demonstrations and has not been validated clinically or in a Chinese population."))


def home():
    ui.hero(t)
    ui.title(t("选择评估方式", "Choose an assessment"),
             t("两个入口平级，可按想了解的信息选择。", "Choose either mode based on the information you want to explore."))
    columns = st.columns(2)
    descriptions = {
        "quick": (t("年龄、身高、体重", "Age, height, and weight"),
                  t("用较少信息体验研究性筛查。", "Explore research screening with fewer inputs.")),
        "comprehensive": (t("八项模型特征、SHAP解释", "Eight model features and SHAP"),
                          t("了解更多健康管理关注事项。", "Explore health-management considerations across several domains.")),
    }
    for col, option in zip(columns, copy.MODES):
        with col, st.container(key=f"z-mode-{option}"):
            name = pick(copy.MODES[option])
            fields, summary = descriptions[option]
            st.html(f'<div class="z-mode-copy"><div class="z-mode-icon z-icon">{ui.icon(option)}</div>'
                    f'<h3>{escape(name)}</h3><p>{escape(summary)}</p><div class="z-detail">{escape(fields)}</div></div>')
            st.button(t(f"体验{name}", f"Start {name.lower()}"), key=f"z_home_{option}", type="primary",
                      width="stretch", on_click=open_page, args=("assessment", option))
    with st.container(key="z-library"):
        left, right = st.columns([3, 2], vertical_alignment="center")
        with left:
            ui.title(t("科研演示案例库", "Research demo library"),
                     t("浏览11个虚构案例，体验不同年龄、资料完整度和安全提示。", "Explore 11 fictional cases covering age, incomplete information, and safety notices."))
        with right:
            st.button(t("打开科研演示", "Open research demo"), key="z_home_library",
                      width="stretch", on_click=open_page, args=("library",))
    ui.title(t("研究成果", "Research evidence"))
    facts = (
        ("4,648", t("历史队列同人配对比较", "Participants in the paired historical comparison")),
        (t("双模式", "Two modes"), t("低信息负担与多维解释", "Low-input assessment and broader explanations")),
        (t("独立安全提醒", "Separate safety notices"), t("基于有效读数判断", "Based on valid readings")),
    )
    st.html('<div class="z-proof">' + "".join(f"<div><b>{escape(k)}</b><span>{escape(v)}</span></div>"
                                              for k, v in facts) + "</div>")
    with st.expander(t("查看研究依据与限制", "Research basis and limitations")):
        model_evidence()


def set_case(widget):
    st.session_state["z_case"] = st.session_state[widget]
    st.session_state.pop("z_report", None)


def library():
    st.title(t("科研演示案例库", "Research demo library"))
    st.info(pick(copy.DEMO_SCOPE))
    ids = tuple(copy.CASES)
    key = f"z_library_case_{lang}"
    with st.container(key="z-library"):
        st.selectbox(t("选择虚构案例", "Choose a fictional case"), ids, index=ids.index(case_id),
                     format_func=lambda case: pick(copy.CASES[case]), key=key, on_change=set_case, args=(key,))
        st.write(t("选择案例后，用下方任一模式查看它在研究原型中的表现。",
                   "After selecting a case, choose either mode to explore its behavior in the prototype."))
        for column, option in zip(st.columns(2), copy.MODES):
            with column:
                name = pick(copy.MODES[option])
                st.button(t(f"用{name}打开", f"Open in {name.lower()}"), key=f"z_library_{option}",
                          type="primary", width="stretch", on_click=open_page, args=("assessment", option))
    with st.expander(t("查看案例编号与标题", "Case identifiers and titles")):
        st.html('<ul class="z-list">' + "".join(
            f'<li><code>{escape(item[2])}</code> {escape(pick(item))}</li>' for item in copy.CASES.values()) + '</ul>')


def navigation(current):
    if current == "home":
        return
    entries = [(t("返回首页", "Home"), "home")]
    if current != "library":
        entries.append((t("更换模拟案例", "Change demo case"), "library"))
    if current == "report":
        entries.append((t("返回信息核对", "Review inputs"), "assessment"))
    with st.container(key=f"z-navigation-{current}"):
        for col, (label, target) in zip(st.columns(len(entries)), entries):
            with col:
                st.button(label, key=f"z_nav_{current}_{target}", width="stretch", on_click=open_page, args=(target,))


def preset_case(case_id):
    defaults = config["defaults"]
    overrides = config["cases"][case_id]["input"]
    return {**defaults, **overrides, "activity": {**defaults["activity"], **overrides.get("activity", {})}}


def submit_case(mode, case_id, lang):
    if case_id not in config["cases"] or mode not in copy.MODES or lang not in ("zh", "en"):
        return
    # The browser selects an ID. Model and safety inputs only come from the bundled case.
    case = preset_case(case_id)
    if mode == "quick" and not case["quick_bp"]:
        case.update(bp=(), unit="mmHg")
    result = evaluate(mode, case)
    st.session_state["z_report"] = (mode, case_id, lang, result)
    st.session_state["z_page"] = "report"
    st.session_state["z_scroll"] = True


def assessment_form():
    st.title(pick(copy.MODES[mode]))
    st.info(pick(copy.DEMO_SCOPE))
    hold = t("当前案例", "Current case")
    case_label = pick(copy.CASES[case_id])
    st.html(f'<div class="z-context"><small>{escape(hold)}</small><b>{escape(case_label)}</b></div>')
    current_mode = tuple(copy.MODES)
    mode_key = f"z_active_mode_{lang}"

    def switch_mode():
        st.session_state["z_mode"] = st.session_state[mode_key]
        st.session_state.pop("z_report", None)

    st.radio(t("切换评估方式", "Switch assessment mode"), current_mode, index=current_mode.index(mode),
             format_func=lambda value: pick(copy.MODES[value]), horizontal=True, key=mode_key, on_change=switch_mode)

    case = preset_case(case_id)
    comprehensive = mode == "comprehensive"
    labels = [t("适用人群", "Eligibility"), t("基础信息", "Core information")]
    if comprehensive:
        labels += [t("补充指标", "Additional measurements"), t("活动与吸烟", "Activity and smoking")]
    labels += [t("核对与评估", "Review and assess")]
    progress = st.empty()

    def readonly_value(label, text):
        st.html(f'<div class="z-readonly"><small>{escape(label)}</small><b>{escape(text)}</b></div>')

    def number(label, initial):
        readonly_value(label, t("未提供", "Not provided") if initial is None else f"{initial:g}")
        return initial

    def choice(label, options, initial):
        readonly_value(label, options[initial])
        return initial

    answers = {None: t("未选择", "Not selected"), "no": t("否", "No"), "yes": t("是", "Yes"),
               "unknown": t("不清楚", "Unknown")}
    with st.container(key="z-step-eligibility"):
        st.subheader(f"1 · {labels[0]}")
        left, center, right = st.columns(3)
        with left:
            age = number(t("年龄（岁）", "Age (years)"), case["age"])
        with center:
            diabetes = choice(t("是否曾确诊糖尿病？", "Previously diagnosed with diabetes?"),
                              answers, case["diabetes"])
        with right:
            pregnancy = choice(t("目前是否妊娠？", "Currently pregnant?"),
                               {**answers, "not_applicable": t("不适用", "Not applicable")},
                               case["pregnancy"])
    with st.container(key="z-step-core"):
        st.subheader(f"2 · {labels[1]}")
        left, right = st.columns(2)
        with left:
            height = number(t("身高（cm）", "Height (cm)"), case["height"])
        with right:
            weight = number(t("体重（kg）", "Weight (kg)"), case["weight"])
        if height is not None and weight is not None and 120 <= height <= 220 and 30 <= weight <= 250:
            st.write(t("按录入值换算的体重指数（BMI）", "Body mass index (BMI)") +
                     f" · {weight / ((height / 100) ** 2):.1f} kg/m²")

    def blood_pressure():
        st.write(t("每次同时核对收缩压和舒张压；空白读数不计入均值。",
                   "Check both pressures for each reading. Blank readings are left out of the mean."))
        unit = choice(t("读数单位", "Reading units"), {"mmHg": "mmHg", "unknown": t("单位未确认", "Unconfirmed")},
                      case["unit"])
        values = []
        for index, (sbp, dbp) in enumerate(case["bp"], 1):
            left, right = st.columns(2)
            with left:
                first = number(t(f"第{index}次收缩压（mmHg）", f"Reading {index} systolic (mmHg)"), sbp)
            with right:
                second = number(t(f"第{index}次舒张压（mmHg）", f"Reading {index} diastolic (mmHg)"), dbp)
            values.append((first, second))
        return values, unit

    readings, unit = [], "mmHg"
    activity = {}
    waist = sex = smoking = None
    stage_complete = [age is not None and diabetes in {"no", "yes"} and pregnancy in {"no", "yes", "not_applicable"},
                      height is not None and weight is not None]
    if comprehensive:
        with st.container(key="z-step-extra"):
            st.subheader(f"3 · {labels[2]}")
            left, right = st.columns(2)
            with left:
                waist = number(t("腰围（cm）", "Waist circumference (cm)"), case["waist"])
            with right:
                sex = choice(t("模型所用性别", "Sex used by the model"),
                             {None: t("未选择", "Not selected"), 1: t("男", "Male"), 2: t("女", "Female")}, case["sex"])
            with st.expander(t("血压 · 核对前三次读数", "Blood pressure · Check the first three readings"), expanded=True):
                readings, unit = blood_pressure()
            st.caption(t("综合模式至少需要两次完整有效的血压读数。这是待医学审定的原型录入要求。",
                         "Comprehensive assessment needs at least two complete valid readings. This prototype input rule awaits medical review."))
        with st.container(key="z-step-lifestyle"):
            st.subheader(f"4 · {labels[3]}")
            smoking = choice(t("吸烟情况", "Smoking status"),
                             {None: t("未选择", "Not selected"), 0: t("从不吸烟", "Never smoked"),
                              1: t("曾经吸烟", "Former smoker"), 2: t("目前吸烟", "Currently smokes")},
                             case["smoking"])
            options = {None: t("未选择", "Not selected"), "yes": t("参加", "Yes"), "no": t("不参加", "No"),
                       "unknown": t("不清楚", "Unknown"), "refused": t("不愿回答", "Prefer not to answer")}
            with st.expander(t("查看五类身体活动", "View all five activity domains")):
                for (domain, *_), title in zip(ACTIVITY_DOMAINS, copy.DOMAINS):
                    initial = case["activity"][domain]
                    name = pick(title)
                    left, middle, right = st.columns(3)
                    with left:
                        status = choice(name, options, initial["status"])
                    days = minutes = None
                    if status == "yes":
                        with middle:
                            days = number(name + t(" · 天／周", " · days/week"), initial.get("days"))
                        with right:
                            minutes = number(name + t(" · 分钟／日", " · min/day"), initial.get("minutes"))
                    activity[domain] = {"status": status, "days": days, "minutes": minutes}
        pairs_entered = sum(sbp is not None and dbp is not None for sbp, dbp in readings)
        stage_complete += [waist is not None and sex is not None and unit == "mmHg" and pairs_entered >= 2,
                           smoking is not None and all(a["status"] == "no" or
                               (a["status"] == "yes" and a["days"] is not None and a["minutes"] is not None)
                               for a in activity.values())]
    else:
        if case["quick_bp"]:
            with st.expander(t("可选血压 · 不进入简易模型", "Optional blood pressure · Separate from the quick model"), expanded=True):
                readings, unit = blood_pressure()
        else:
            st.caption(t("简易评估未采集血压、腰围、活动或吸烟情况。", "Quick assessment did not collect blood pressure, waist, activity, or smoking information."))

    with st.container(key="z-step-review"):
        st.subheader(f"{len(labels)} · {labels[-1]}")
        st.write(t("请核对上方资料。是否适用、是否有独立提醒，将在提交后分别判断。",
                   "Check the information above. Eligibility and any separate notices are evaluated after submission."))
        progress.html(ui.step_progress(labels, stage_complete, False))
        st.button(t("生成评估报告", "Generate assessment report"), type="primary",
                  key="z_submit", width="stretch", on_click=submit_case, args=(mode, case_id, lang))


def safety_block(bp):
    key = "z-safety-flagged" if bp.notices else "z-safety"
    with st.container(key=key):
        st.subheader(t("独立安全提醒", "Independent safety notices"))
        for order, level in bp.notices:
            message = (t(f"第{order}次有效血压读数触发高度关注提醒。",
                         f"Valid blood pressure reading {order} triggered a high-attention notice.") if level == "urgent"
                       else t(f"第{order}次有效血压读数触发测量关注提醒。",
                              f"Valid blood pressure reading {order} triggered a measurement-attention notice."))
            st.warning(message)
        if bp.notices:
            st.write(t("提醒依据本次有效的单次血压读数，原型规则待医学审定。",
                       "Notices use valid individual blood pressure readings. The prototype rules await medical review."))
        elif not bp.used:
            st.info(t("血压未评估。未获得有效血压读数。", "Blood pressure was not assessed. No valid reading was available."))
        else:
            st.write(t("有效读数未触发原型规则。这不能判断血压是否正常。",
                       "No valid reading triggered a prototype rule. This does not establish normal blood pressure."))
        for order, code in bp.issues:
            st.write(t(f"第{order}次读数需要核对。", f"Check reading {order}. ") + reason_message(code))
        if bp.provided:
            st.caption(t(f"有效读数：{len(bp.used)}次（共3个录入位置）",
                         f"Valid readings: {len(bp.used)} out of 3 input positions"))
        if bp.means is not None:
            st.caption(t("有效读数均值", "Mean of valid readings") + f" · {bp.means[0]:.1f} / {bp.means[1]:.1f} mmHg")
        if len(bp.used) == 1:
            st.write(t("仅有一次有效读数，与研究测量流程不同。",
                       "Only one valid reading was available, which differs from the research protocol."))


def management_cards(concerns):
    cards = []
    for concern in concerns:
        rule_id = concern["rule_id"]
        name = pick(copy.CONCERNS[rule_id]) if rule_id in copy.CONCERNS else concern["name"][lang]
        status = concern["status"]
        details = []
        if concern["missing"]:
            missing = " / ".join(pick(copy.FIELDS[field]) for field in concern["missing"])
            details.append(t("未评估：", "Not assessed: ") + missing)
        for match in concern["matches"]:
            label = match["label"][lang]
            details.append(f"{label} · {match['value']:g}{match['unit']}")
        cards.append(f'<article class="z-management-card"><h4>{escape(name)}</h4>'
                     f'<span class="z-status {escape(status)}">{escape(pick(copy.CONCERN_STATUS[status]))}</span>' +
                     "".join(f"<p>{escape(text)}</p>" for text in details) + "</article>")
    if cards:
        st.html('<div class="z-management">' + "".join(cards) + '</div>')


def report():
    saved = st.session_state.get("z_report")
    if saved is None or saved[:3] != (mode, case_id, lang):
        open_page("assessment")
        st.rerun()
    result = saved[3]
    assessed = result.status == "result"
    st.title(t("研究性评估报告", "Research assessment report"))
    context = f"{pick(copy.CASES[case_id])} · {pick(copy.MODES[mode])}"
    st.html(f'<div class="z-context"><b>{escape(context)}</b><small>{escape(t("虚构案例", "Fictional case"))}</small></div>')
    with st.container(key="z-report"):
        if assessed:
            st.subheader(t("研究性筛查提示：阳性", "Research screening prompt: positive") if result.positive else
                         t("研究性筛查提示：阴性", "Research screening prompt: negative"))
            ui.score_meter(result.probability, t("模型输出概率", "Model probability"))
            st.caption(t("冻结筛查阈值", "Frozen screening threshold") + f" · {THRESHOLDS[mode]:.2%}")
        else:
            st.subheader(pick(copy.STATES[result.status]))
            st.write(reason_message(result.reason))
        st.write(pick(copy.SAFETY_SCOPE))
        for warning in result.warnings:
            st.warning(input_message(warning, lang))
    safety_block(result.bp)
    with st.container(key="z-boundary"):
        st.subheader(t("模型适用边界", "Applicability and limits"))
        note = copy.AGE_NOTES.get(result.age_group)
        if note:
            st.write(pick(note))
        else:
            st.write(t("本原型尚未完成临床验证，以上内容用于虚构案例演示。",
                       "This prototype has not been clinically validated. The output is for a fictional demonstration."))
    if assessed and mode == "comprehensive" and result.explanation:
        ui.title(t("模型解释 · SHAP", "Model explanation · SHAP"),
                 t("这些因素解释模型为何得到本次结果。贡献不代表病因、干预收益或医学优先级。",
                   "These factors explain the model output. Contributions do not establish causes, intervention benefits, or medical priority."))
        st.html(ui.shap_chart(result.explanation, copy.FACTORS_ZH if zh else copy.FACTORS_EN,
                              t("SHAP正负贡献图", "Signed SHAP contribution chart"),
                              t("降低模型输出", "Lowers output"), t("提高模型输出", "Raises output")))
    ui.title(t("健康管理关注事项", "Health-management considerations"),
             t("根据有效录入资料单独判断。规则待医学审定，内容仅作研究演示。",
               "These considerations use valid entered information. The rules await medical review."))
    if result.concerns:
        management_cards(result.concerns)
    else:
        st.info(t("本次没有可展示的管理评估。", "No management assessment is available for this case."))
    with st.expander(t("研究依据与技术详情", "Research basis and technical details")):
        st.write(t("冻结阈值（完整精度）", "Frozen cutoff (full precision)") + f" · `{THRESHOLDS[mode]}`")
        st.write(t("两模型均为冻结的 L2 逻辑回归。界面显示按百分比舍入，筛查判断使用完整精度。",
                   "Both models are frozen L2 logistic regressions. The displayed percentage is rounded; screening uses the full precision cutoff."))
        model_evidence()
        if result.age_group in AGE_EVIDENCE:
            count, a, b = AGE_EVIDENCE[result.age_group]
            se, sp, positives = a if mode == "comprehensive" else b
            st.write(t(f"历史年龄组 {result.age_group}（{count}人，未加权）：敏感度 {se:.2f}%，特异度 {sp:.2f}%，筛查阳性比例 {positives:.2f}%。这是组水平统计。",
                       f"Historical age group {result.age_group} ({count} participants, unweighted): sensitivity {se:.2f}%, specificity {sp:.2f}%, screen-positive rate {positives:.2f}%. These are group statistics."))
        if assessed and mode == "comprehensive" and result.explanation:
            st.write(t("SHAP按 log-odds 量纲展示未改变的模型贡献，不表达医学因果关系。",
                       "SHAP shows the original contributions on the log-odds scale without implying medical causation."))
        for concern in result.concerns:
            st.caption(f"{concern['rule_id']} · {concern['version']} · " + t("待医学审定", "Pending medical review"))
            for match in concern["matches"]:
                st.write(f"{match['label'][lang]} · {match['value']:g}{match['unit']} "
                         f"{match['comparison']} {match['threshold']:g}{match['unit']}")


with st.container(key=f"z-view-{page}"):
    navigation(page)
    {"home": home, "library": library, "assessment": assessment_form, "report": report}[page]()
