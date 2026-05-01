
"""
QuestBridge vs. Deferred Acceptance Simulation

Purpose:
This simulation compares a simplified QuestBridge-style matching mechanism
against a student-proposing Deferred Acceptance (DA) mechanism.

The model is calibrated using publicly available QuestBridge statistics:
- QuestBridge finalists are modeled as high-achieving, low-income students.
- The simulated pool uses 300 finalists.
- The simulated capacity is scaled to approximate the 2024 finalist match rate.
- The QuestBridge-style mechanism uses strategic submitted rankings, while DA
  uses students' true preferences.

Important modeling note:
This is not meant to reproduce the exact QuestBridge algorithm. Rather, it is a
controlled simulation that isolates one key market design question:
How do outcomes differ when students can report true preferences under DA versus
when they may strategically rank safer colleges under a QB-style process?
"""

import numpy as np
import pandas as pd
import random
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# 1. REPRODUCIBILITY
# ============================================================
# Setting the seed makes the random simulation reproducible.
# Anyone who runs the code should get the same results.
np.random.seed(136)
random.seed(136)

# ============================================================
# 2. SIMULATION SETTINGS
# ============================================================
# The simulation uses 300 students, representing QuestBridge finalists.
NUM_STUDENTS = 300

# QuestBridge allows finalists to rank up to 15 colleges.
# Therefore, the model uses 15 colleges as each student's effective ranking set.
NUM_COLLEGES = 15

college_names = [f"College_{i}" for i in range(1, NUM_COLLEGES + 1)]

# Colleges are grouped into three broad selectivity tiers.
college_tiers = (
    ["Most Selective"] * 5 +
    ["Middle Selective"] * 5 +
    ["Less Selective"] * 5
)

# The 2024 QuestBridge match rate among finalists is approximately:
# 2,627 matched finalists / 7,288 finalists ≈ 36%.
# Scaling this to 300 simulated finalists gives about 108-112 seats.
# I use 112 seats, or a 37.3% simulated capacity rate.
capacities = [8] * 7 + [7] * 8
college_capacity = dict(zip(college_names, capacities))

colleges_df = pd.DataFrame({
    "college": college_names,
    "tier": college_tiers,
    "capacity": capacities
})

TOTAL_SEATS = sum(capacities)

# ============================================================
# 3. GENERATE QUESTBRIDGE-INFORMED STUDENT DATA
# ============================================================
# Students are not modeled as generic applicants.
# They are modeled as QuestBridge finalists: strong GPA, strong coursework,
# low-income background, and high involvement outside the classroom.

students = []

for i in range(NUM_STUDENTS):

    # The three groups represent variation within the finalist pool,
    # not "qualified" versus "unqualified" students.
    if i < 100:
        group = "Highest Academic Finalists"
        gpa = np.random.normal(3.97, 0.04)
        sat = np.random.normal(1490, 45)
        essay = np.random.normal(9.0, 0.5)
    elif i < 200:
        group = "Middle Academic Finalists"
        gpa = np.random.normal(3.90, 0.07)
        sat = np.random.normal(1375, 65)
        essay = np.random.normal(8.4, 0.7)
    else:
        group = "Context-Strong Finalists"
        gpa = np.random.normal(3.82, 0.10)
        sat = np.random.normal(1305, 70)
        essay = np.random.normal(8.0, 0.8)

    # Keep generated values within realistic bounds.
    gpa = np.clip(gpa, 3.4, 4.0)
    sat = np.clip(sat, 1050, 1600)
    essay = np.clip(essay, 1, 10)

    # Context variables are based on QuestBridge finalist profile statistics.
    household_under_65k = np.random.binomial(1, 0.89)
    free_reduced_lunch = np.random.binomial(1, 0.86)
    first_generation = np.random.binomial(1, 0.80)
    leadership = np.random.binomial(1, 0.91)
    paid_job = np.random.binomial(1, 0.66)
    home_responsibilities = np.random.binomial(1, 0.75)
    volunteering = np.random.binomial(1, 0.60)

    # Context score summarizes non-academic factors colleges may value
    # in a holistic review process.
    context_score = (
        1.4 * household_under_65k +
        1.2 * free_reduced_lunch +
        1.0 * first_generation +
        0.8 * leadership +
        0.7 * paid_job +
        0.7 * home_responsibilities +
        0.6 * volunteering +
        np.random.normal(0, 0.4)
    )

    context_score = np.clip((context_score / 6.4) * 10, 1, 10)

    students.append({
        "student_id": f"S{i+1}",
        "group": group,
        "gpa": round(gpa, 2),
        "sat": round(sat),
        "essay": round(essay, 2),
        "household_under_65k": household_under_65k,
        "free_reduced_lunch": free_reduced_lunch,
        "first_generation": first_generation,
        "leadership": leadership,
        "paid_job": paid_job,
        "home_responsibilities": home_responsibilities,
        "volunteering": volunteering,
        "context_score": round(context_score, 2)
    })

