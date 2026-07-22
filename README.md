# Equitable Allocation of Housing Interventions

Predicting exits from homelessness with machine learning, then allocating scarce
housing interventions with an optimization model that maximizes exits **without
violating the Fair Housing Act**. This repository extends
[Kube et al. (2023)](https://doi.org/10.1145/3617694.3623217) and accompanies the
paper [`EquitableInterventionAllocation_05192024.pdf`](EquitableInterventionAllocation_05192024.pdf).

## Abstract

The number of people experiencing homelessness in the United States is growing, and
there are serious consequences for living unsheltered. At the same time, federal,
state, and local governments devote a substantial amount of funding to addressing
this persistent problem. Given this growth, governments may need to be more efficient
with existing funding. To that end, recent advances leveraging machine learning and
optimization by Kube et al. (2023) promise to more efficiently allocate scarce housing
interventions to households. However, governments bound by legal and ethical
constraints may not be able to implement these solutions if efficiency gains come at
the cost of violating the Fair Housing Act. In this paper, we advance the work by
Kube et al. (2023) in the following ways:

- We derive the relationship between the optimal allocation of housing interventions to
  households and the conditional average treatment effect.
- We document where the Department of Housing and Urban Development's policy may not
  align with the goal of achieving the greatest number of exits from homelessness.
- We develop a simple exploratory data analysis technique for determining when
  allocating interventions to maximize exits from homelessness may violate the Fair
  Housing Act.
- We develop a method for dynamically addressing potential disproportionate assignments
  of housing interventions by Protected Classes, thereby ensuring the Fair Housing Act
  is not violated.

## Pipeline at a glance

```
  HMIS warehouse (SQL / pyodbc)
          │
          ▼
   Build/     ── feature engineering, outcome labeling, train/test split, encoders
          │        → train_allfeatures_*.csv, test_allfeatures_*.csv, traindf_*.pkl
          ▼
   Analysis/  ── model grid search (ElasticNet, RandomForest) + fairness EDA (CATE)
          │        → Output/models/*.pkl, per-household P(exit | intervention)
          ▼
          │        → OptimizationData_04012024.csv
          ▼
   Optimization/ ── fairness-constrained integer program (PuLP / CBC)
                   → weekly household → intervention assignments
```

The three interventions modeled throughout are **RRH** (Rapid Re-Housing), **PSH**
(Permanent Supportive Housing), and **TSH** (Transitional Housing).

## Repository layout

| Path | What it does |
| --- | --- |
| [`Build/`](Build/) | Pulls HMIS data over SQL, engineers features, labels outcomes, splits train/test, and fits encoders/scalers. |
| [`Analysis/`](Analysis/) | Trains and evaluates models, and runs the counterfactual / Conditional Average Treatment Effect (CATE) fairness analysis. |
| [`Optimization/`](Optimization/) | Integer program that allocates interventions to households subject to weekly capacity and a fairness penalty. |
| [`EquitableInterventionAllocation_05192024.pdf`](EquitableInterventionAllocation_05192024.pdf) | The paper. |

### `Build/` — from HMIS to an analytic dataset

Run in this order (see [`Build/ReadME.txt`](Build/ReadME.txt) for the original notes):

1. [`BuildFeatures_02132024.py`](Build/BuildFeatures_02132024.py) — runs three SQL
   pulls against the HMIS warehouse (`e_prod`) and saves the raw feature tables:
   - [`HeadofHouseholdsSQL_01312024.py`](Build/HeadofHouseholdsSQL_01312024.py) —
     head-of-household features (disability, income, benefits), limited to HoH + CE enrollments.
   - [`HouseholdRollUpSQL_01312024.py`](Build/HouseholdRollUpSQL_01312024.py) —
     features for the whole household, aggregated to the household level.
   - [`LiteralHomelessnessHistorySQL_01312024.py`](Build/LiteralHomelessnessHistorySQL_01312024.py) —
     all literal-homelessness events prior to a Coordinated Entry (CE) enrollment.
2. [`BuildInterventionOutcomes_02132024.py`](Build/BuildInterventionOutcomes_02132024.py) —
   associates housing interventions with CE events and derives whether each household
   **successfully exited** (helpers in [`InterventionOutcomes_SQL_02122024.py`](Build/InterventionOutcomes_SQL_02122024.py)).
3. [`BuildAnalyticDataSet_02142024.py`](Build/BuildAnalyticDataSet_02142024.py) —
   merges 1) and 2), cleans sparse categoricals and invalid continuous values
   (e.g. negative ages), and writes **separate train/test sets to avoid leakage**.
4. [`PreprocessAnalyticDataSet_02292024.py`](Build/PreprocessAnalyticDataSet_02292024.py) —
   fits imputers, one-hot **and Weight-of-Evidence (WOE)** encoders, and standard
   scalers, then materializes ML-ready feature matrices per feature set.
- [`Dictionaries.py`](Build/Dictionaries.py) — shared config: category remapping rules
  and the feature-set lists (`X_hoh_*`, `X_house_*`, `X_all_*`, in OHE and WOE
  variants) plus the `ywoexmatch` helper that maps WOE column names to a given outcome.

### `Analysis/` — models and the fairness EDA

- [`ElasticNet_03012024.py`](Analysis/ElasticNet_03012024.py) — a large grid search
  (up to 288 configurations) over Lasso / Ridge / Elastic-Net logistic regression,
  sweeping **6 outcome definitions × 3 feature sets × 2 encodings × PCA / feature
  selection**, with a coarse-then-refined hyperparameter search. Each fitted model and
  its CV metrics are pickled to `Output/models/`.
- [`RFC_03082024.py`](Analysis/RFC_03082024.py) — the Random-Forest analogue (48
  configurations; OHE and the redundant PCA+selection combos are skipped because RF
  handles them poorly / they are too slow).
