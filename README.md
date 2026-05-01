# QuestBridge vs Deferred Acceptance Simulation

This repository contains the code and data for a simulation comparing the QuestBridge National College Match mechanism to the Deferred Acceptance (DA) algorithm.

## Overview

This project analyzes how different matching mechanisms affect college admissions outcomes. In particular, it compares:

- **Deferred Acceptance (DA):** a strategy-proof mechanism where students can report their true preferences
- **QuestBridge-style matching:** a mechanism where students may strategically rank colleges to improve match probability

The simulation models 300 QuestBridge finalists and 15 colleges, incorporating realistic academic profiles, preference rankings, and strategic behavior.

---

## Key Findings

- The QuestBridge-style mechanism produces a higher percentage of top-ranked matches (e.g., first-choice and top-3 outcomes)
- However, these improvements are partially driven by **strategic ranking behavior**
- Deferred Acceptance produces outcomes that better reflect **true student preferences**
- Neither mechanism fully eliminates disparities across student groups

---

## Repository Contents

- `qb_vs_da_final_simulation.py` — main simulation code used to generate the simulation results
- `final_correct_qb_da_dataset.csv` — complete dataset of all 300 students, including preference rankings and match outcomes under both mechanisms

---

## Data Description

The dataset includes:

- Student characteristics (academic group)
- True preference rankings
- Submitted (strategic) rankings under the QB-style mechanism
- Match outcomes under both DA and QB
- Rank of matched college in both true and submitted preferences

---

## Reproducibility

The results can be reproduced by running the Python code in a standard environment such as:

- Google Colab: https://colab.research.google.com/
- Jupyter Notebook
- VS Code

---

## Author

Merry Wang

## Note on Code Assistance

The simulation code was developed with the assistance of ChatGPT as a coding tool. All modeling decisions, assumptions, and interpretations are my own.