students_df = pd.DataFrame(students)

# ============================================================
# 4. GENERATE STUDENTS' TRUE PREFERENCES
# ============================================================
# True preferences represent where students would prefer to attend if they
# could rank honestly without worrying about strategic consequences.

def generate_true_preferences(group):
    most_selective = college_names[:5]
    middle_selective = college_names[5:10]
    less_selective = college_names[10:15]

    # All finalists are ambitious, but stronger academic finalists are modeled
    # as somewhat more likely to prefer the most selective schools.
    if group == "Highest Academic Finalists":
        weighted_list = most_selective * 6 + middle_selective * 3 + less_selective * 1
    elif group == "Middle Academic Finalists":
        weighted_list = most_selective * 4 + middle_selective * 4 + less_selective * 2
    else:
        weighted_list = most_selective * 3 + middle_selective * 4 + less_selective * 3

    ranking = []
    while len(ranking) < NUM_COLLEGES:
        choice = random.choice(weighted_list)
        if choice not in ranking:
            ranking.append(choice)

    return ranking

true_student_preferences = {
    row["student_id"]: generate_true_preferences(row["group"])
    for _, row in students_df.iterrows()
}

# ============================================================
# 5. GENERATE COLLEGE PREFERENCES
# ============================================================
# Colleges rank students using a simplified holistic score.
# More selective colleges place more weight on GPA/SAT, while less selective
# colleges place more relative weight on essays and contextual strength.

college_preferences = {}

for college, tier in zip(college_names, college_tiers):
    ranked_students = students_df.copy()

    if tier == "Most Selective":
        ranked_students["college_score"] = (
            0.35 * ranked_students["gpa"] * 400 +
            0.30 * ranked_students["sat"] +
            0.20 * ranked_students["essay"] * 160 +
            0.15 * ranked_students["context_score"] * 160
        )
    elif tier == "Middle Selective":
        ranked_students["college_score"] = (
            0.28 * ranked_students["gpa"] * 400 +
            0.25 * ranked_students["sat"] +
            0.25 * ranked_students["essay"] * 160 +
            0.22 * ranked_students["context_score"] * 160
        )
    else:
        ranked_students["college_score"] = (
            0.22 * ranked_students["gpa"] * 400 +
            0.20 * ranked_students["sat"] +
            0.25 * ranked_students["essay"] * 160 +
            0.33 * ranked_students["context_score"] * 160
        )

    # Add idiosyncratic admissions variation.
    # This prevents all colleges within a tier from having identical rankings.
    ranked_students["college_score"] += np.random.normal(0, 25, NUM_STUDENTS)

    ranked_students = ranked_students.sort_values("college_score", ascending=False)
    college_preferences[college] = list(ranked_students["student_id"])

# Convert each college's ranking list into a lookup dictionary.
# Lower rank number means the college prefers that student more.
college_rankings = {
    college: {student: rank for rank, student in enumerate(pref_list)}
    for college, pref_list in college_preferences.items()
}

# ============================================================
# 6. DEFERRED ACCEPTANCE MECHANISM
# ============================================================
# Student-proposing DA:
# - Students apply to their true favorite remaining college.
# - Colleges temporarily hold their favorite applicants up to capacity.
# - Rejected students continue proposing.
# - This continues until no student wants to make another proposal.

