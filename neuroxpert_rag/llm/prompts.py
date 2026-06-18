"""Prompt templates used by LLM-backed extractors."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from neuroxpert_rag.pilot.schemas import KB_RECORD_FIELDS


def kb_json_schema_hint() -> str:
    """Human-readable schema hint for the model.

    We keep it as a simple description rather than JSON Schema to stay lightweight.
    """

    fields = ", ".join(KB_RECORD_FIELDS)
    return (
        "You must output EXACTLY one JSON object (no markdown). "
        f"The object MUST contain ALL of these keys: {fields}. "
        "If a value is unknown, use null."
    )


def build_extraction_prompt(paper: Dict[str, Any]) -> str:
    """Build a strict prompt for extracting one KB record from a paper."""

    title = (paper.get("title") or "").strip()
    abstract = (paper.get("abstract") or "").strip()
    journal = (paper.get("journal") or "").strip()
    year = paper.get("year")
    query = paper.get("query")
    pmid = paper.get("pmid")

    # Provide the record skeleton to reduce missing keys.
    skeleton = {k: None for k in KB_RECORD_FIELDS}
    skeleton.update(
        {
            "source": "pubmed",
            "source_id": pmid,
            "query": query,
            "title": title,
            "year": year,
            "journal": journal,
            "citation_id": pmid,
        }
    )

    return "\n".join(
        [
            kb_json_schema_hint(),
            "\nRules:",
            "- Base claims ONLY on the provided title/abstract.",
            "- Do NOT output empty strings. Use null or the string 'unknown'.",
            "- supporting_sentence MUST be a verbatim sentence copied from the abstract (or null).",
            "- evidence_strength is a float in [0,1] representing strength of evidence in THIS abstract.",
            "- extraction_confidence is one of: low, medium, high.",
            "- relationship should be a short label like associated_with / predicts / correlates_with.",
            "- direction must be: higher / lower / unclear.",
            "- Use direction='unclear' unless the supporting_sentence explicitly states positive, negative, increased, decreased, higher, lower, inverse, or predicts.",
            "- directness must be: direct / indirect / background / unclear.",
            "- directness='direct' only if the supporting_sentence itself names both the phenotype and the brain feature/system.",
            "- directness='indirect' if the sentence supports a nearby construct but not the exact phenotype or feature.",
            "- directness='background' if the sentence is only general context, a study aim, or a broad conclusion.",
            "- Do NOT infer a BIS subscale unless the supporting_sentence explicitly names it.",
            "- If the sentence says only BIS, Barratt, trait impulsivity, impulsivity, discounting, risky decision-making, hyperactivity, or symptoms, use phenotype='impulsivity (general)' unless a specific BIS subscale is explicitly named.",
            "- feature_type must match the sentence exactly when possible.",
            "- Use feature_type='functional connectivity' only for FC/rsFC/connectivity between brain regions or networks.",
            "- Use feature_type='dynamic connectivity' for dynamic FC, dFC, connectivity states, time-varying connectivity, or effective connectivity.",
            "- Use feature_type='BOLD variability' for ALFF, ReHo, BOLD variability, temporal variability, tSTD, MSSD, or signal variability.",
            "- Use feature_type='structural connectivity' for anatomical/structural circuits or white-matter connectivity.",
            "- Use feature_type='EEG connectivity' for EEG source or scalp connectivity.",
            "- Use feature_type='covariates' only for age, sex, diagnosis, motion, or demographics.",
            "- brain_system is often not explicit in abstracts; use 'unknown' unless named (DMN, salience, etc.).",
            "\nControlled vocab hints:",
            "- phenotype: nonplanning impulsivity | motor impulsivity | attentional impulsivity | impulsivity (general) | BIS total | unknown",
            "- feature_type: functional connectivity | dynamic connectivity | BOLD variability | structural connectivity | EEG connectivity | covariates | unknown",
            "- brain_system: default mode network | frontoparietal/control network | salience/ventral attention network | somatomotor network | unknown",
            "\nPaper:",
            f"PMID: {pmid}",
            f"Title: {title}",
            f"Journal: {journal}",
            f"Year: {year}",
            f"Query provenance: {query}",
            "Abstract:",
            abstract or "(no abstract)",
            "\nReturn JSON object matching this skeleton (fill values):",
            json.dumps(skeleton, ensure_ascii=False),
        ]
    )
