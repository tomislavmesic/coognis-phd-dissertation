# PhD Dissertation Appendix Materials: Methodology Step 2

This folder contains the appendix materials for the `Phase 2 – Development and Validation of the Psychological Profiling Model` of the dissertation methodology. The materials document the data preparation, classifier comparison, and model tuning workflow used for binary MBTI personality-dimension classification.

## Contents

| File | Purpose |
| --- | --- |
| `01_data_preparation.ipynb` | Cleans the raw MBTI posts dataset and creates binary target columns for the four MBTI dimensions. |
| `01_data_preparation.html` | Rendered HTML version of the data-preparation notebook. |
| `01_data_preparation.pdf` | Rendered PDF version of the data-preparation notebook. |
| `02_classifiers_test.ipynb` | Compares classifiers and resampling methods across MBTI binary dimensions. |
| `02_classifiers_test.html` | Rendered HTML version of the classifier-comparison notebook. |
| `02_classifiers_test.pdf` | Rendered PDF version of the classifier-comparison notebook. |
| `03_model_tuning.ipynb` | Tunes selected models and evaluates tuned classifier performance. |
| `03_model_tuning.html` | Rendered HTML version of the model-tuning notebook. |
| `03_model_tuning.pdf` | Rendered PDF version of the model-tuning notebook. |

## Expected Data Layout

The notebooks use relative paths. Run them from the root of this phase folder, with data arranged as follows:

```text
phase_2_psychological_profiling/
  data/
    kaggle_mbti.csv
    data_clean.csv
```

The raw source dataset is downloaded from Kaggle:

```text
https://www.kaggle.com/phuongpm/mbti-prediction/data
```

Place the downloaded raw dataset at:

```text
data/kaggle_mbti.csv
```

Then run `01_data_preparation.ipynb` to clean the raw posts and prepare the dataset used by the classifier and tuning notebooks.

## Environment Setup

Use Python 3.9 or newer. The notebooks were originally executed with a Jupyter kernel named `phase_02` using Python 3.9.4.

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install jupyter ipykernel
python -m ipykernel install --user --name phase_02 --display-name "phase_02"
```

Then open the notebooks in Jupyter or VS Code and select the `phase_02` kernel.

If downloading through the Kaggle API instead of the browser, install and configure the Kaggle CLI first:

```bash
pip install kaggle
mkdir -p phase_2_psychological_profiling/input
kaggle datasets download -d phuongpm/mbti-prediction -p phase_2_psychological_profiling/input --unzip
```

After download, make sure the raw file is named:

```text
phase_2_psychological_profiling/data/kaggle_mbti.csv
```

## Reproduction Steps

Run the notebooks in this order:

1. `01_data_preparation.ipynb`

   Input: `data/kaggle_mbti.csv`

   Output: `data/data_clean.csv`

   This notebook cleans the original MBTI post text and derives binary MBTI dimension columns.

2. `02_classifiers_test.ipynb`

   Input: `data/data_clean.csv`

   This notebook builds TF-IDF features, tests classifiers, evaluates resampling strategies, and reports classification metrics for `E_I`, `S_N`, `T_F`, and `J_P`.

3. `03_model_tuning.ipynb`

   Inputs:

   ```text
   data/data_clean.csv
   output/mbti_data_clean_classified_tuned.csv
   ```

   This notebook evaluates tuned models and compares tuned predictions against the prepared classified output.

If starting from `01_data_preparation.ipynb`, either rename its cleaned output to `data/data_clean.csv` before running the later notebooks, or adjust the later notebooks to read `data/data_clean.csv`.

For this appendix package, the intended reproduction flow is:

```bash
cd phase_2_psychological_profiling
mkdir -p input output
# download the Kaggle source dataset into data/kaggle_mbti.csv
# run 01_data_preparation.ipynb
cp data/data_clean.csv data/data_clean.csv
```

## Optional Notebook Export

To regenerate HTML and PDF artifacts from the notebooks:

```bash
cd phase_2_psychological_profiling

jupyter nbconvert --to html 01_data_preparation.ipynb
jupyter nbconvert --to html 02_classifiers_test.ipynb
jupyter nbconvert --to html 03_model_tuning.ipynb

jupyter nbconvert --to pdf 01_data_preparation.ipynb
jupyter nbconvert --to pdf 02_classifiers_test.ipynb
jupyter nbconvert --to pdf 03_model_tuning.ipynb
```

PDF export requires a local LaTeX installation. If PDF export is not available, use the included PDFs or export from the browser after opening the HTML files.

## Reproducibility Notes

- Some classifier and resampling combinations are computationally expensive and may take several minutes to run.
- The notebooks use random seeds in the train/test split, resampling methods, and selected classifiers where supported.
- Results can vary slightly across library versions, operating systems, and hardware.
- The rendered HTML and PDF files are included as dissertation appendix artifacts; the `.ipynb` files are the executable source of record.
