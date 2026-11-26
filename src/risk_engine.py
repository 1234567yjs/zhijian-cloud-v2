
from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
import shap

from eligibility import EligibilityError, check_eligibility
from activity_features import ActivityInputError, build_activity_features
from input_validation import validate_screening_inputs


# =========================================================
# 1. 项目路径
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL_DIR = PROJECT_ROOT / "models"
RULES_DIR = PROJECT_ROOT / "app" / "rules"

MODEL_PATH = MODEL_DIR / "zhijian_logistic_model.joblib"
THRESHOLD_PATH = MODEL_DIR / "screening_threshold.txt"
RULES_PATH = RULES_DIR / "intervention_rules.json"
SHAP_REFERENCE_PATH = MODEL_DIR / "shap_reference_mean.json"


# =========================================================
# 2. 加载模型、阈值、规则库
# =========================================================

model = joblib.load(MODEL_PATH)

with open(
    THRESHOLD_PATH,
    "r",
    encoding="utf-8"
) as f:
    screening_threshold = float(
        f.read().strip()
    )

with open(
    RULES_PATH,
    "r",
    encoding="utf-8"
) as f:
    intervention_rules = json.load(f)


# =========================================================
# 3. 模型变量
# =========================================================

model_features = [
    "RIDAGEYR",
    "BMXBMI",
    "BMXWAIST",
    "SBP_mean",
    "DBP_mean",
    "log_MET",
    "RIAGENDR",
    "smoking_status"
]


# =========================================================
# 4. 语言文本
# =========================================================

FACTOR_LABELS = {

    "zh": {
        "年龄": "年龄",
        "BMI": "BMI",
        "腰围": "腰围",
        "收缩压": "收缩压",
        "舒张压": "舒张压",
        "身体活动": "身体活动",
        "性别": "性别",
        "吸烟状态": "吸烟状态"
    },

    "en": {
        "年龄": "Age",
        "BMI": "BMI",
        "腰围": "Waist circumference",
        "收缩压": "Systolic blood pressure",
        "舒张压": "Diastolic blood pressure",
        "身体活动": "Physical activity",
        "性别": "Sex",
        "吸烟状态": "Smoking status"
    }
}


DOMAIN_LABELS = {

    "zh": {
        "体重与中心性肥胖": "体重与中心性肥胖",
        "血压管理": "血压管理",
        "身体活动": "身体活动",
        "吸烟管理": "吸烟管理"
    },

    "en": {
        "体重与中心性肥胖": "Weight & Central Adiposity",
        "血压管理": "Blood Pressure Management",
        "身体活动": "Physical Activity",
        "吸烟管理": "Smoking Management"
    }
}


# =========================================================
# 5. 工具函数
# =========================================================

def normalize_lang(lang):
    return "en" if lang == "en" else "zh"


def pick_lang(value, lang):

    lang = normalize_lang(lang)

    if isinstance(value, dict):

        if lang in value:
            return value[lang]

        if "zh" in value:
            return value["zh"]

        return next(
            iter(value.values())
        )

    return value


# =========================================================
# 6. 建立 SHAP 解释器
# =========================================================

preprocessor = model.named_steps[
    "preprocessor"
]

classifier = model.named_steps[
    "model"
]

feature_names = (
    preprocessor
    .get_feature_names_out()
)

reference = json.loads(SHAP_REFERENCE_PATH.read_text(encoding="utf-8"))
reference_mean = np.asarray(reference["mean"], dtype=float)
if (reference["schema"] != 1 or reference["feature_names"] != feature_names.tolist()
        or reference_mean.shape != (len(feature_names),) or not np.isfinite(reference_mean).all()):
    raise ValueError("invalid SHAP reference summary")
# Interventional LinearExplainer only needs the original masker's transformed mean.
explainer = shap.LinearExplainer(classifier, (reference_mean, None))


# =========================================================
# 7. 聚合 SHAP
# =========================================================