def run_deferred_acceptance(student_preferences):
    free_students = list(students_df["student_id"])
    next_proposal_index = {student: 0 for student in free_students}
    current_matches = {college: [] for college in college_names}

    while free_students:
        student = free_students.pop(0)

        # If the student has proposed to all colleges, they remain unmatched.
        if next_proposal_index[student] >= NUM_COLLEGES:
            continue

        college = student_preferences[student][next_proposal_index[student]]
        next_proposal_index[student] += 1

        # Student proposes to the next college.
        current_matches[college].append(student)

        # College keeps its most preferred students up to capacity.
        current_matches[college].sort(key=lambda s: college_rankings[college][s])

        if len(current_matches[college]) > college_capacity[college]:
            rejected_student = current_matches[college].pop()

            # Rejected student can propose again later.
            if next_proposal_index[rejected_student] < NUM_COLLEGES:
                free_students.append(rejected_student)

    matches = []

    for college, matched_students in current_matches.items():
        for student in matched_students:
            true_rank = true_student_preferences[student].index(college) + 1
            matches.append({
                "student_id": student,
                "matched_college": college,
                "true_choice_rank": true_rank
            })

    return pd.DataFrame(matches)

# ============================================================
# 7. QUESTBRIDGE-STYLE SUBMITTED PREFERENCES
# ============================================================
# Under the QB-style model, students may not rank exactly according to true
# preferences. Instead, some students move "safer" schools upward because the
# real Match is binding and students care about maximizing match probability.

def make_qb_strategic_preferences(student_id, group):
    true_ranking = true_student_preferences[student_id].copy()

    most_selective = college_names[:5]
    middle_selective = college_names[5:10]
    less_selective = college_names[10:15]

    if group == "Highest Academic Finalists":
        # Strongest students are modeled as most likely to rank truthfully.
        strategic_ranking = true_ranking
    elif group == "Middle Academic Finalists":
        # Middle finalists move some middle/less selective options upward.
        safer = [c for c in true_ranking if c in middle_selective + less_selective]
        reaches = [c for c in true_ranking if c in most_selective]
        strategic_ranking = safer[:7] + reaches + safer[7:]
    else:
        # Context-strong finalists are modeled as most likely to rank safer schools higher.
        less = [c for c in true_ranking if c in less_selective]
        middle = [c for c in true_ranking if c in middle_selective]
        most = [c for c in true_ranking if c in most_selective]
        strategic_ranking = less[:4] + middle + most + less[4:]

    # Students do not always rank all 15 colleges.
    # This approximates QuestBridge's statistic that Match Scholarship Recipients
    # rank 10 colleges on average, with 76% ranking 7 or more.
    list_length = int(np.clip(round(np.random.normal(10, 2.5)), 4, 15))
    return strategic_ranking[:list_length]

qb_student_preferences = {
    row["student_id"]: make_qb_strategic_preferences(row["student_id"], row["group"])
    for _, row in students_df.iterrows()
}

# ============================================================
# 8. QUESTBRIDGE-STYLE MATCHING MECHANISM
# ============================================================
# This approximates QB by using:
# - submitted rankings that may differ from true preferences,
# - college acceptable pools rather than full preference lists,
# - assignment to the highest-ranked submitted college that can match.
#
# This is intentionally simplified. It captures the strategic ranking pressure
# but does not claim to replicate every institutional rule of QuestBridge.

def run_qb_style_match(qb_preferences):
    current_matches = {college: [] for college in college_names}
    students_in_process = list(students_df["student_id"])

    # Acceptable pools are set large enough for colleges to fill seats,
    # but small enough that not every student is admissible everywhere.
    acceptable_cutoff = {
        "Most Selective": 45,
        "Middle Selective": 80,
        "Less Selective": 120
    }

    acceptable_students = {}

    for college, tier in zip(college_names, college_tiers):
        cutoff = acceptable_cutoff[tier]
        acceptable_students[college] = set(college_preferences[college][:cutoff])

    # Processing order represents uncertainty in a simplified admit/match process.
    random.shuffle(students_in_process)

    for student in students_in_process:
        for college in qb_preferences[student]:

            # Student can only match to a college if the college finds them acceptable.
            if student in acceptable_students[college]:

                # If the college still has space, accept the student.
                if len(current_matches[college]) < college_capacity[college]:
                    current_matches[college].append(student)
                    break

                # If full, the college compares the new student with current matches.
                temporary_pool = current_matches[college] + [student]
                temporary_pool.sort(key=lambda s: college_rankings[college][s])
                kept = temporary_pool[:college_capacity[college]]

                if student in kept:
                    current_matches[college] = kept

                break

    matches = []

    for college, matched_students in current_matches.items():
        for student in matched_students:
            true_rank = true_student_preferences[student].index(college) + 1
            submitted_rank = qb_preferences[student].index(college) + 1
            matches.append({
                "student_id": student,
                "matched_college": college,
                "true_choice_rank": true_rank,
                "submitted_choice_rank": submitted_rank
            })

    return pd.DataFrame(matches)

