"""Schema definitions for NeuroXpert-RAG pilots.

We keep schemas as plain Python dict structures so we can:
- validate extracted objects consistently
- keep the extraction model pluggable (placeholder now; LLM later)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


KB_RECORD_FIELDS: List[str] = [
    # provenance
    "source",  # e.g. pubmed
    "source_id",  # e.g. PMID
    "query",
    "title",
    "year",
    "journal",
    # extracted knowledge
    "brain_system",
    "feature_type",
    "phenotype",
    "diagnostic_context",
    "relationship",
    "direction",
    "mechanism",
    "directness",  # direct | indirect | background | unclear
    "evidence_strength",  # float in [0, 1]
    "supporting_sentence",
    # citation
    "citation_id",  # PMID or DOI
    # extraction meta
    "extraction_model",
    "extraction_confidence",
]


def empty_kb_record() -> Dict[str, Any]:
    """Return an empty knowledge-base record with all fields present."""

    return {k: None for k in KB_RECORD_FIELDS}


def _norm_label(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.lower()
    text = re.sub(r"[_\-/]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_feature_type(value: Any) -> str:
    """Map model wording variants onto the controlled feature vocabulary."""

    text = _norm_label(value)
    if text is None or text in {"none", "null", "n/a", "na"}:
        return "unknown"

    if any(tok in text for tok in ["alff", "reho", "bold", "variability", "temporal variability", "tstd", "mssd"]):
        return "BOLD variability"
    if any(tok in text for tok in ["dynamic", "dfc", "time varying", "connectivity state", "effective connectivity"]):
        return "dynamic connectivity"
    if any(tok in text for tok in ["structural", "anatomical", "white matter", "gray matter", "grey matter", "volume"]):
        return "structural connectivity"
    if "eeg" in text or "alpha band" in text or "source connectivity" in text:
        return "EEG connectivity"
    if any(tok in text for tok in ["covariate", "age", "sex", "motion", "demographic"]):
        return "covariates"
    if any(tok in text for tok in ["functional connectivity", "resting state connectivity", "resting state functional connectivity", "rsfc", " fc", "connectome", "connectivity"]):
        return "functional connectivity"
    return "unknown"


def normalize_phenotype(value: Any) -> str:
    """Map phenotype variants onto the controlled phenotype vocabulary."""

    text = _norm_label(value)
    if text is None or text in {"none", "null", "n/a", "na"}:
        return "unknown"
    if any(tok in text for tok in ["nonplanning", "non planning", "non planning"]):
        return "nonplanning impulsivity"
    if "motor" in text:
        return "motor impulsivity"
    if any(tok in text for tok in ["attention", "attentional"]):
        return "attentional impulsivity"
    if "bis total" in text or "barratt total" in text:
        return "BIS total"
    if any(tok in text for tok in ["impuls", "bis", "barratt", "risk taking", "risky", "discounting", "hyperactivity"]):
        return "impulsivity (general)"
    return "unknown"


def normalize_direction(value: Any) -> str:
    """Normalize association direction to higher/lower/unclear."""

    text = _norm_label(value)
    if text is None or text in {"none", "null", "n/a", "na", "unknown"}:
        return "unclear"
    if any(tok in text for tok in ["positive", "higher", "increased", "increase", "greater", "elevated"]):
        return "higher"
    if any(tok in text for tok in ["negative", "lower", "decreased", "decrease", "reduced", "inverse"]):
        return "lower"
    if text in {"higher", "lower", "unclear"}:
        return text
    return "unclear"


def normalize_directness(value: Any) -> str:
    text = _norm_label(value)
    if text in {"direct", "indirect", "background", "unclear"}:
        return text
    return "unclear"


def normalize_kb_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize controlled-vocabulary fields in-place and return ``rec``."""

    rec["feature_type"] = normalize_feature_type(rec.get("feature_type"))
    rec["phenotype"] = normalize_phenotype(rec.get("phenotype"))
    rec["direction"] = normalize_direction(rec.get("direction"))
    rec["directness"] = normalize_directness(rec.get("directness"))
    return rec


def validate_kb_record(obj: Dict[str, Any]) -> List[str]:
    """Lightweight validator. Returns a list of issues (empty if OK)."""

    issues: List[str] = []
    missing = [k for k in KB_RECORD_FIELDS if k not in obj]
    if missing:
        issues.append(f"missing fields: {missing}")

    # evidence_strength
    ev = obj.get("evidence_strength")
    if ev is not None:
        try:
            evf = float(ev)
            if not (0.0 <= evf <= 1.0):
                issues.append("evidence_strength out of [0,1]")
        except Exception:
            issues.append("evidence_strength not a number")

    return issues
