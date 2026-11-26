"""Bilingual display copy for the local research prototype."""

VERSION = "2.0.2"
BUILD_ID = "cloud-competition-2.0.2"

MODES = {
    "quick": ("简易评估", "Quick Assessment"),
    "comprehensive": ("综合健康评估", "Comprehensive Assessment"),
}

# Titles are independent of the frozen case inputs and stable identifiers.
CASES = {
    "ordinary": ("普通成年人健康评估", "Adult health assessment", "X"),
    "middle": ("中年人健康评估", "Middle-aged adult assessment", "Y"),
    "young": ("年轻人群筛查局限", "Screening limits for younger adults", "YOUNG"),
    "older": ("老年人群筛查局限", "Screening limits for older adults", "OLDER"),
    "topcode": ("80岁及以上人群适用性", "Applicability for adults aged 80 and over", "TOPCODE"),
    "bp_alert": ("血压异常安全提醒", "Blood pressure safety notice", "BP"),
    "diagnosed": ("已确诊糖尿病人群", "Prior diabetes diagnosis", "DIAG"),
    "unknown": ("适用性信息不完整", "Incomplete eligibility information", "UNKNOWN"),
    "single_bp": ("血压测量次数不足", "Too few blood pressure readings", "SINGLE-BP"),
    "bad_bp": ("血压输入异常", "Invalid blood pressure entry", "BAD-BP"),
    "missing": ("健康信息缺失", "Missing health information", "MISSING"),
}

STATES = {
    "withheld": ("暂缓给出筛查结论", "Screening outcome withheld"),
    "ineligible": ("不符合适用条件", "Eligibility criteria not met"),
    "incomplete": ("必要信息不完整", "Required information is incomplete"),
    "invalid": ("部分输入不符合要求", "Some inputs are invalid"),
    "error": ("暂时无法完成评估", "Assessment temporarily unavailable"),
}

AGE_NOTES = {
    "20–39": ("历史队列中，两种模型在20–39岁组漏筛较多，因此暂不提供该年龄组的个人筛查结论。",
              "Both models missed many cases among adults aged 20–39 in the historical cohort. Individual screening outcomes are withheld for this group."),
    "40–59": ("历史队列的40–59岁组仍有漏筛和误报。",
              "False negatives and false positives still occurred among adults aged 40–59 in the historical cohort."),
    "60–79": ("历史队列中，两种模型在60–79岁组假阳性较多，因此暂不提供该年龄组的个人筛查结论。",
              "Both models produced many false positives among adults aged 60–79 in the historical cohort. Individual screening outcomes are withheld for this group."),
    "80+": ("历史调查将80岁及以上统一记录为80岁。两种模型在该组均提示阳性，因此暂不提供个人筛查结论。",
            "The survey coded all ages 80 and above as 80. Both models flagged everyone in that historical group, so individual screening outcomes are withheld."),
}