def calculate_aggregated_shap(
    user_df
):

    transformed = (
        preprocessor.transform(
            user_df
        )
    )

    if hasattr(
        transformed,
        "toarray"
    ):
        transformed = (
            transformed.toarray()
        )
    else:
        transformed = np.asarray(
            transformed
        )

    shap_result = explainer(
        transformed
    )

    values = (
        shap_result.values[0]
    )

    feature_index = {
        name: i
        for i, name
        in enumerate(
            feature_names
        )
    }

    aggregated = {

        "年龄":
            float(
                values[
                    feature_index[
                        "num__RIDAGEYR"
                    ]
                ]
            ),

        "BMI":
            float(
                values[
                    feature_index[
                        "num__BMXBMI"
                    ]
                ]
            ),

        "腰围":
            float(
                values[
                    feature_index[
                        "num__BMXWAIST"
                    ]
                ]
            ),

        "收缩压":
            float(
                values[
                    feature_index[
                        "num__SBP_mean"
                    ]
                ]
            ),

        "舒张压":
            float(
                values[
                    feature_index[
                        "num__DBP_mean"
                    ]
                ]
            ),

        "身体活动":
            float(
                values[
                    feature_index[
                        "num__log_MET"
                    ]
                ]
            )
    }

    sex_indices = [
        i
        for i, name
        in enumerate(
            feature_names
        )
        if name.startswith(
            "cat__RIAGENDR_"
        )
    ]

    aggregated[
        "性别"
    ] = float(
        values[
            sex_indices
        ].sum()
    )

    smoking_indices = [
        i
        for i, name
        in enumerate(
            feature_names
        )
        if name.startswith(
            "cat__smoking_status_"
        )
    ]

    aggregated[
        "吸烟状态"
    ] = float(
        values[
            smoking_indices
        ].sum()
    )

    return aggregated


# =========================================================
# 8. SHAP 作用方向
# =========================================================

def describe_shap_direction(
    value,
    lang="zh",
    small_threshold=0.02
):

    lang = normalize_lang(lang)

    if abs(value) < small_threshold:

        return (
            "相对参考水平变化较小"
            if lang == "zh"
            else "Small change relative to reference"
        )

    if value > 0:

        return (
            "使模型预测向较高方向变化"
            if lang == "zh"
            else "Shifts the model prediction higher"
        )

    return (
        "使模型预测向较低方向变化"
        if lang == "zh"
        else "Shifts the model prediction lower"
    )


# =========================================================
# 9. 安全提醒
# =========================================================

def generate_safety_messages(
    sbp,
    dbp,
    lang="zh"
):

    lang = normalize_lang(lang)

    messages = []

    if (
        sbp >= 180
        or dbp >= 120
    ):

        if lang == "zh":

            title = "血压明显升高"

            message = (
                "当前血压达到需高度关注的范围。"
                "建议在安静状态下规范复测；"
                "如持续达到该水平，或同时出现胸痛、"
                "呼吸困难、严重头痛、意识异常或神经系统症状等，"
                "应及时就医。"
            )

        else:

            title = "Markedly elevated blood pressure"

            message = (
                "Your current blood pressure is markedly elevated. "
                "Please repeat the measurement under standardized resting conditions. "
                "If this level persists, or if chest pain, shortness of breath, "
                "severe headache, altered consciousness, or neurological symptoms occur, "
                "seek prompt medical attention."
            )

        messages.append({
            "level": "urgent",
            "title": title,
            "message": message
        })

    elif (
        sbp >= 140
        or dbp >= 90
    ):

        if lang == "zh":

            title = "建议进一步进行血压评估"

            message = (
                "当前血压处于明显升高范围，"
                "建议进行规范复测并记录多次测量结果，"
                "同时咨询医疗专业人员进一步评估。"
            )

        else:

            title = "Further blood pressure evaluation is recommended"

            message = (
                "Your current blood pressure is elevated. "
                "Repeat the measurement under standardized conditions, "
                "record multiple readings, and consider further evaluation "
                "by a healthcare professional."
            )

        messages.append({
            "level": "medical_evaluation",
            "title": title,
            "message": message
        })

    return messages


# =========================================================
# 10. 健康管理关注事项：仅根据客观指标，不进行医学排序
# =========================================================

def generate_management_concerns(
    bmi,
    waist,
    sbp,
    dbp,
    met,
    smoking_status,
    lang="zh"
):

    lang = normalize_lang(lang)
    observations = {
        "BMXBMI": bmi, "BMXWAIST": waist,
        "SBP_mean": sbp, "DBP_mean": dbp,
        "MET_min_week": met, "smoking_status": smoking_status
    }
    rows = []
    # The order is for stable presentation only, never a clinical ranking.
    for domain, rule_key in domain_to_rule.items():
        rule = intervention_rules[rule_key]
        matched = []
        for condition in rule["trigger_conditions"]:
            value = observations[condition["variable"]]
            threshold = condition["threshold"]
            if condition["operator"] == ">=":
                triggered = value >= threshold
            elif condition["operator"] == "<":
                triggered = value < threshold
            elif condition["operator"] == "==":
                triggered = value == threshold
            else:
                raise ValueError("Unsupported rule operator")
            if triggered:
                matched.append(condition)
        if matched:
            reasons = []
            for condition in matched:
                variable = condition["variable"]
                unit = condition.get("unit", "")
                label = condition["label"][lang]
                reasons.append(
                    f"{label}: {observations[variable]:g}{unit} "
                    f"{condition['operator']} {condition['threshold']:g}{unit}"
                )
            rows.append({
                "domain_key": domain,
                "domain_display": DOMAIN_LABELS[lang][domain],
                "rule_key": rule_key,
                "rule_id": rule["rule_id"],
                "trigger_reason": "; ".join(reasons),
            })
    return pd.DataFrame(rows, columns=[
        "domain_key", "domain_display", "rule_key", "rule_id", "trigger_reason"
    ])