# ============================================================
# 9. RUN BOTH MECHANISMS
# ============================================================

da_matches = run_deferred_acceptance(true_student_preferences)
qb_matches = run_qb_style_match(qb_student_preferences)

def build_results(matches_df, mechanism_name):
    results = students_df.merge(matches_df, on="student_id", how="left")
    results["matched"] = results["matched_college"].notna()
    results["mechanism"] = mechanism_name

    results = results.merge(
        colleges_df[["college", "tier"]],
        left_on="matched_college",
        right_on="college",
        how="left"
    ).drop(columns=["college"])

    return results

da_results = build_results(da_matches, "Deferred Acceptance")
qb_results = build_results(qb_matches, "QuestBridge-style")

combined_results = pd.concat([da_results, qb_results], ignore_index=True)

# ============================================================
# 10. SUMMARY STATISTICS
# ============================================================

summary = (
    combined_results
    .groupby("mechanism")
    .agg(
        total_students=("student_id", "count"),
        matched_students=("matched", "sum"),
        match_rate=("matched", "mean"),
        avg_true_choice_rank=("true_choice_rank", "mean"),
        first_choice_matches=("true_choice_rank", lambda x: (x == 1).sum()),
        top_three_matches=("true_choice_rank", lambda x: (x <= 3).sum()),
        top_five_matches=("true_choice_rank", lambda x: (x <= 5).sum())
    )
    .reset_index()
)

summary["match_rate_pct"] = (summary["match_rate"] * 100).round(1)
summary["avg_true_choice_rank"] = summary["avg_true_choice_rank"].round(2)
summary["first_choice_rate_among_matched"] = (
    summary["first_choice_matches"] / summary["matched_students"] * 100
).round(1)
summary["top_three_rate_among_matched"] = (
    summary["top_three_matches"] / summary["matched_students"] * 100
).round(1)
summary["top_five_rate_among_matched"] = (
    summary["top_five_matches"] / summary["matched_students"] * 100
).round(1)

group_summary = (
    combined_results
    .groupby(["mechanism", "group"])
    .agg(
        students=("student_id", "count"),
        matched_students=("matched", "sum"),
        match_rate=("matched", "mean"),
        avg_true_choice_rank=("true_choice_rank", "mean")
    )
    .reset_index()
)

group_summary["match_rate_pct"] = (group_summary["match_rate"] * 100).round(1)
group_summary["avg_true_choice_rank"] = group_summary["avg_true_choice_rank"].round(2)

choice_rank_summary = (
    combined_results[combined_results["matched"]]
    .groupby(["mechanism", "true_choice_rank"])
    .size()
    .reset_index(name="number_of_students")
)

choice_rank_summary["percent_of_matched"] = (
    choice_rank_summary.groupby("mechanism")["number_of_students"]
    .transform(lambda x: x / x.sum() * 100)
).round(1)

# Compare submitted versus true ranks for QB only.
qb_rank_distortion = qb_results[qb_results["matched"]].copy()
qb_rank_distortion["rank_distortion"] = (
    qb_rank_distortion["true_choice_rank"] - qb_rank_distortion["submitted_choice_rank"]
)

qb_distortion_summary = pd.DataFrame({
    "metric": [
        "Average true rank among QB matched students",
        "Average submitted rank among QB matched students",
        "Average rank distortion (true rank - submitted rank)",
        "Share of QB matches where submitted rank is better than true rank"
    ],
    "value": [
        round(qb_rank_distortion["true_choice_rank"].mean(), 2),
        round(qb_rank_distortion["submitted_choice_rank"].mean(), 2),
        round(qb_rank_distortion["rank_distortion"].mean(), 2),
        f"{(qb_rank_distortion['rank_distortion'] > 0).mean() * 100:.1f}%"
    ]
})

