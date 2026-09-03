import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent.cohort_analyst import analyze_cohorts
from agent.retry_bandit import run_bandit_simulation, ARMS, CATEGORIES

print("Generating cohort analyst fallback data...")
cohort_res = analyze_cohorts()
cohort_df = cohort_res["df"]
scatter_by_cluster = {}
for c in cohort_res["cohorts"]:
    cid = c["cluster_id"]
    c_sub = cohort_df[cohort_df["cluster"] == cid][["pca_x", "pca_y", "amount", "method"]]
    scatter_by_cluster[str(cid)] = c_sub.head(300).to_dict(orient="records")

cohort_payload = {
    "status": "ok",
    "cohorts": cohort_res["cohorts"],
    "scatter_by_cluster": scatter_by_cluster,
    "pca_variance_ratio": cohort_res["pca_variance_ratio"],
    "total_at_risk": cohort_res["total_at_risk"],
    "non_trivial_passed": cohort_res["non_trivial_passed"],
}

print("Generating bandit simulation fallback data...")
bandit_res = run_bandit_simulation(n_episodes=1000, seed=42)
bandit_serializable = {}
for cat in CATEGORIES:
    r = bandit_res[cat]
    bandit_serializable[cat] = {
        "bandit_cum_rewards": r["bandit_cum_rewards"],
        "fixed_cum_rewards": r["fixed_cum_rewards"],
        "taxonomy_cum_rewards": r["taxonomy_cum_rewards"],
        "random_cum_rewards": r["random_cum_rewards"],
        "optimal_arm": r["optimal_arm"],
        "most_chosen_arm": r["most_chosen_arm"],
        "final_optimal_pull_rate": r["final_optimal_pull_rate"],
        "percentage_gain_vs_fixed": r["percentage_gain_vs_fixed"],
        "percentage_gain_vs_taxonomy": r["percentage_gain_vs_taxonomy"],
        "taxonomy_default_arm": r["taxonomy_default_arm"],
        "converged": r["converged"],
    }

bandit_payload = {
    "status": "ok",
    "categories": CATEGORIES,
    "arms": ARMS,
    "results": bandit_serializable,
}

out_path = os.path.join(PROJECT_ROOT, "frontend", "src", "data", "fallbackStats.ts")
os.makedirs(os.path.dirname(out_path), exist_ok=True)

with open(out_path, "w", encoding="utf-8") as f:
    f.write("// Pre-computed statistical benchmarks from ML model runs.\n")
    f.write("// Used as initial/fallback data so charts and stats immediately render without waiting for backend.\n\n")
    f.write("export const FALLBACK_COHORT_DATA = ")
    json.dump(cohort_payload, f, indent=2)
    f.write(" as const\n\n")
    f.write("export const FALLBACK_BANDIT_DATA = ")
    json.dump(bandit_payload, f, indent=2)
    f.write(" as const\n")

print(f"Successfully wrote fallback stats to {out_path}")
