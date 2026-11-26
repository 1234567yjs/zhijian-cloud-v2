"""Shared assessment and display policy for the fictional-case demo."""

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import importlib
from io import BytesIO
import json
import logging
from operator import eq, ge, lt
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from activity_features import ActivityInputError, build_activity_features
from eligibility import check_eligibility
from input_validation import (
    BMI_OBSERVED_MAX, BMI_OBSERVED_MIN, BMI_P01, BMI_P99, InputValidationError, _finite_number,
)


ROOT = Path(__file__).resolve().parents[1]
LOGGER = logging.getLogger(__name__)
FEATURES = {
    "quick": ("RIDAGEYR", "BMXBMI"),
    "comprehensive": ("RIDAGEYR", "BMXBMI", "BMXWAIST", "SBP_mean", "DBP_mean", "log_MET", "RIAGENDR", "smoking_status"),
}
THRESHOLDS = {"quick": 0.2881613862608534, "comprehensive": 0.2964271851200581}
LOCKS = {
    "B": ("models/baseline_pipeline.joblib", "613E70A6F31CC0411D49FB661B195046A900ECCE3E8A5F12EE084F5A3D417675"),
    "B_threshold": ("models/baseline_threshold.txt", "F4727277EDE64D9307ED0E4972245F0AEE6E8A4A98302F7704DCD5913BBC3037"),
    "A": ("models/zhijian_logistic_model.joblib", "9D53FFD654D754E25CA6235C4728272D359C53023D36FD7EA6224FC8A5AC88CF"),
    "A_threshold": ("models/screening_threshold.txt", "1BA131EC8593F012CEBF98917E1D4D7F07CB716764DCFEC7BFA7F9EB3D8A315D"),
    "A_background": ("models/shap_reference_mean.json", "2C6FC94CAF7794EE7750E550B38621900F383C558CA26C3F074462BFB4A49419"),
}
RULE_FIELDS = {"weight_management": ("BMXBMI", "BMXWAIST"), "blood_pressure_management": ("SBP_mean", "DBP_mean"),
               "physical_activity": ("MET_min_week",), "smoking_cessation": ("smoking_status",)}
AGE_EVIDENCE = {
    "20–39": (1720, (28.06, 92.72, 9.65), (23.98, 92.65, 9.24)),
    "40–59": (1620, (72.97, 52.81, 55.43), (74.90, 50.45, 57.65)),
    "60–79": (1056, (98.72, 1.76, 98.48), (99.45, 0.98, 99.24)),
    "80+": (252, (100.0, 0.0, 100.0), (100.0, 0.0, 100.0)),
}


@dataclass(frozen=True)
class BloodPressure:
    used: tuple[int, ...]
    means: tuple[float, float] | None
    issues: tuple[tuple[int, str], ...]
    notices: tuple[tuple[int, str], ...]
    provided: bool


@dataclass(frozen=True)
class Assessment:
    status: str
    reason: str | None
    age_group: str | None
    bmi: float | None
    bp: BloodPressure
    concerns: tuple[dict, ...]
    probability: float | None = None
    positive: bool | None = None
    explanation: tuple[tuple[str, float], ...] = ()
    warnings: tuple[str, ...] = ()


def task08_age_group(age):
    if age < 20:
        return None
    return "20–39" if age < 40 else "40–59" if age < 60 else "60–79" if age < 80 else "80+"


def training_bp_means(readings):
    readings = list(readings)[:3]
    return tuple(float(np.mean(values)) if values else None for values in
                 ([reading[column] for reading in readings if reading[column] is not None] for column in range(2)))


