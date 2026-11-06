"""Đánh giá mô hình: (1) trích kỹ năng từ CV, (2) chất lượng xếp hạng gợi ý việc làm.

Chạy từ thư mục backend:  python -m evaluation.evaluate
Không cần CSDL. Kết quả in ra màn hình và ghi vào ../docs/ket_qua_danh_gia.md
"""

import math
import random
from pathlib import Path

from ai.cv_parser import parse_cv
from ai.matcher import (
    CandidateFeatures,
    JobFeatures,
    TextSimilarity,
    rank_jobs_for_candidate,
)
from ai.skill_extractor import SkillDictionary, SkillEntry
from ai.text_utils import jaccard
from constants import DEFAULT_MATCH_WEIGHTS
from evaluation.dataset import CANDIDATES, JOBS
from scripts.seed_data import SKILLS

K_VALUES = (1, 3, 5)
NDCG_K = 5
RANDOM_TRIALS = 200
OUTPUT_PATH = Path(__file__).resolve().parents[2] / "docs" / "ket_qua_danh_gia.md"


def build_dictionary() -> SkillDictionary:
    return SkillDictionary(
        [SkillEntry(i, name, cat, tuple(aliases)) for i, (name, cat, aliases) in
         enumerate(SKILLS, start=1)]
    )


# ---------- Trích xuất kỹ năng ----------

def evaluate_extraction(dictionary: SkillDictionary) -> tuple[dict, list[dict]]:
    tp = fp = fn = 0
    rows = []
    for cand in CANDIDATES:
        found = {s.name for s in parse_cv(cand["cv"], dictionary).skills}
        expected = set(cand["expected_skills"])
        c_tp, c_fp, c_fn = len(found & expected), len(found - expected), len(expected - found)
        tp, fp, fn = tp + c_tp, fp + c_fp, fn + c_fn
        rows.append({"id": cand["id"], "precision": c_tp / max(1, c_tp + c_fp),
                     "recall": c_tp / max(1, c_tp + c_fn),
                     "missed": sorted(expected - found), "extra": sorted(found - expected)})
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-9, precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1}, rows


# ---------- Xếp hạng ----------

def precision_at_k(ranked: list[int], relevant: dict[int, int], k: int) -> float:
    return sum(1 for j in ranked[:k] if relevant.get(j, 0) > 0) / k


def recall_at_k(ranked: list[int], relevant: dict[int, int], k: int) -> float:
    total = sum(1 for g in relevant.values() if g > 0)
    return sum(1 for j in ranked[:k] if relevant.get(j, 0) > 0) / max(1, total)


def ndcg_at_k(ranked: list[int], relevant: dict[int, int], k: int) -> float:
    dcg = sum((2 ** relevant.get(j, 0) - 1) / math.log2(i + 2) for i, j in enumerate(ranked[:k]))
    ideal = sorted(relevant.values(), reverse=True)[:k]
    idcg = sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def reciprocal_rank(ranked: list[int], relevant: dict[int, int]) -> float:
    for i, j in enumerate(ranked, start=1):
        if relevant.get(j, 0) > 0:
            return 1 / i
    return 0.0


def _metrics(ranked: list[int], relevant: dict[int, int]) -> dict[str, float]:
    metrics = {f"P@{k}": precision_at_k(ranked, relevant, k) for k in K_VALUES}
    metrics["R@5"] = recall_at_k(ranked, relevant, 5)
    metrics[f"NDCG@{NDCG_K}"] = ndcg_at_k(ranked, relevant, NDCG_K)
    metrics["MRR"] = reciprocal_rank(ranked, relevant)
    return metrics


def _average(rows: list[dict[str, float]]) -> dict[str, float]:
    return {key: sum(r[key] for r in rows) / len(rows) for key in rows[0]}


