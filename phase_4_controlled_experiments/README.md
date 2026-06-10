# PhD Dissertation Appendix Materials: Methodology Phase 4

This folder contains the appendix materials for `Phase 4 - Controlled Experiments and Evaluation` of the dissertation methodology. The materials document the statistical analysis workflow for two controlled experiments evaluating persona-aligned responses and matched versus mismatched response conditions.

The executable source of record is provided as Jupyter notebooks. Rendered HTML/PDF versions, result tables, and figures are included as appendix artifacts.

## Contents

| Path | Purpose |
| --- | --- |
| `notebooks/experiment_a_analysis.ipynb` | Reproduces the main statistical analysis for Experiment A. |
| `notebooks/experiment_a_analysis.html` | Rendered HTML version of the Experiment A notebook. |
| `notebooks/experiment_a_analysis.pdf` | Rendered PDF version of the Experiment A notebook. |
| `notebooks/experiment_b_analysis.ipynb` | Reproduces the main statistical analysis for Experiment B. |
| `notebooks/experiment_b_analysis.html` | Rendered HTML version of the Experiment B notebook. |
| `notebooks/experiment_b_analysis.pdf` | Rendered PDF version of the Experiment B notebook. |
| `data/experiment_a_data_participant_summary.csv` | Participant-level Experiment A input dataset. |
| `data/experiment_a_data_scenario.csv` | Scenario-level Experiment A input dataset. |
| `data/experiment_b_data_participant_summary.csv` | Participant-level Experiment B input dataset. |
| `data/experiment_b_data_scenario.csv` | Scenario-level Experiment B input dataset. |
| `results/` | Exported CSV result tables used as appendix artifacts. |
| `figures/` | Exported PNG figures used as appendix artifacts. |

## Experimental Materials

The `experiments/` directory contains the participant-facing experimental instruments used for the two controlled evaluation studies. These materials document the opening screens, persona elicitation logic, scenario texts, response stimuli, interaction scripts, questionnaires, and representative examples.

### Experiment A

Experiment A evaluates psychologically adapted AI-generated support responses in comparison with generic AI-generated support responses. Participants are assigned to one of four communication personas based on their preferred answer style:

- STJ: structured, procedural, step-by-step communication.
- NTP: analytical, explanatory, reasoning-oriented communication.
- NFJ: supportive, contextual, reassurance-oriented communication.
- SFP: concise, practical, action-oriented communication.

The experiment contains six university support scenarios covering student exchange, tuition payment delay, Wi-Fi access, suspicious email handling, attendance policy, and elective course selection. For each scenario, participants evaluate a generic response and a persona-adapted response. A Group A/B counterbalancing design varies whether the generic or adapted response appears as Response A or Response B, reducing response-order effects. The questionnaire captures perceived clarity, satisfaction, trust, reuse intention, and response preference.

### Experiment B

Experiment B evaluates expert interaction matching in simulated university support conversations. Participants are presented with matched and mismatched expert-user interactions, where the expert's communication style either corresponds to or differs from the participant's selected communication persona.

The experiment contains four university scenarios: suspicious email, course schedule conflict, Wi-Fi access problem, and thesis topic change. Each scenario preserves the same core facts across conditions while varying the expert communication style. The questionnaire captures perceived ease, helpfulness, trust, likelihood of contacting the expert again, perceived style match, and overall confidence in using a support system that connects users with experts.

## Repository Structure

```text
phase_4_controlled_experiments/
  experiments/
    experiment_a/
    experiment_b/
  data/
  figures/
  notebooks/
  results/
```

| Path | Reproducibility Role |
| --- | --- |
| `experiments/` | Participant-facing experimental materials, questionnaires, scenario stimuli, persona definitions, and representative examples. |
| `data/` | Input datasets used by the statistical notebooks. |
| `figures/` | Exported visual artifacts generated from the statistical analysis. |
| `notebooks/` | Executable Jupyter notebooks that reproduce the Experiment A and Experiment B analyses. |
| `results/` | Exported CSV result tables corresponding to the notebook calculations. |

## Expected Data Layout

The notebooks use relative paths and expect the following layout:

```text
phase_4_controlled_experiments/
  data/
    experiment_a_data_participant_summary.csv
    experiment_a_data_scenario.csv
    experiment_b_data_participant_summary.csv
    experiment_b_data_scenario.csv
  notebooks/
    experiment_a_analysis.ipynb
    experiment_b_analysis.ipynb
  results/
  figures/
```

The input CSV files use semicolon delimiters and comma decimal separators. The notebooks read them with:

```python
pd.read_csv(..., sep=";", decimal=",", encoding="utf-8-sig")
```

## Environment Setup

