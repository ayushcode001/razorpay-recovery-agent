"""
Contextual Bandit for Dynamic Retry Timing Optimization (Offline Simulation).

Answers the decision question:
"What retry cooldown timing maximizes P(recovery) for each specific failure category?"

Explicit Scope Limit:
This is a self-contained offline simulated demonstration of reinforcement learning /
multi-armed bandits in revenue recovery. It is NOT wired into the live synchronous webhook.

Setup:
  - Discrete timing action arms:
      0: 1 minute    (Immediate / Transient Hiccup)
      1: 15 minutes  (Gateway Recovery Backoff)
      2: 1 hour      (Customer Re-prompt Window)
      3: 6 hours     (Alternative Payment Setup)
      4: 24 hours    (Next-Day / Salary-Credit Timing)

  - Ground-Truth Optimal Delay Profiles (Bake-in physics of payment failure modes):
      - insufficient_funds / retry_later:  peaks at 24 hours (funds credited)
      - smart_retry (timeouts / gateway):   peaks at 15 minutes (network resolved)
      - change_method:                     peaks at 6 hours (instrument swap)
      - user_error (CVV / OTP):            peaks at 1 hour (customer attention)

  - Algorithm: Thompson Sampling Bandit with Beta(alpha, beta) conjugate priors.
  - Evaluation: Evaluates cumulative reward vs Fixed-Delay Baseline (e.g. static 1-min retry).
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_CHART_PATH = os.path.join(PROJECT_ROOT, "bandit_convergence.png")

# Cooldown Action Arms (in minutes)
ARMS = [
    {"index": 0, "name": "1 min", "minutes": 1, "desc": "Immediate Retry"},
    {"index": 1, "name": "15 min", "minutes": 15, "desc": "Gateway Backoff"},
    {"index": 2, "name": "1 hour", "minutes": 60, "desc": "Customer Re-prompt"},
    {"index": 3, "name": "6 hours", "minutes": 360, "desc": "Method Switch Window"},
    {"index": 4, "name": "24 hours", "minutes": 1440, "desc": "Salary/Daily Cooldown"},
]

# Ground-truth success probability matrix P(success | Category, Arm)
# Used by the environment simulator to generate Bernoulli recovery outcomes
GROUND_TRUTH_REWARD_DIST = {
    "retry_later": {
        0: 0.15,  # 1 min (funds don't magically appear in 1 min)
        1: 0.22,  # 15 min
        2: 0.35,  # 1 hr
        3: 0.52,  # 6 hr
        4: 0.78,  # 24 hr (OPTIMAL: daily balance credit / payroll)
    },
    "smart_retry": {
        0: 0.45,  # 1 min
        1: 0.82,  # 15 min (OPTIMAL: bank gateway latency clears)
        2: 0.65,  # 1 hr (unnecessarily long wait loses customer momentum)
        3: 0.48,  # 6 hr
        4: 0.30,  # 24 hr
    },
    "change_method": {
        0: 0.10,  # 1 min (customer hasn't fetched new card)
        1: 0.35,  # 15 min
        2: 0.60,  # 1 hr
        3: 0.76,  # 6 hr (OPTIMAL: customer finds replacement card/UPI)
        4: 0.55,  # 24 hr (drop-off from delayed intent)
    },
    "user_error": {
        0: 0.25,  # 1 min (customer irritated if spammed instantly)
        1: 0.50,  # 15 min
        2: 0.74,  # 1 hr (OPTIMAL: calm re-prompt notification)
        3: 0.55,  # 6 hr
        4: 0.38,  # 24 hr
    },
}

CATEGORIES = ["retry_later", "smart_retry", "change_method", "user_error"]
OPTIMAL_ARM_INDEX = {
    "retry_later": 4,   # 24h
    "smart_retry": 1,   # 15m
    "change_method": 3, # 6h
    "user_error": 2,    # 1h
}


class ThompsonSamplingBandit:
    """
    Beta-Bernoulli Thompson Sampling Agent.
    Maintains Alpha (successes + 1) and Beta (failures + 1) for each arm.
    """

    def __init__(self, n_arms: int = 5):
        self.n_arms = n_arms
        self.alphas = np.ones(n_arms)
        self.betas = np.ones(n_arms)
        self.pull_counts = np.zeros(n_arms, dtype=int)
        self.rewards_history = []
        self.chosen_arms_history = []

    def select_arm(self) -> int:
        # Sample from posterior Beta distribution for each arm
        samples = np.random.beta(self.alphas, self.betas)
        return int(np.argmax(samples))

    def update(self, arm: int, reward: int):
        self.pull_counts[arm] += 1
        if reward == 1:
            self.alphas[arm] += 1
        else:
            self.betas[arm] += 1
        self.chosen_arms_history.append(arm)
        self.rewards_history.append(reward)

    def get_estimated_probs(self) -> np.ndarray:
        return self.alphas / (self.alphas + self.betas)


def simulate_environment_reward(category: str, arm: int) -> int:
    true_p = GROUND_TRUTH_REWARD_DIST[category][arm]
    return 1 if np.random.random() < true_p else 0


def run_bandit_simulation(n_episodes: int = 5000, seed: int = 42):
    np.random.seed(seed)
    results = {}

    for category in CATEGORIES:
        bandit = ThompsonSamplingBandit(n_arms=len(ARMS))
        
        # Baselines for comparison:
        # Baseline 1: Fixed naive 1-minute immediate cooldown (Arm 0)
        # Baseline 2: Random arm selection
        baseline_fixed_rewards = []
        baseline_random_rewards = []

        bandit_cum_rewards = []
        fixed_cum_rewards = []
        random_cum_rewards = []

        bandit_cum = 0
        fixed_cum = 0
        random_cum = 0

        for ep in range(n_episodes):
            # 1. Bandit choice
            chosen_arm = bandit.select_arm()
            reward = simulate_environment_reward(category, chosen_arm)
            bandit.update(chosen_arm, reward)
            bandit_cum += reward
            bandit_cum_rewards.append(bandit_cum)

            # 2. Fixed baseline (always Arm 0: 1 min)
            fixed_reward = simulate_environment_reward(category, 0)
            fixed_cum += fixed_reward
            fixed_cum_rewards.append(fixed_cum)

            # 3. Random baseline
            rand_arm = np.random.choice(len(ARMS))
            rand_reward = simulate_environment_reward(category, rand_arm)
            random_cum += rand_reward
            random_cum_rewards.append(random_cum)

        # Check convergence in last 1000 episodes
        last_1000_arms = bandit.chosen_arms_history[-1000:]
        most_chosen_arm = int(np.bincount(last_1000_arms).argmax())
        optimal_arm = OPTIMAL_ARM_INDEX[category]
        converged = (most_chosen_arm == optimal_arm)
        optimal_pull_rate = (np.array(last_1000_arms) == optimal_arm).mean()

        results[category] = {
            "bandit": bandit,
            "bandit_cum_rewards": bandit_cum_rewards,
            "fixed_cum_rewards": fixed_cum_rewards,
            "random_cum_rewards": random_cum_rewards,
            "total_bandit_recoveries": bandit_cum,
            "total_fixed_recoveries": fixed_cum,
            "total_random_recoveries": random_cum,
            "net_gain_over_fixed": bandit_cum - fixed_cum,
            "percentage_gain": ((bandit_cum - fixed_cum) / fixed_cum) if fixed_cum else 0,
            "optimal_arm": optimal_arm,
            "most_chosen_arm": most_chosen_arm,
            "converged": converged,
            "final_optimal_pull_rate": optimal_pull_rate,
            "estimated_probs": bandit.get_estimated_probs().tolist(),
        }

    return results


def plot_bandit_results(results: dict, out_path: str = OUTPUT_CHART_PATH):
    plt.style.use("dark_background")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=150)
    fig.patch.set_facecolor('#090d16')

    palette = {
        "retry_later": "#3b82f6",
        "smart_retry": "#10b981",
        "change_method": "#8b5cf6",
        "user_error": "#f59e0b",
    }

    category_titles = {
        "retry_later": "Insufficient Funds (retry_later) -> Optimal: 24h Cooldown",
        "smart_retry": "Network / Bank Timeout (smart_retry) -> Optimal: 15m Backoff",
        "change_method": "Card Expired / Blocked (change_method) -> Optimal: 6h Window",
        "user_error": "Incorrect CVV / OTP (user_error) -> Optimal: 1h Nudge",
    }

    for idx, category in enumerate(CATEGORIES):
        ax = axes[idx // 2, idx % 2]
        ax.set_facecolor('#111827')
        
        data = results[category]
        episodes = np.arange(1, len(data["bandit_cum_rewards"]) + 1)

        ax.plot(episodes, data["bandit_cum_rewards"], label="Thompson Sampling Bandit", color=palette[category], linewidth=2.4)
        ax.plot(episodes, data["fixed_cum_rewards"], label="Fixed Cooldown Baseline (1m)", color="#94a3b8", linestyle="--", linewidth=1.8)
        ax.plot(episodes, data["random_cum_rewards"], label="Random Policy Baseline", color="#64748b", linestyle=":", linewidth=1.4)

        opt_name = ARMS[data["optimal_arm"]]["name"]
        ax.set_title(category_titles[category], fontsize=11, fontweight="bold", pad=10, color="#f3f4f6")
        ax.set_xlabel("Simulation Episode", fontsize=9, color="#9ca3af")
        ax.set_ylabel("Cumulative Recoveries", fontsize=9, color="#9ca3af")
        ax.grid(True, linestyle="--", alpha=0.15, color="#ffffff")
        ax.legend(loc="upper left", fontsize=8, framealpha=0.3)

        # Annotate final outcome
        gain = data["percentage_gain"]
        final_rate = data["final_optimal_pull_rate"]
        ax.text(
            0.97, 0.08,
            f"Converged to: {opt_name}\nOptimal arm pick rate: {final_rate:.1%}\nLift vs Fixed: +{gain:.1%}",
            transform=ax.transAxes,
            fontsize=8,
            ha="right",
            va="bottom",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#1e293b", edgecolor=palette[category], alpha=0.9),
            color="#f3f4f6"
        )

    plt.suptitle("Razorpay Recovery Agent — Contextual Bandit for Dynamic Retry Timing", fontsize=14, fontweight="bold", y=0.98, color="#60a5fa")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"[Bandit] Convergence comparison chart saved to: {out_path}")


if __name__ == "__main__":
    n_episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print(f"Running Thompson Sampling Retry-Timing Bandit simulation ({n_episodes} episodes)...")
    results = run_bandit_simulation(n_episodes=n_episodes)

    print("\n=== BANDIT SIMULATION SUMMARY (5,000 Episodes per Category) ===")
    print(f"{'Category':<16} {'Optimal Arm':<14} {'Selected Arm':<14} {'Final Pull Rate':<18} {'Lift vs Fixed Baseline':<20}")
    
    all_converged = True
    for cat in CATEGORIES:
        r = results[cat]
        opt_str = f"Arm {r['optimal_arm']} ({ARMS[r['optimal_arm']]['name']})"
        sel_str = f"Arm {r['most_chosen_arm']} ({ARMS[r['most_chosen_arm']]['name']})"
        pull_str = f"{r['final_optimal_pull_rate']:.1%}"
        lift_str = f"+{r['percentage_gain']:.1%} (+{r['net_gain_over_fixed']} recoveries)"
        print(f"{cat:<16} {opt_str:<14} {sel_str:<14} {pull_str:<18} {lift_str:<20}")
        if not r["converged"]:
            all_converged = False

    print(f"\nGround Truth Convergence Verification: {'PASSED (100% categories converged to true optimal timing)' if all_converged else 'FAILED'}")
    plot_bandit_results(results)