def evaluate_ranking(dictionary: SkillDictionary) -> dict[str, dict[str, float]]:
    ids = {entry.name: sid for sid, entry in dictionary.entries.items()}
    jobs = [
        JobFeatures(
            job_id=j["id"], title=j["title"], text=j["description"],
            required_skill_ids={ids[s] for s in j["required"]},
            optional_skill_ids={ids[s] for s in j["optional"]},
            min_years_experience=j["years"], location=j["location"], work_type=j["work_type"],
        )
        for j in JOBS
    ]
    rng = random.Random(0)
    methods: dict[str, list[dict[str, float]]] = {
        "Ngẫu nhiên": [], "Jaccard kỹ năng": [], "TF-IDF văn bản": [],
        "Chỉ đặc trưng kỹ năng": [], "Hybrid (đề xuất)": [],
    }
    skill_only = {name: (1.0 if name == "skill" else 0.0) for name in DEFAULT_MATCH_WEIGHTS}
    for cand in CANDIDATES:
        # Kỹ năng lấy từ CV qua bộ trích xuất (đánh giá đầu-cuối, không dùng nhãn kỹ năng)
        parsed = parse_cv(cand["cv"], dictionary)
        candidate = CandidateFeatures(
            candidate_id=cand["id"], skill_ids={s.skill_id for s in parsed.skills},
            text=f"{cand['target']} {cand['cv']}", years_experience=cand["years"],
            location=cand["location"], work_types=cand["work_types"],
            target_position=cand["target"],
        )
        relevant = cand["relevance"]

        random_rows = []
        for _ in range(RANDOM_TRIALS):
            order = [j.job_id for j in jobs]
            rng.shuffle(order)
            random_rows.append(_metrics(order, relevant))
        methods["Ngẫu nhiên"].append(_average(random_rows))

        by_jaccard = sorted(
            jobs, key=lambda j: -jaccard(
                {str(s) for s in candidate.skill_ids},
                {str(s) for s in j.required_skill_ids | j.optional_skill_ids},
            ),
        )
        methods["Jaccard kỹ năng"].append(_metrics([j.job_id for j in by_jaccard], relevant))

        sim = TextSimilarity([candidate.text, *(f"{j.title} {j.text}" for j in jobs)])
        scores = sim.similarity_to_all(0, list(range(1, len(jobs) + 1)))
        by_tfidf = [j.job_id for _, j in sorted(zip(scores, jobs, strict=True),
                                                key=lambda x: -x[0])]
        methods["TF-IDF văn bản"].append(_metrics(by_tfidf, relevant))

        ranked_skill = rank_jobs_for_candidate(candidate, jobs, weights=skill_only)
        methods["Chỉ đặc trưng kỹ năng"].append(
            _metrics([r.job_id for r in ranked_skill], relevant)
        )
        ranked = rank_jobs_for_candidate(candidate, jobs, weights=DEFAULT_MATCH_WEIGHTS)
        methods["Hybrid (đề xuất)"].append(_metrics([r.job_id for r in ranked], relevant))
    return {name: _average(rows) for name, rows in methods.items()}


def _fmt(value: float) -> str:
    return f"{value:.3f}"


def write_report(extraction: dict, extraction_rows: list[dict],
                 ranking: dict[str, dict[str, float]]) -> str:
    metric_names = list(next(iter(ranking.values())))
    lines = [
        "# Kết quả đánh giá mô hình",
        "",
        "_Tệp này được sinh tự động bởi `python -m evaluation.evaluate`._",
        "",
        f"Tập đánh giá: {len(CANDIDATES)} CV, {len(JOBS)} tin tuyển dụng, nhãn gán thủ công.",
        "",
        "## 1. Trích xuất kỹ năng từ CV",
        "",
        "| Precision | Recall | F1 |",
        "|---|---|---|",
        f"| {_fmt(extraction['precision'])} | {_fmt(extraction['recall'])} | "
        f"{_fmt(extraction['f1'])} |",
        "",
        "| CV | Precision | Recall | Bỏ sót | Thừa |",
        "|---|---|---|---|---|",
    ]
    for r in extraction_rows:
        lines.append(f"| {r['id']} | {_fmt(r['precision'])} | {_fmt(r['recall'])} | "
                     f"{', '.join(r['missed']) or '-'} | {', '.join(r['extra']) or '-'} |")
    lines += [
        "",
        "## 2. Xếp hạng gợi ý việc làm",
        "",
        "| Phương pháp | " + " | ".join(metric_names) + " |",
        "|---|" + "---|" * len(metric_names),
    ]
    for name, metrics in ranking.items():
        lines.append(f"| {name} | " + " | ".join(_fmt(metrics[m]) for m in metric_names) + " |")
    report = "\n".join(lines) + "\n"
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    return report


def main() -> None:
    dictionary = build_dictionary()
    extraction, rows = evaluate_extraction(dictionary)
    ranking = evaluate_ranking(dictionary)
    print(write_report(extraction, rows, ranking))
    print(f"Đã ghi báo cáo: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