Use Python 3.9 or newer.

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install pandas numpy scipy matplotlib statsmodels jupyter ipykernel nbconvert
python -m ipykernel install --user --name phase_04 --display-name "phase_04"
```

Then open the notebooks in Jupyter or VS Code and select the `phase_04` kernel.

## Reproduction Steps

Run the notebooks from the `notebooks/` directory, because the notebook code reads input files from `../data/`.

```bash
cd phase_4_controlled_experiments/notebooks
jupyter notebook
```

Run the notebooks in this order:

1. `experiment_a_analysis.ipynb`

   Inputs:

   ```text
   ../data/experiment_a_data_participant_summary.csv
   ../data/experiment_a_data_scenario.csv
   ```

   This notebook calculates the Experiment A participant preference results, aligned versus generic response score comparison, persona-level summaries, scenario-level summaries, and visualizations.

   Main statistical procedures:

   - Binomial test for aligned-response preference.
   - Wilson confidence interval for the aligned-preference proportion.
   - Paired t-test for aligned versus generic mean scores.
   - Wilcoxon signed-rank test.
   - Cohen's h and paired Cohen's d effect sizes.

2. `experiment_b_analysis.ipynb`

   Inputs:

   ```text
   ../data/experiment_b_data_participant_summary.csv
   ../data/experiment_b_data_scenario.csv
   ```

   This notebook calculates the Experiment B matched versus mismatched group comparison, contact-again analysis, persona-level summaries, scenario-level summaries, and visualizations.

   Main statistical procedures:

   - Welch independent-samples t-tests for group comparisons.
   - Mann-Whitney U tests for matched versus mismatched comparisons.
   - Benjamini-Hochberg FDR correction for multiple comparisons.
   - Chi-square test for the binary contact-again outcome.
   - Phi, Cramer's V, odds ratio, and Cohen's d effect sizes.

## Included Result Tables

The `results/` directory contains exported CSV summaries corresponding to notebook calculations:

| File | Purpose |
| --- | --- |
| `experiment_a_core_calculations.csv` | Core Experiment A hypothesis-test results and effect sizes. |
| `experiment_a_participant_summary.csv` | Participant-level Experiment A summary. |
| `experiment_a_persona_summary.csv` | Experiment A summary by persona. |
| `experiment_a_scenario_summary.csv` | Experiment A summary by scenario. |
| `experiment_b_group_means.csv` | Experiment B group-level descriptive statistics. |
| `experiment_b_group_comparison.csv` | Experiment B matched versus mismatched statistical comparison. |
| `experiment_b_contact_yes_rates.csv` | Binary contact-again rates by group. |
| `experiment_b_contact_binary_test.csv` | Chi-square test for the contact-again binary outcome. |
| `experiment_b_contact_binary_effect_size.csv` | Contact-again binary effect size. |
| `experiment_b_contact_binary_odds_ratio.csv` | Contact-again binary odds ratio. |
| `experiment_b_persona_summary.csv` | Experiment B summary by persona and group. |
| `experiment_b_scenario_summary.csv` | Experiment B summary by scenario and group. |

## Included Figures

The `figures/` directory contains exported PNG visualizations corresponding to notebook plots:

| File | Purpose |
| --- | --- |
| `experiment_a_mean_scores.png` | Experiment A aligned versus generic mean scores. |
| `experiment_a_persona_effects.png` | Experiment A personalization effect by persona. |
| `experiment_a_scenario_effects.png` | Experiment A personalization effect by scenario. |
| `experiment_a_preference_counts.png` | Experiment A final preference counts. |
| `experiment_a_persona_comparison.png` | Experiment A persona-level aligned/generic comparison. |
| `experiment_a_scenario_comparison.png` | Experiment A scenario-level aligned/generic comparison. |
| `experiment_b_overall_mean_by_group.png` | Experiment B overall mean by group. |
| `experiment_b_style_match_by_group.png` | Experiment B style-match mean by group. |
| `experiment_b_contact_again.png` | Experiment B contact-again rate comparison. |
| `experiment_b_persona_comparison.png` | Experiment B persona-level matched/mismatched comparison. |
| `experiment_b_scenario_comparison.png` | Experiment B scenario-level matched/mismatched comparison. |
| `experiment_b_mean_differences.png` | Experiment B matched minus mismatched mean differences. |
| `experiment_b_effect_sizes.png` | Experiment B Cohen's d effect sizes across metrics. |

## Optional Notebook Export

To regenerate rendered HTML artifacts after executing the notebooks:

```bash
cd phase_4_controlled_experiments/notebooks

jupyter nbconvert --to html experiment_a_analysis.ipynb
jupyter nbconvert --to html experiment_b_analysis.ipynb
```

To regenerate PDFs:

```bash
cd phase_4_controlled_experiments/notebooks

jupyter nbconvert --to pdf experiment_a_analysis.ipynb
jupyter nbconvert --to pdf experiment_b_analysis.ipynb
```

PDF export requires a local LaTeX installation. If PDF export is not available, use the included PDFs or export from the browser after opening the HTML files.

## Reproducibility Notes

- The notebooks calculate and display the statistical tables and figures. In their current form, they do not overwrite the CSV files in `results/` or the PNG files in `figures/`.
- Run notebooks from `phase_4_controlled_experiments/notebooks` so that the relative paths to `../data/` resolve correctly.
- The included rendered HTML/PDF files preserve the notebook outputs as dissertation appendix artifacts.
- Results can vary slightly across Python package versions, especially for statistical routines and plot rendering.
