"""Track-A controlled fault-injection stress test (Step 4a / Experiment 3, Track A). Deterministic; no model calls.

Uses the production Track-A code unchanged (neuroxpert_rag.pilot.kb_audit.audit_record, schemas.validate_kb_record,
i.e. the same functions prepare_semantic_audit.prepare_rows applies): pass = schema_valid & citation_valid &
sentence_present & sentence_anchored.
Base rows: every archived 700-abstract record (all three extractors) that passes Track A with a non-empty sentence.
Each fault is applied programmatically to ONE base row at a time; the corpus is untouched.

Fault classes
  provenance/content corruptions (Track A should REJECT -> sensitivity):
    wrong_pmid_in_corpus, wrong_pmid_not_in_corpus, sentence_from_other_pmid, number_changed, direction_word_changed,
    sentence_composed_two_abstracts, word_dropped, schema_missing_field, schema_strength_out_of_range
  normalisation-only variants (Track A should RETAIN -> specificity):
    whitespace_variant, nbsp_variant, trailing_period_removed
  surface variants outside the whitespace-normalisation contract (behaviour reported, not prejudged):
    case_variant, unicode_dash_quote_variant, truncated_quote
"""
import csv, json, random, re, collections, pathlib, sys
sys.path.insert(0, "/Users/irfankhan/Documents/project 4/Egyptial_Informatics_Journal")
from neuroxpert_rag.pilot.kb_audit import audit_record, load_pubmed_corpus_jsonl
from neuroxpert_rag.pilot.schemas import KB_RECORD_FIELDS, validate_kb_record
SRC = pathlib.Path("/Users/irfankhan/Documents/project 4/Egyptial_Informatics_Journal/neuroxpert_rag")
FIG = SRC / "results_package_mature_2026_05_29/03_figure_source_data"; OUT = pathlib.Path(__file__).parent
CORPUS = SRC / "data/pilot/pubmed_corpus_700_abstracts.jsonl"
MODELS = {"Llama 3.1 8B": "final_llama31_8b_700", "Qwen 2.5 7B": "final_qwen25_7b_700", "Mistral 7B": "final_mistral7b_700"}
tb = lambda v: str(v).strip().lower() in ("true", "1", "yes", "t")
corpus = load_pubmed_corpus_jsonl(str(CORPUS)); pmids = sorted(corpus)
rng = random.Random(20260914)

def to_kb(r):
    """audit-sheet row -> KB record as the extractor would have produced it (all fields present)."""
    kb = {k: "" for k in KB_RECORD_FIELDS}
    kb.update(source="pubmed", source_id=r["pmid"], query=r["query"], title=r["title"], year=r["year"], journal=r["journal"],
              brain_system=r["extracted_brain_system"], feature_type=r["extracted_feature_type"], phenotype=r["extracted_phenotype"],
              diagnostic_context=r["extracted_diagnostic_context"], relationship=r["extracted_relationship"], direction=r["extracted_direction"],
              mechanism=r["extracted_mechanism"], directness=r["extracted_directness"], evidence_strength=r["evidence_strength"],
              supporting_sentence=r["supporting_sentence"], citation_id=r["pmid"])
    return kb
def track_a(kb):
    issues = validate_kb_record(kb); aud = audit_record(kb, corpus); sent = (kb.get("supporting_sentence") or "").strip()
    st = {"schema_valid": not issues, "citation_valid": bool(aud["citation_valid"]), "sentence_present": bool(sent), "sentence_anchored": bool(aud["evidence_anchored"])}
    st["pass"] = all(st.values()); return st

bases = []
for m, d in MODELS.items():
    for r in csv.DictReader(open(FIG / d / "semantic_llm_verifier_all.csv", encoding="utf-8")):
        if all(tb(r[k]) for k in ("schema_valid", "citation_valid", "sentence_present", "sentence_anchored")) and r["supporting_sentence"].strip():
            kb = to_kb(r); assert track_a(kb)["pass"], (m, r["pmid"], r["record_id"])   # production status reproduced
            bases.append((m, r["record_id"], kb))
print("base rows passing Track A (reproduced with production code):", len(bases))

DIR_WORDS = [("higher", "lower"), ("lower", "higher"), ("increased", "decreased"), ("decreased", "increased"), ("greater", "smaller"),
             ("reduced", "enhanced"), ("positive", "negative"), ("negative", "positive"), ("stronger", "weaker"), ("weaker", "stronger")]
def other_sentence(pmid):
    for _ in range(50):
        p = rng.choice(pmids)
        if p == pmid: continue
        sents = [s for s in re.split(r"(?<=[.!?])\s+", corpus[p].get("abstract") or "") if len(s.split()) >= 8]
        if sents: return p, rng.choice(sents)
    return None, None