# =========================================================
# 11. 规则映射
# =========================================================

domain_to_rule = {

    "体重与中心性肥胖":
        "weight_management",

    "血压管理":
        "blood_pressure_management",

    "身体活动":
        "physical_activity",

    "吸烟管理":
        "smoking_cessation"
}


# =========================================================
# 12. 干预建议匹配
# =========================================================

def match_intervention_rules(
    concerns_df,
    lang="zh"
):

    lang = normalize_lang(lang)

    recommendations = []

    for _, row in concerns_df.iterrows():

        domain = row[
            "domain_key"
        ]

        rule_key = row["rule_key"]

        rule = (
            intervention_rules[
                rule_key
            ]
        )

        source_reference = rule.get("source_reference")
        source_verified = bool(source_reference) and rule.get("review_status") == "medically_reviewed"
        recommendations.append({
            "rule_id": row["rule_id"],
            "rule_version": rule["rule_version"],
            "review_status": rule["review_status"],
            "trigger_reason": row["trigger_reason"],

            "domain":
                row[
                    "domain_display"
                ],

            "title":
                pick_lang(
                    rule["name"],
                    lang
                ),

            "core_message":
                pick_lang(
                    rule[
                        "core_message"
                    ],
                    lang
                ),

            "actions": pick_lang(rule["actions"], lang) if source_reference else [],
            "source": pick_lang(source_reference, lang) if source_reference else "",
            "source_verified": source_verified,
        })

    return recommendations


# =========================================================
# 13. 输入检查
# =========================================================

def validate_inputs(
    age,
    sex,
    bmi,
    waist,
    sbp,
    dbp,
    smoking_status,
    met_min_week,
    height_cm=None,
    weight_kg=None
):
    return validate_screening_inputs(
        age, sex, bmi, waist, sbp, dbp, smoking_status, met_min_week,
        height_cm=height_cm, weight_kg=weight_kg
    )


# =========================================================
# 14. 核心风险评估函数
# =========================================================

