"""Pre-prediction plausibility checks for the research screening prototype.

BMI bounds are the observed nonmissing range in the 2015–2016 development
CSV (SHA-256 8E63314817D41763502C981A17786687C8F2A728BC76DC01F961D282FCC54D4F).
They define a model-evidence boundary, not a medical impossibility threshold.
"""

import math
from typing import NamedTuple


BMI_OBSERVED_MIN = 14.5
BMI_OBSERVED_MAX = 64.6
BMI_P01 = 17.9
BMI_P99 = 49.984

MESSAGES = {
    "zh": {
        "age_range": "年龄须在20至100岁之间。",
        "sex": "请选择有效的性别选项。",
        "smoking": "请选择有效的吸烟状态。",
        "bmi_invalid": "BMI输入无效，请核对身高和体重。",
        "bmi_mismatch": "身高、体重与BMI计算结果不一致，请重新填写。",
        "bmi_outside_reference": "当前BMI超出模型开发队列观测范围（14.5–64.6 kg/m²）。请核对身高和体重；即使数据正确，本原型也无法提供有依据的筛查结论，请咨询医疗专业人员。",
        "bmi_sparse_reference": "当前BMI处于模型开发队列观测范围的边缘，相关样本较少。请核对输入并谨慎解读筛查结果。",
        "waist_range": "腰围须在40至200 cm之间。",
        "bp_range": "血压数值超出本网页输入范围，请核对测量和填写。",
        "bp_order": "收缩压须大于舒张压。请核对两项数值或重新测量。",
        "height_range": "身高须在120至220 cm之间。",
        "weight_range": "体重须在30至250 kg之间。",
        "height_weight_missing": "请同时提供身高和体重。",
        "activity_invalid": "身体活动数值无效，请检查后重试。",
        "generic": "输入信息无效，请核对后重试。",
    },
    "en": {
        "age_range": "Age must be between 20 and 100 years.",
        "sex": "Please select a valid sex option.",
        "smoking": "Please select a valid smoking status.",
        "bmi_invalid": "BMI is invalid. Please check height and weight.",
        "bmi_mismatch": "Height, weight, and calculated BMI do not agree. Please enter them again.",
        "bmi_outside_reference": "This BMI is outside the observed range in the model development cohort (14.5–64.6 kg/m²). Please check height and weight. Even if correct, this prototype cannot provide a supported screening result; consult a healthcare professional.",
        "bmi_sparse_reference": "This BMI is near the edge of the observed development-cohort range, where samples are sparse. Please verify the input and interpret the screening result cautiously.",
        "waist_range": "Waist circumference must be between 40 and 200 cm.",
        "bp_range": "Blood pressure is outside this form's input range. Please check the measurement and entry.",
        "bp_order": "Systolic pressure must be greater than diastolic pressure. Check both values or repeat the measurement.",
        "height_range": "Height must be between 120 and 220 cm.",
        "weight_range": "Weight must be between 30 and 250 kg.",
        "height_weight_missing": "Please provide both height and weight.",
        "activity_invalid": "Physical activity value is invalid. Please check and try again.",
        "generic": "The input is invalid. Please check and try again.",
    },
}


def input_message(code, lang="zh"):
    language = "en" if lang == "en" else "zh"
    return MESSAGES[language].get(code, MESSAGES[language]["generic"])


class InputValidationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class ValidationResult(NamedTuple):
    warnings: tuple[str, ...]


def _finite_number(value, lower, upper, code):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputValidationError(code)
    if not math.isfinite(value) or not lower <= value <= upper:
        raise InputValidationError(code)


def validate_screening_inputs(age, sex, bmi, waist, sbp, dbp,
                              smoking_status, met_min_week,
                              height_cm=None, weight_kg=None):
    """Reject invalid inputs before model/SHAP, and flag sparse BMI tails.

    Optional raw height and weight let the web route verify its BMI calculation.
    Direct callers without them still receive the same BMI evidence-bound check.
    """
    _finite_number(age, 20, 100, "age_range")
    if isinstance(sex, bool) or sex not in (1, 2):
        raise InputValidationError("sex")
    if isinstance(smoking_status, bool) or smoking_status not in (0, 1, 2):
        raise InputValidationError("smoking")
    _finite_number(bmi, 0, math.inf, "bmi_invalid")
    _finite_number(waist, 40, 200, "waist_range")
    _finite_number(sbp, 70, 250, "bp_range")
    _finite_number(dbp, 30, 150, "bp_range")
    _finite_number(met_min_week, 0, math.inf, "activity_invalid")
    if sbp <= dbp:
        raise InputValidationError("bp_order")
    if (height_cm is None) != (weight_kg is None):
        raise InputValidationError("height_weight_missing")
    if height_cm is not None:
        _finite_number(height_cm, 120, 220, "height_range")
        _finite_number(weight_kg, 30, 250, "weight_range")
        calculated = weight_kg / ((height_cm / 100) ** 2)
        if not math.isclose(bmi, calculated, rel_tol=1e-9, abs_tol=1e-9):
            raise InputValidationError("bmi_mismatch")
    if not BMI_OBSERVED_MIN <= bmi <= BMI_OBSERVED_MAX:
        raise InputValidationError("bmi_outside_reference")
    warnings = ("bmi_sparse_reference",) if bmi < BMI_P01 or bmi > BMI_P99 else ()
    return ValidationResult(warnings)