REASONS = {
    "age_missing": ("请填写年龄。", "Enter an age."),
    "diabetes_yes": ("既往已确诊糖尿病，超出当前模型的筛查范围。",
                     "A prior diabetes diagnosis falls outside the current model’s screening scope."),
    "diabetes_unknown": ("既往糖尿病诊断情况未知，暂无法确认是否适用。",
                         "Eligibility cannot be confirmed when prior diabetes diagnosis status is unknown."),
    "pregnancy_yes": ("当前妊娠，超出模型的筛查范围。", "Current pregnancy falls outside the model’s screening scope."),
    "pregnancy_unknown": ("妊娠状态未知，暂无法确认是否适用。", "Eligibility cannot be confirmed when pregnancy status is unknown."),
    "extended_missing": ("请补齐腰围、性别和吸烟情况。", "Enter the waist measurement, sex, and smoking status."),
    "bp_quality": ("综合评估需要至少两次完整、有效的血压读数。只有一次时，可查看该次读数的独立安全提醒。",
                   "Comprehensive assessment needs at least two complete, valid blood pressure readings. A single reading can still be checked for a separate safety notice."),
    "bp_incomplete": ("每次血压须填写收缩压和舒张压，或将该次两项都留空。", "Enter both systolic and diastolic values for a reading or leave both blank."),
    "bp_extra": ("评估使用前三次血压读数。", "The assessment uses the first three blood pressure readings."),
    "bp_unit": ("请先确认血压单位为 mmHg。", "Confirm that the blood pressure unit is mmHg."),
    "system": ("暂时无法完成评估，请返回首页重试或联系维护人员。",
               "The assessment could not be completed. Return to the home page to retry, or contact support."),
    "age_evidence": ("现有证据不足以支持这个年龄组的常规筛查结论。", "Current evidence is insufficient for a routine screening outcome in this age group."),
    "activity_missing": ("请核对五类身体活动。未知或缺失的回答不能按零计算。", "Check all five activity domains. Unknown or missing answers are not counted as zero."),
    "activity_days": ("每周参与天数应为1至7天。", "Enter 1 to 7 days per week."),
    "activity_minutes": ("每天的活动时间须大于0分钟且小于1440分钟。", "Daily activity must be longer than 0 and shorter than 1,440 minutes."),
    "activity_contradictory": ("选择不参加时，请将天数和分钟数留空。", "Leave days and minutes blank for an activity marked no."),
    "activity_weekly_total": ("五类活动的合计时间不能超过一周总时长。", "The combined duration cannot exceed one week."),
}

DOMAINS = (
    ("高强度工作活动", "Vigorous activity at work"),
    ("中等强度工作活动", "Moderate activity at work"),
    ("出行步行或骑车", "Walking or cycling for transport"),
    ("高强度休闲活动", "Vigorous recreation"),
    ("中等强度休闲活动", "Moderate recreation"),
)

FIELDS = {
    "BMXBMI": ("体重指数（BMI）", "Body mass index (BMI)"),
    "BMXWAIST": ("腰围", "Waist circumference"),
    "SBP_mean": ("收缩压", "Systolic blood pressure"),
    "DBP_mean": ("舒张压", "Diastolic blood pressure"),
    "MET_min_week": ("身体活动", "Physical activity"),
    "smoking_status": ("吸烟情况", "Smoking status"),
}

FACTORS_EN = {"年龄": "Age", "BMI": "BMI", "腰围": "Waist circumference",
              "收缩压": "Systolic blood pressure", "舒张压": "Diastolic blood pressure",
              "身体活动": "Physical activity", "性别": "Sex", "吸烟状态": "Smoking status"}
FACTORS_ZH = {"吸烟状态": "吸烟情况"}

CONCERNS = {
    "MGT-WEIGHT-01": ("体重与中心性肥胖管理", "Weight and central adiposity"),
    "MGT-BP-01": ("血压管理", "Blood pressure"),
    "MGT-ACTIVITY-01": ("身体活动管理", "Physical activity"),
    "MGT-SMOKING-01": ("吸烟管理", "Smoking"),
}

CONCERN_STATUS = {
    "triggered": ("触发关注", "Attention flagged"),
    "partial": ("部分指标未评估", "Partly assessed"),
    "unassessed": ("未评估", "Not assessed"),
    "not_triggered": ("未触发提醒", "No notice triggered"),
}

SAFETY_SCOPE = ("阳性不能确诊，阴性不能排除糖代谢异常。", "A positive screen cannot establish a diagnosis. A negative screen cannot rule out dysglycemia.")
CLINICAL_LIMITS = ("结果仅供研究参考，不能用于诊断。模型尚未完成中国人群验证或临床验证。",
                   "Results are for research reference only and cannot be used for diagnosis. The models have not been validated clinically or in a Chinese population.")
CASE_SCOPE = ("预设案例为虚构资料，只读。", "Preset cases are fictional and read-only.")