def check_blood_pressure(readings=(), unit="mmHg"):
    used, valid, issues, notices = [], [], [], []
    readings = tuple(readings)
    for order, (sbp, dbp) in enumerate(readings, 1):
        if sbp is None and dbp is None:
            continue
        try:
            if order > 3:
                raise InputValidationError("bp_extra")
            if unit != "mmHg":
                raise InputValidationError("bp_unit")
            if sbp is None or dbp is None:
                raise InputValidationError("bp_incomplete")
            _finite_number(sbp, 70, 250, "bp_range")
            _finite_number(dbp, 30, 150, "bp_range")
            if sbp <= dbp:
                raise InputValidationError("bp_order")
        except InputValidationError as error:
            issues.append((order, error.code))
            continue
        used.append(order)
        valid.append((sbp, dbp))
        if sbp >= 180 or dbp >= 120:
            notices.append((order, "urgent"))
        elif sbp >= 140 or dbp >= 90:
            notices.append((order, "medical_evaluation"))
    means = training_bp_means(valid) if valid and not issues else None
    return BloodPressure(tuple(used), means, tuple(issues), tuple(notices), bool(used or issues))


def _checked_bytes(lock):
    relative, expected = LOCKS[lock]
    contents = (ROOT / relative).read_bytes()
    if sha256(contents).hexdigest().upper() != expected:
        raise ValueError("asset integrity mismatch")
    return contents


@lru_cache(maxsize=1)
def _model_b():
    payload = _checked_bytes("B")
    if float(_checked_bytes("B_threshold").decode().strip()) != THRESHOLDS["quick"]:
        raise ValueError("baseline threshold mismatch")
    return joblib.load(BytesIO(payload))


@lru_cache(maxsize=1)
def _engine_a():
    _checked_bytes("A")
    _checked_bytes("A_background")
    if float(_checked_bytes("A_threshold").decode().strip()) != THRESHOLDS["comprehensive"]:
        raise ValueError("main threshold mismatch")
    engine = importlib.import_module("risk_engine")
    if engine.screening_threshold != THRESHOLDS["comprehensive"]:
        raise ValueError("main engine threshold mismatch")
    return engine


def _predict(mode, frame):
    engine = _engine_a() if mode == "comprehensive" else None
    model = engine.model if engine is not None else _model_b()
    if tuple(model.feature_names_in_) != FEATURES[mode] or not np.array_equal(model.classes_, [0, 1]):
        raise ValueError("frozen pipeline interface mismatch")
    values = np.asarray(model.predict_proba(frame), dtype=float)
    if (values.shape != (1, 2) or not np.isfinite(values).all() or not ((0 <= values) & (values <= 1)).all()
            or not np.isclose(values.sum(), 1, rtol=0, atol=1e-12)):
        raise ValueError("invalid probability")
    contributions = engine.calculate_aggregated_shap(frame) if engine is not None else {}
    if any(not np.isfinite(value) for value in contributions.values()):
        raise ValueError("invalid contribution")
    return float(values[0, 1]), tuple(sorted(((str(key), float(value)) for key, value in contributions.items()),
                                               key=lambda item: abs(item[1]), reverse=True))


@lru_cache(maxsize=1)
def _rules():
    return json.loads((ROOT / "app/rules/intervention_rules.json").read_text(encoding="utf-8"))


def management_concerns(observed):
    rules = _rules()
    operators = {">=": ge, "<": lt, "==": eq}
    result = []
    for key, expected in RULE_FIELDS.items():
        rule = rules[key]
        matched = []
        for condition in rule["trigger_conditions"]:
            value = observed.get(condition["variable"])
            if value is not None and operators[condition["operator"]](value, condition["threshold"]):
                matched.append({"label": condition["label"], "value": value, "unit": condition.get("unit", ""),
                                "comparison": condition["operator"], "threshold": condition["threshold"]})
        missing = tuple(field for field in expected if observed.get(field) is None)
        status = "triggered" if matched else "unassessed" if len(missing) == len(expected) else "partial" if missing else "not_triggered"
        result.append({"rule_id": rule["rule_id"], "version": rule["rule_version"], "name": rule["name"],
                       "review": rule["review_status"], "status": status, "missing": missing, "matches": tuple(matched)})
    return tuple(result)