def assess(
    age,
    sex,
    bmi,
    waist,
    sbp,
    dbp,
    smoking_status,
    met_min_week,
    lang="zh",
    diabetes_diagnosis=None,
    pregnancy_status=None,
    activity_answers=None,
    height_cm=None,
    weight_kg=None
):

    lang = normalize_lang(
        lang
    )

    eligibility = check_eligibility(
        age=age,
        diabetes_diagnosis=diabetes_diagnosis,
        pregnancy_status=pregnancy_status
    )
    if not eligibility.eligible:
        raise EligibilityError(eligibility.code)

    activity_features = None
    if activity_answers is not None:
        activity_features = build_activity_features(activity_answers)
        if not np.isfinite(met_min_week) or not np.isclose(
            met_min_week, activity_features.met_min_week, rtol=0, atol=1e-9
        ):
            raise ActivityInputError("mismatch")

    validate_inputs(
        age=age,
        sex=sex,
        bmi=bmi,
        waist=waist,
        sbp=sbp,
        dbp=dbp,
        smoking_status=
            smoking_status,
        met_min_week=
            met_min_week,
        height_cm=height_cm,
        weight_kg=weight_kg
    )

    # NHANES 中 80 岁以上统一编码为 80
    model_age = min(
        age,
        80
    )

    user_df = pd.DataFrame({

        "RIDAGEYR":
            [
                model_age
            ],

        "BMXBMI":
            [
                bmi
            ],

        "BMXWAIST":
            [
                waist
            ],

        "SBP_mean":
            [
                sbp
            ],

        "DBP_mean":
            [
                dbp
            ],

        "log_MET":
            [
                activity_features.log_met if activity_features is not None
                else np.log1p(met_min_week)
            ],

        "RIAGENDR":
            [
                sex
            ],

        "smoking_status":
            [
                smoking_status
            ]
    })

    # -----------------------------------------------------
    # 风险预测
    # -----------------------------------------------------

    probability = float(
        model.predict_proba(
            user_df
        )[0, 1]
    )

    screening_positive = (
        probability
        >= screening_threshold
    )

    risk_percent = (
        probability * 100
    )

    threshold_percent = (
        screening_threshold
        * 100
    )

    # -----------------------------------------------------
    # 风险等级
    # -----------------------------------------------------

    if (
        risk_percent
        <
        threshold_percent * 0.75
    ):

        risk_level_key = "low"

        risk_level = (
            "较低筛查风险"
            if lang == "zh"
            else "Lower screening risk"
        )

    elif (
        risk_percent
        <
        threshold_percent
    ):

        risk_level_key = "near"

        risk_level = (
            "接近筛查阈值"
            if lang == "zh"
            else "Near screening threshold"
        )

    else:

        risk_level_key = "high"

        risk_level = (
            "筛查风险升高"
            if lang == "zh"
            else "Elevated screening risk"
        )

    # -----------------------------------------------------
    # SHAP
    # -----------------------------------------------------

    shap_dict = (
        calculate_aggregated_shap(
            user_df
        )
    )

    # -----------------------------------------------------
    # 用户可读值
    # -----------------------------------------------------

    if lang == "zh":

        sex_text = (
            "男性"
            if sex == 1
            else "女性"
        )

        smoking_text = {
            0: "从未吸烟",
            1: "既往吸烟",
            2: "当前吸烟"
        }[
            smoking_status
        ]

        raw_values = {

            "年龄":
                f"{age:.0f} 岁",

            "性别":
                sex_text,

            "BMI":
                f"{bmi:.1f} kg/m²",

            "腰围":
                f"{waist:.1f} cm",

            "收缩压":
                f"{sbp:.0f} mmHg",

            "舒张压":
                f"{dbp:.0f} mmHg",

            "身体活动":
                (
                    f"{met_min_week:.0f} "
                    "MET-min/week"
                ),

            "吸烟状态":
                smoking_text
        }

    else:

        sex_text = (
            "Male"
            if sex == 1
            else "Female"
        )

        smoking_text = {
            0: "Never smoker",
            1: "Former smoker",
            2: "Current smoker"
        }[
            smoking_status
        ]

        raw_values = {

            "年龄":
                f"{age:.0f} years",

            "性别":
                sex_text,

            "BMI":
                f"{bmi:.1f} kg/m²",

            "腰围":
                f"{waist:.1f} cm",

            "收缩压":
                f"{sbp:.0f} mmHg",

            "舒张压":
                f"{dbp:.0f} mmHg",

            "身体活动":
                (
                    f"{met_min_week:.0f} "
                    "MET-min/week"
                ),

            "吸烟状态":
                smoking_text
        }

    modifiable = {

        "年龄": False,
        "性别": False,
        "BMI": True,
        "腰围": True,
        "收缩压": True,
        "舒张压": True,
        "身体活动": True,
        "吸烟状态": True
    }

    explanation_rows = []

    for factor, value in shap_dict.items():

        explanation_rows.append({

            "factor_key":
                factor,

            "health_factor":
                FACTOR_LABELS[
                    lang
                ][
                    factor
                ],

            "current_value":
                raw_values[
                    factor
                ],

            "shap_value":
                float(
                    value
                ),

            "direction":
                describe_shap_direction(
                    value,
                    lang=lang
                ),

            "modifiable":
                modifiable[
                    factor
                ],

            "abs_contribution":
                abs(
                    float(value)
                )
        })

    explanation_df = (
        pd.DataFrame(
            explanation_rows
        )
        .sort_values(
            "abs_contribution",
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )

    # -----------------------------------------------------
    # 健康管理关注事项，与 SHAP 解释分离
    # -----------------------------------------------------

    concerns_df = (
        generate_management_concerns(
            bmi=bmi,
            waist=waist,
            sbp=sbp,
            dbp=dbp,
            met=met_min_week,
            smoking_status=
                smoking_status,
            lang=lang
        )
    )

    recommendations = (
        match_intervention_rules(
            concerns_df,
            lang=lang
        )
    )

    safety_messages = (
        generate_safety_messages(
            sbp=sbp,
            dbp=dbp,
            lang=lang
        )
    )

    # -----------------------------------------------------
    # 输出文本
    # -----------------------------------------------------

    if lang == "zh":

        screening_result = (
            "筛查阳性"
            if screening_positive
            else "筛查阴性"
        )

        model_notice = (
            "本结果用于糖代谢异常风险筛查与健康管理辅助，"
            "不能替代临床诊断。"
        )

    else:

        screening_result = (
            "Screen Positive"
            if screening_positive
            else "Screen Negative"
        )

        model_notice = (
            "This result is intended for risk screening "
            "and health management support and does not "
            "replace clinical diagnosis."
        )

    return {

        "language":
            lang,

        "risk_probability":
            probability,

        "risk_percent":
            risk_percent,

        "risk_level_key":
            risk_level_key,

        "risk_level":
            risk_level,

        "screening_threshold":
            screening_threshold,

        "screening_positive":
            bool(
                screening_positive
            ),

        "screening_result":
            screening_result,

        "explanation":
            explanation_df,

        "shap_dict":
            shap_dict,

        "management_concerns": concerns_df,

        "recommendations":
            recommendations,

        "safety_messages":
            safety_messages,

        "model_notice":
            model_notice
    }