def faults(kb):
    s = kb["supporting_sentence"]; pm = kb["citation_id"]; words = s.split(); out = []
    p2 = rng.choice([p for p in pmids if p != pm]); out.append(("wrong_pmid_in_corpus", {"citation_id": p2, "source_id": p2}))
    fake = str(90000000 + rng.randint(0, 9999999)); out.append(("wrong_pmid_not_in_corpus", {"citation_id": fake, "source_id": fake}))
    _, s2 = other_sentence(pm)
    if s2: out.append(("sentence_from_other_pmid", {"supporting_sentence": s2}))
    m = re.search(r"\d", s)
    if m:
        d = s[m.start()]; out.append(("number_changed", {"supporting_sentence": s[:m.start()] + str((int(d) + 1) % 10) + s[m.end():]}))
    for a, b in DIR_WORDS:
        if re.search(rf"\b{a}\b", s): out.append(("direction_word_changed", {"supporting_sentence": re.sub(rf"\b{a}\b", b, s, count=1)})); break
    if s2 and len(words) >= 8:
        w2 = s2.split(); out.append(("sentence_composed_two_abstracts", {"supporting_sentence": " ".join(words[: len(words) // 2] + w2[len(w2) // 2:])}))
    if len(words) >= 8:
        k = len(words) // 2; out.append(("word_dropped", {"supporting_sentence": " ".join(words[:k] + words[k + 1:])}))
    out.append(("schema_missing_field", {"__drop__": "directness"}))
    out.append(("schema_strength_out_of_range", {"evidence_strength": "1.7"}))
    out.append(("whitespace_variant", {"supporting_sentence": s.replace(" ", "  ", 2).replace(", ", ",\n", 1)}))
    out.append(("nbsp_variant", {"supporting_sentence": s.replace(" ", " ", 3)}))
    if s.endswith("."): out.append(("trailing_period_removed", {"supporting_sentence": s[:-1]}))
    out.append(("case_variant", {"supporting_sentence": s[0].lower() + s[1:] if s[0].isupper() else s[0].upper() + s[1:]}))
    if "-" in s: out.append(("unicode_dash_quote_variant", {"supporting_sentence": s.replace("-", "–", 1)}))
    elif "'" in s: out.append(("unicode_dash_quote_variant", {"supporting_sentence": s.replace("'", "’", 1)}))
    if len(words) >= 10: out.append(("truncated_quote", {"supporting_sentence": " ".join(words[: max(6, int(len(words) * 0.6))])}))
    return out

EXPECT = {"wrong_pmid_in_corpus": "reject", "wrong_pmid_not_in_corpus": "reject", "sentence_from_other_pmid": "reject", "number_changed": "reject",
          "direction_word_changed": "reject", "sentence_composed_two_abstracts": "reject", "word_dropped": "reject", "schema_missing_field": "reject",
          "schema_strength_out_of_range": "reject", "whitespace_variant": "retain", "nbsp_variant": "retain", "trailing_period_removed": "retain",
          "case_variant": "surface", "unicode_dash_quote_variant": "surface", "truncated_quote": "surface"}
rows = []; agg = collections.defaultdict(lambda: collections.Counter())
for m, rid, kb in bases:
    for ft, change in faults(kb):
        v = dict(kb)
        if "__drop__" in change: v.pop(change["__drop__"])
        else: v.update(change)
        st = track_a(v); agg[ft]["n"] += 1; agg[ft]["pass"] += st["pass"]
        for k in ("schema_valid", "citation_valid", "sentence_present", "sentence_anchored"): agg[ft][f"fail_{k}"] += (not st[k])
        rows.append({"extractor": m, "record_id": rid, "pmid": kb["citation_id"], "fault_type": ft, "expected": EXPECT[ft], "track_a_pass": st["pass"],
                     **{k: st[k] for k in ("schema_valid", "citation_valid", "sentence_present", "sentence_anchored")}})
with open(OUT / "track_a_fault_rows.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
summ = {"n_base_rows": len(bases), "by_fault_type": {}}
lines = ["# Track-A controlled fault injection (production audit code; all Track-A-passing archived rows)", "", f"Base rows: {len(bases)}", "",
         "| Fault type | expected | n | rejected | retained | rejection rate % | retention rate % | failing check(s) |", "|---|---|---|---|---|---|---|---|"]
for ft in EXPECT:
    c = agg[ft]; n = c["n"]; rej = n - c["pass"]
    checks = ", ".join(f"{k.replace('fail_','')}={c[k]}" for k in ("fail_schema_valid", "fail_citation_valid", "fail_sentence_present", "fail_sentence_anchored") if c[k])
    summ["by_fault_type"][ft] = {"expected": EXPECT[ft], "n": n, "rejected": rej, "retained": c["pass"], "rejection_rate": round(100 * rej / n, 2) if n else None, "failing_checks": checks}
    lines.append(f"| {ft} | {EXPECT[ft]} | {n} | {rej} | {c['pass']} | {100*rej/n:.1f} | {100*c['pass']/n:.1f} | {checks} |")
sens = {ft: summ["by_fault_type"][ft]["rejection_rate"] for ft, e in EXPECT.items() if e == "reject"}
spec = {ft: 100 - summ["by_fault_type"][ft]["rejection_rate"] for ft, e in EXPECT.items() if e == "retain"}
summ["sensitivity_corruptions_pct"] = sens; summ["specificity_normalisation_variants_pct"] = spec
(OUT / "track_a_fault_injection_results.json").write_text(json.dumps(summ, indent=2))
(OUT / "track_a_fault_injection_results.md").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