def _base_inputs(values):
    age, height, weight = (values.get(key) for key in ("age", "height", "weight"))
    if age is None:
        raise InputValidationError("age_missing")
    _finite_number(age, 0, 100, "age_range")
    if int(age) != age:
        raise InputValidationError("age_range")
    if height is None or weight is None:
        raise InputValidationError("height_weight_missing")
    _finite_number(height, 120, 220, "height_range")
    _finite_number(weight, 30, 250, "weight_range")
    bmi = weight / ((height / 100) ** 2)
    if not BMI_OBSERVED_MIN <= bmi <= BMI_OBSERVED_MAX:
        raise InputValidationError("bmi_outside_reference")
    return int(age), float(bmi)


def evaluate(mode, values, predictor=None):
    if mode not in FEATURES:
        raise ValueError("unknown demo mode")
    if predictor is None:
        predictor = _predict
    bp = check_blood_pressure(values.get("bp", ()), values.get("unit", "mmHg"))
    age_group, bmi = None, None
    observed = {}
    notices = ()

    def outcome(status, reason=None, **prediction):
        return Assessment(status, reason, age_group, bmi, bp, management_concerns(observed), warnings=notices, **prediction)

    try:
        age = values.get("age")
        if age is None:
            return outcome("incomplete", "age_missing")
        _finite_number(age, 0, 100, "age_range")
        if int(age) != age:
            raise InputValidationError("age_range")
        age_group = task08_age_group(age)
        eligibility = check_eligibility(age, values.get("diabetes"), values.get("pregnancy"))
        if not eligibility.eligible:
            status = "incomplete" if eligibility.code.endswith(("_missing", "_unknown")) else "ineligible"
            return outcome(status, eligibility.code)
        age, bmi = _base_inputs(values)
        observed["BMXBMI"] = bmi
        if bmi < BMI_P01 or bmi > BMI_P99:
            notices = ("bmi_sparse_reference",)
        row = {"RIDAGEYR": min(age, 80), "BMXBMI": bmi}
        if bp.means:
            observed["SBP_mean"], observed["DBP_mean"] = bp.means
        if bp.issues:
            code = bp.issues[0][1]
            return outcome("incomplete" if code == "bp_incomplete" else "invalid", code)
        if mode == "comprehensive":
            waist, sex, smoking = (values.get(key) for key in ("waist", "sex", "smoking"))
            if waist is None or sex is None or smoking is None:
                return outcome("incomplete", "extended_missing")
            _finite_number(waist, 40, 200, "waist_range")
            if isinstance(sex, bool) or sex not in (1, 2):
                raise InputValidationError("sex")
            if isinstance(smoking, bool) or smoking not in (0, 1, 2):
                raise InputValidationError("smoking")
            observed.update(BMXWAIST=waist, smoking_status=smoking)
            activity = build_activity_features(values.get("activity"))
            observed["MET_min_week"] = activity.met_min_week
            if len(bp.used) < 2:
                return outcome("incomplete", "bp_quality")
            row.update(BMXWAIST=waist, SBP_mean=bp.means[0], DBP_mean=bp.means[1], log_MET=activity.log_met,
                       RIAGENDR=sex, smoking_status=smoking)
        if age_group != "40–59":
            return outcome("withheld", "age_evidence")
        frame = pd.DataFrame([row], columns=FEATURES[mode])
        probability, explanation = predictor(mode, frame)
        return outcome("result", probability=probability, positive=probability >= THRESHOLDS[mode],
                       explanation=explanation if mode == "comprehensive" else ())
    except InputValidationError as error:
        return outcome("incomplete" if error.code == "height_weight_missing" else "invalid", error.code)
    except ActivityInputError as error:
        return outcome("incomplete" if error.code == "missing" else "invalid", "activity_" + error.code)
    except Exception as error:
        LOGGER.error("v2_assessment_failed type=%s", type(error).__name__)
        return Assessment("error", "system", age_group, bmi, bp, ())