profile_check = pd.DataFrame({
    "Simulated variable": [
        "Average unweighted GPA",
        "SAT 25th percentile",
        "SAT 75th percentile",
        "% under $65k household income",
        "% free/reduced lunch",
        "% first generation",
        "% leadership role",
        "% paid part-time job",
        "Average submitted QB list length",
        "% QB students submitting 7+ colleges"
    ],
    "Simulation result": [
        round(students_df["gpa"].mean(), 2),
        round(students_df["sat"].quantile(0.25)),
        round(students_df["sat"].quantile(0.75)),
        f"{students_df['household_under_65k'].mean() * 100:.1f}%",
        f"{students_df['free_reduced_lunch'].mean() * 100:.1f}%",
        f"{students_df['first_generation'].mean() * 100:.1f}%",
        f"{students_df['leadership'].mean() * 100:.1f}%",
        f"{students_df['paid_job'].mean() * 100:.1f}%",
        round(np.mean([len(v) for v in qb_student_preferences.values()]), 2),
        f"{np.mean([len(v) >= 7 for v in qb_student_preferences.values()]) * 100:.1f}%"
    ],
    "QuestBridge target / reference": [
        "3.9 average GPA",
        "1290 lower bound of middle 50%",
        "1460 upper bound of middle 50%",
        "89%",
        "86%",
        "80%",
        "91%",
        "66%",
        "10 college partners on average among 2024 Match Scholarship Recipients",
        "76% of 2024 Match Scholarship Recipients ranked 7+ colleges"
    ]
})

# ============================================================
# 11. SAVE OUTPUTS
# ============================================================

output_dir = Path("/mnt/data/qb_da_final_outputs")
output_dir.mkdir(exist_ok=True)

summary.to_csv(output_dir / "overall_summary.csv", index=False)
group_summary.to_csv(output_dir / "group_summary.csv", index=False)
choice_rank_summary.to_csv(output_dir / "choice_rank_summary.csv", index=False)
profile_check.to_csv(output_dir / "profile_check.csv", index=False)
qb_distortion_summary.to_csv(output_dir / "qb_rank_distortion_summary.csv", index=False)

# GPA distribution
plt.figure(figsize=(7, 5))
students_df["gpa"].hist(bins=18)
plt.title("Simulated GPA Distribution")
plt.xlabel("Unweighted GPA")
plt.ylabel("Number of Students")
plt.tight_layout()
plt.savefig(output_dir / "gpa_distribution.png", dpi=200)
plt.close()

# SAT distribution
plt.figure(figsize=(7, 5))
students_df["sat"].hist(bins=18)
plt.title("Simulated SAT Distribution")
plt.xlabel("SAT Score")
plt.ylabel("Number of Students")
plt.tight_layout()
plt.savefig(output_dir / "sat_distribution.png", dpi=200)
plt.close()

# Choice rank distribution chart with clean # labels
choice_pivot = (
    choice_rank_summary
    .pivot(index="true_choice_rank", columns="mechanism", values="number_of_students")
    .fillna(0)
)

ax = choice_pivot.plot(kind="bar", figsize=(9, 5))
ax.set_title("Distribution of Matched Students by True Choice Rank")
ax.set_xlabel("True Student Choice Rank")
ax.set_ylabel("Number of Matched Students")
ax.set_xticklabels([f"#{int(x)}" for x in choice_pivot.index], rotation=0)
ax.legend(title="Mechanism")
plt.tight_layout()
plt.savefig(output_dir / "choice_rank_distribution.png", dpi=200)
plt.close()

# Match rate by mechanism
plot_summary = combined_results.groupby("mechanism")["matched"].mean() * 100
ax = plot_summary.plot(kind="bar", figsize=(7, 5))
ax.set_title("Match Rate by Mechanism")
ax.set_xlabel("Mechanism")
ax.set_ylabel("Match Rate (%)")
ax.set_xticklabels(plot_summary.index, rotation=0)
plt.tight_layout()
plt.savefig(output_dir / "match_rate_by_mechanism.png", dpi=200)
plt.close()

# Save the full Python code to a file.
code_file_path = Path("/mnt/data/qb_vs_da_final_simulation.py")

# This variable is filled by the notebook wrapper that writes the file.
try:
    code_file_path.write_text(FULL_CODE_TEXT)
except NameError:
    pass

# Print tables for easy viewing.
print("\nPROFILE CHECK")
print(profile_check.to_string(index=False))

print("\nOVERALL SUMMARY")
print(summary.to_string(index=False))

print("\nGROUP SUMMARY")
print(group_summary.to_string(index=False))

print("\nCHOICE RANK SUMMARY")
print(choice_rank_summary.to_string(index=False))

print("\nQB RANK DISTORTION SUMMARY")
print(qb_distortion_summary.to_string(index=False))
