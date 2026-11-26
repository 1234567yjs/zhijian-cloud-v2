"""Product safety gate for the population represented by the screening model."""

from typing import NamedTuple


class EligibilityResult(NamedTuple):
    eligible: bool
    code: str


class EligibilityError(ValueError):
    """The current screening model must not be run for this input."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


MESSAGES = {
    "zh": {
        "age": "本研究模型仅面向20岁及以上成年人；请咨询医疗专业人员选择适当检查。",
        "diabetes_yes": "您报告已有糖尿病明确诊断。当前模型不适用于此情况，不提供筛查结论；请按医疗专业人员建议进行评估和管理。",
        "diabetes_unknown": "请先核实既往糖尿病诊断情况。当前模型的适用性尚不能确认，因此不提供筛查结论。",
        "diabetes_missing": "请先确认是否曾被医生告知患有糖尿病，才能使用当前筛查模型。",
        "pregnancy_yes": "您报告目前处于妊娠期。当前模型不适用于妊娠期，不提供筛查结论；请咨询产科或其他医疗专业人员。",
        "pregnancy_unknown": "请先核实当前妊娠状态。当前模型的适用性尚不能确认，因此不提供筛查结论。",
        "pregnancy_missing": "请先确认当前妊娠状态，或选择“不适用”，才能使用当前筛查模型。",
        "invalid": "适用人群确认信息无效，请重新选择。",
    },
    "en": {
        "age": "This research model is for adults aged 20 or older. Please ask a healthcare professional about appropriate testing.",
        "diabetes_yes": "You report a previous diabetes diagnosis. This model is not intended for this situation and will not provide a screening result. Follow your healthcare professional's advice for evaluation and care.",
        "diabetes_unknown": "Please clarify your previous diabetes diagnosis status. Model applicability cannot be confirmed, so no screening result is provided.",
        "diabetes_missing": "Please confirm whether a clinician has ever told you that you have diabetes before using this screening model.",
        "pregnancy_yes": "You report a current pregnancy. This model is not intended for use during pregnancy and will not provide a screening result. Please consult an obstetric or other healthcare professional.",
        "pregnancy_unknown": "Please clarify your current pregnancy status. Model applicability cannot be confirmed, so no screening result is provided.",
        "pregnancy_missing": "Please confirm your current pregnancy status, or select 'Not applicable', before using this screening model.",
        "invalid": "The eligibility answers are invalid. Please select them again.",
    },
}


def check_eligibility(age, diabetes_diagnosis=None, pregnancy_status=None):
    """Return an explicit decision before any model or SHAP computation.

    diabetes_diagnosis: yes/no/unknown; pregnancy_status:
    yes/no/not_applicable/unknown. Missing answers fail closed.
    Pregnancy is never inferred from the model's binary sex feature.
    """
    if not isinstance(age, (int, float)) or not (age >= 20):
        return EligibilityResult(False, "age")
    if diabetes_diagnosis is None:
        return EligibilityResult(False, "diabetes_missing")
    if diabetes_diagnosis not in ("yes", "no", "unknown"):
        return EligibilityResult(False, "invalid")
    if diabetes_diagnosis != "no":
        return EligibilityResult(False, "diabetes_" + diabetes_diagnosis)
    if pregnancy_status is None:
        return EligibilityResult(False, "pregnancy_missing")
    if pregnancy_status not in ("yes", "no", "not_applicable", "unknown"):
        return EligibilityResult(False, "invalid")
    if pregnancy_status in ("yes", "unknown"):
        return EligibilityResult(False, "pregnancy_" + pregnancy_status)
    return EligibilityResult(True, "eligible")


def eligibility_message(code, lang="zh"):
    language = "en" if lang == "en" else "zh"
    return MESSAGES[language].get(code, MESSAGES[language]["invalid"])