- [`CounterfactualEvaluation_03182024.py`](Analysis/CounterfactualEvaluation_03182024.py) —
  the fairness core. For the best models it computes **Conditional Average Treatment
  Effects (CATE)** — the change in predicted exit probability if a household *were*
  vs. *were not* given each intervention — and plots kernel-density estimates of that
  change **broken out by protected class** (race, gender, sexual orientation,
  disability, veteran status, family size). Divergent distributions are the EDA signal
  that maximizing exits could disadvantage a protected class.
- [`EvaluateTestingSet_04012024.py`](Analysis/EvaluateTestingSet_04012024.py) — locks
  in the chosen model (RandomForest, `success_180`), scores the held-out test set,
  retrains on all data, generates per-household P(exit) under each intervention, and
  exports `OptimizationData_04012024.csv` — the hand-off to the optimizer. Person IDs
  are re-mapped to synthetic IDs and dates are jittered ±3 days to de-identify.

**Outcome definitions.** Six binary labels are modeled: `success_180 / 365 / 730`
(a successful exit with no reentry within 6 / 12 / 24 months) and
`success_noexit_180 / 365 / 730` (the same reentry windows but *not* conditioned on a
recorded exit destination).

### `Optimization/` — fairness-constrained allocation

- [`Optimiz_initial.ipynb`](Optimization/Optimiz_initial.ipynb) — the baseline model:
  binary `x[household, intervention]`, maximize total exit probability, one assignment
  per household, a flat per-intervention capacity. No time dimension, no fairness term.
- [`Optimization_final.ipynb`](Optimization/Optimization_final.ipynb) — the full model.
  It adds a **weekly time index**, real **weekly capacities** derived from historical
  intervention counts, and a **fairness penalty**:

  **Decision variables** `x[i, j, t] ∈ {0, 1}` — assign household `i` intervention `j`
  in week `t`.

  **Objective** (maximize):

  ```
  Σ  P(exit | i, j, t) · x[i,j,t]        # efficiency: expected exits
    +  Σ  Cj · (1 − penalty[subpop, t]) · x[i,j,t]   # fairness reward
  ```

  where `penalty[subpop, t]` is a per-week gender **risk ratio** (`R_male` / `R_female`,
  relative to an equity ratio of 1), and **`Cj` ≥ 0** is the tunable fairness weight
  (`Cj = 0` reduces to pure efficiency). The notebook sweeps `Cj` from 0.1 → 0.6,
  shrinking each risk ratio toward the equity line via
  `adjusted_R = 1 + (R − 1)·(1 − Cj)`, and selects **`Cj ≈ 0.322`** to hit a target
  split of ~55.8% female / 44.2% male assignments.

  **Constraints:** each household assigned at most once; per-intervention weekly
  assignments ≤ weekly capacity.

  Solved with the CBC solver bundled in PuLP (`PULP_CBC_CMD`); CPLEX is optionally
  wired in but commented out.

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

Paths and the database connection are resolved from environment variables by
[`Build/config.py`](Build/config.py), so the code is cross-platform and no credentials
live in source control. All are optional except the DB string (needed only by the
Build scripts that query HMIS):

| Variable | Purpose | Default |
| --- | --- | --- |
| `HOMELESSNESS_DATA_DIR` | Input / intermediate data | `<repo>/Data` |
| `HOMELESSNESS_OUTPUT_DIR` | Trained models and figures | `<repo>/Output` |
| `HOMELESSNESS_DB_CONN` | `pyodbc` connection string for the HMIS warehouse | — (required for `Build/` DB pulls) |

The `Data/` and `Output/` trees are created automatically on first import.

### Running

The `Build/` and `Analysis/` scripts run from **inside their own directory** (they use
`sys.path.append('../')` to import `Build.Dictionaries` / `Build.config`):

```bash
cd Analysis
python ElasticNet_03012024.py
```

The optimization notebooks read their inputs from `HOMELESSNESS_DATA_DIR` (falling back
to a sibling `Dataset/` folder), so point that variable at the directory holding
`OptimizationData_04012024.csv` and `InterventionData_04052024.csv`:

```bash
export HOMELESSNESS_DATA_DIR=/path/to/data
jupyter notebook Optimization/Optimization_final.ipynb
```

## Reproducibility notes & caveats

This is **research-grade code**, not a packaged product. Note before running:

- **Data is not included.** The scripts expect HMIS extracts and intermediate CSV/PKL
  files under `HOMELESSNESS_DATA_DIR`, none of which are in this repo. Access to
  protected HMIS data requires appropriate authorization.
- **Database access.** Set `HOMELESSNESS_DB_CONN` to a valid `pyodbc` connection string
  before running the `Build/` scripts that query the warehouse; they raise a clear error
  if it is unset.
- **Dated filenames.** Several scripts read intermediate files with hard-coded dates in
  their names (e.g. `traindf_2024-03-07.pkl`, `InterventionOutcomes_2024-04-18.pkl`),
  exposed as `SOURCE_DATE` constants where practical. Adjust these to match your build.
- **`np.random` placeholder.** One cell in `Optimization_final.ipynb`
  (`evaluate_model_effectiveness`) returns a random value as a stand-in effectiveness
  metric — treat the `Cj` selection cells as the source of truth for the final model.

## Requirements

Python 3.9+ and the packages in [`requirements.txt`](requirements.txt): pandas, numpy,
scikit-learn, category_encoders, scipy, matplotlib, pyodbc, and pulp.

## Authors

- **Trevor Gratz** — data build, modeling, and counterfactual/fairness analysis
  (`trevormgratz@gmail.com`).
- **Anu Zan** — optimization model (Georgia Tech ISYE 6740, Spring 2024).
