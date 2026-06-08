# COOGNIS PhD Dissertation Repository

## Enhancing Internal Knowledge Discovery through Artificial Intelligence and Psychological Profiling

This repository contains the reproducibility materials supporting the doctoral dissertation:

> **Enhancing Internal Knowledge Discovery through Artificial Intelligence and Psychological Profiling**

by **Tomislav Mesic**

conducted at:

**University of Pardubice, Faculty of Economics and Administration**  
Pardubice, Czech Republic

with academic affiliation to:

**Algebra Bernays University**  
Zagreb, Croatia

---

## Repository Purpose

This repository provides research materials supporting the methodological reproducibility of the doctoral dissertation, including:

- cleaned datasets
- statistical analysis workflows
- machine learning experimentation
- controlled experimental evaluation
- proof-of-feasibility implementation materials
- exported notebooks
- figures and statistical outputs
- supporting documentation

The repository is organized according to the **multi-phase methodological framework** adopted in the dissertation and prioritizes **scientific reproducibility**, **research transparency**, and **methodological clarity**.

At the same time, certain implementation components remain intentionally restricted in order to balance reproducibility with ethical, privacy, security, and intellectual-property considerations related to future system development.

---

## Dissertation Overview

The dissertation investigates whether **psychologically adaptive expert systems** may improve:

- organizational communication
- hidden knowledge discovery
- expertise facilitation
- communication alignment
- personalized organizational support

through the integration of:

- **Artificial Intelligence (AI)**
- **Machine Learning (ML)**
- **Psychological Profiling**
- **Adaptive Communication**
- **Knowledge Discovery**
- **Expert Recommendation Mechanisms**

The research introduces **COOGNIS**, a psychologically adaptive expert-system framework designed to support organizational intelligence through machine learning–based psychological profiling and context-sensitive communication adaptation.

---

## Methodological Framework

The repository is structured according to the dissertation methodology phases.

### Phase 1 – Behavioral Economics and Organizational Analysis

Contains materials related to organizational and behavioral analysis used to identify challenges associated with hidden knowledge, communication barriers, and organizational support limitations.

Includes:

- survey instruments
- cleaned survey datasets
- statistical analysis notebooks
- statistical outputs
- visualizations
- exported notebook documentation

Folder:

```text
phase_1_behavioral_economics/
```

---

### Phase 2 – Development and Validation of the Psychological Profiling Model

Contains materials supporting the development and validation of the **SYNAPSE** psychological profiling module through a multimodel MBTI machine learning framework.

Includes:

- classifier comparison notebooks
- model tuning notebooks
- preprocessing workflows
- evaluation metrics
- trained-model documentation
- exported notebooks

The original training dataset is referenced from Kaggle and is not redistributed when licensing restrictions apply.

Folder:

```text
phase_2_psychological_profiling/
```

---

### Phase 3 – System Implementation and Modular Architecture

Contains reproducibility materials supporting the proof-of-feasibility implementation of the **COOGNIS** framework.

Includes:

- modular architecture documentation
- limited reproducible prototype implementation
- implementation notes
- API examples
- architectural resources

To balance **scientific reproducibility** with **future commercialization considerations**, this phase intentionally includes a **limited research-oriented implementation package** rather than the complete production system.

The provided materials remain sufficient to reproduce the architectural logic and implementation principles described in the dissertation.

Folder:

```text
phase_3_coognis_implementation/
```

---

### Phase 4 – Controlled Experiments and Evaluation

Contains materials supporting the controlled experimental evaluation of psychologically adaptive communication and expert matching.

Includes:

- experimental scenarios
- participant and scenario datasets
- statistical analysis notebooks
- evaluation outputs
- figures and plots
- exported notebook documentation

This phase supports reproducibility of:

- **Experiment A** – Adaptive Communication Evaluation (**H1**)
- **Experiment B** – Psychologically Informed Expert Matching (**H2**)

Folder:

```text
phase_4_controlled_experiments/
```

---

## Repository Structure

```text
coognis-phd-dissertation/
│
├── README.md
├── requirements.txt
├── CITATION.cff
│
├── phase_1_behavioral_economics/
├── phase_2_psychological_profiling/
├── phase_3_coognis_implementation/
├── phase_4_controlled_experiments/
│
└── supplementary_materials/
```

---

## Reproducibility Philosophy

This repository prioritizes **scientific reproducibility** while balancing practical, ethical, and intellectual-property considerations.

The included materials are sufficient to reproduce:

- statistical analyses
- machine learning experiments
- controlled evaluations
- proof-of-feasibility implementation workflows

Certain production-oriented implementation components remain intentionally restricted in order to protect:

- privacy
- security
- future commercialization potential
- organizational deployment considerations

while preserving the scientific reproducibility of the research.

---

## Environment Setup

The repository was developed using **Python** and **Jupyter Notebook** workflows.

Install dependencies using:

```bash
pip install -r requirements.txt
```

It is recommended to create a virtual environment before installation.

Example:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## How to Reproduce the Research

Each methodological phase contains an independent `README.md` file describing:

- required inputs
- execution order
- notebook workflow
- expected outputs
- reproducibility procedures
- dependencies
- methodological assumptions

Researchers are encouraged to follow phase-specific instructions sequentially.

Recommended execution order:

```text
1. Phase 1 – Behavioral Economics
2. Phase 2 – Psychological Profiling
3. Phase 3 – COOGNIS Implementation
4. Phase 4 – Controlled Experiments
```

---

## License

This repository is distributed for **academic and non-commercial research purposes only**.

Unless otherwise specified, materials are provided under:

> **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**

You are permitted to:

- use
- reproduce
- adapt
- cite

the materials for:

- academic research
- scientific reproducibility
- educational purposes

You may **not**:

- commercially redistribute
- commercialize
- repackage
- use implementation materials for commercial product development

without explicit written permission from the author.

The **COOGNIS framework**, implementation concepts, and associated system-development materials remain protected intellectual property.

---

## Citation

If you use this repository in academic work, please cite:

**Mesic, T.** (2026).  
*Enhancing Internal Knowledge Discovery through Artificial Intelligence and Psychological Profiling* (Doctoral dissertation).  
University of Pardubice, Faculty of Economics and Administration.

Citation metadata is additionally available in:

```text
CITATION.cff
```

---

## Contact

**Tomislav Mesic**

University of Pardubice, Faculty of Economics and Administration  
Pardubice, Czech Republic

Algebra Bernays University  
Zagreb, Croatia

Email:

- tomislav.mesic@upce.cz  
- tomislav.mesic@algebra.hr