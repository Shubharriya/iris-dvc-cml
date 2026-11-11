# Reproducible ML Experiment with Git, DVC and CML (Iris)

Random-forest classifier on the Iris dataset, turned into a versioned, reproducible DVC pipeline whose
results are reproduced and reported automatically on every pull request by GitHub Actions + CML.

```
iris-dvc-cml/
├── notebooks/iris_experiment.ipynb   (a) exploratory notebook with results
├── src/download_data.py              writes data/raw/iris.csv
├── src/prepare.py                    (b) stage 1: train/test split
├── src/train.py                      (b) stage 2: train the model
├── src/evaluate.py                   (b) stage 3: metrics.json + confusion_matrix.png
├── params.yaml                       (b) all parameters
├── dvc.yaml                          (d) pipeline definition
├── .github/workflows/cml.yaml        (e) CI workflow with CML report
└── requirements.txt
```

Expected outputs below are from an actual run of these exact files.

---

## 0. Setup (once)

```bash
cd iris-dvc-cml
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install jupyter                     # only needed for the notebook
```

## (a) Notebook: train and report accuracy and F1

```bash
jupyter notebook notebooks/iris_experiment.ipynb     # Kernel → Restart & Run All
```

Random forest (10 trees, depth 2), 70/30 stratified split, seed 42. Expected:

```
train: 105 rows, test: 45 rows
Accuracy : 0.9111
F1 (macro): 0.9107
              precision    recall  f1-score   support
      setosa       1.00      1.00      1.00        15
  versicolor       0.82      0.93      0.88        15
   virginica       0.92      0.80      0.86        15
```

Macro F1 averages the three classes equally, so a weak class is not hidden.

## (b) Notebook → scripts + params.yaml

| Notebook section | Script | Reads | Writes | Parameters used |
|---|---|---|---|---|
| Load + split | `src/prepare.py` | `data/raw/iris.csv` | `data/prepared/{train,test}.csv` | `prepare.test_size`, `prepare.random_state` |
| Train | `src/train.py` | `data/prepared/train.csv` | `models/model.pkl` | `train.n_estimators`, `train.max_depth`, `train.random_state` |
| Evaluate | `src/evaluate.py` | model + test set | `metrics.json`, `confusion_matrix.png` | – |

No value is hard-coded in the scripts: everything tunable is read from `params.yaml`.

## (c) Git + DVC: track the dataset and configure a remote

```bash
git init -b main
dvc init
python src/download_data.py                 # creates data/raw/iris.csv (150 rows)
dvc add data/raw/iris.csv                   # creates data/raw/iris.csv.dvc + data/raw/.gitignore
mkdir -p ../dvc-storage
dvc remote add -d localremote ../dvc-storage
git add .
git commit -m "Iris project: scripts, params, notebook; data tracked by DVC"
dvc push                                    # → "1 file pushed"
```

What to show:
- `cat data/raw/iris.csv.dvc`: Git stores only this pointer (`md5: 4224576f0267bf88902f87f0f6200967`, size 2757), not the CSV.
- `cat .dvc/config`: the default remote `localremote`.
- `git ls-files`: `iris.csv` is **not** listed, `iris.csv.dvc` is.

The remote here is a local folder, which DVC fully supports. A cloud remote (S3, Google Drive, DagsHub)
is configured the same way: `dvc remote add -d myremote s3://bucket/path`.

## (d) DVC pipeline, parameter change and comparison

```bash
dvc repro                 # runs prepare → train → evaluate, writes dvc.lock
dvc metrics show
git add -A && git commit -m "Baseline pipeline run" && dvc push
dvc repro                 # again: every stage is skipped ("Data and pipelines are up to date")
dvc dag                   # shows the pipeline graph
```

Expected after the first run:
```
Path          accuracy    f1_macro
metrics.json  0.9111      0.9107
```

Change parameters on a branch and compare:

```bash
git checkout -b experiment/more-trees
# edit params.yaml:  n_estimators: 10 → 50,  max_depth: 2 → 4
dvc repro                 # 'prepare' is skipped; only 'train' and 'evaluate' re-run
dvc params diff
dvc metrics diff
```

Expected:
```
Path         Param               HEAD    workspace
params.yaml  train.max_depth     2       4
params.yaml  train.n_estimators  10      50

Path          Metric    HEAD    workspace    Change
metrics.json  accuracy  0.9111  0.8889       -0.0222
metrics.json  f1_macro  0.9107  0.8878       -0.0229
```

**Interpretation:** the larger forest is slightly *worse*. With 45 test samples, −0.0222 is exactly one
more misclassified flower (1/45), so the difference is within noise: a bigger model is not automatically
better. DVC re-ran only the stages whose parameters or inputs changed.

```bash
git add -A && git commit -m "Experiment: 50 trees, depth 4"
```

## (e) GitHub Actions + CML report on a pull request

The workflow `.github/workflows/cml.yaml` runs on every pull request into `main`:

1. Checks out the code with full history.
2. Installs Python 3.13, CML and the pinned requirements (including DVC).
3. Gets the dataset: `dvc pull`, or, because a local-folder remote is not reachable from GitHub,
   regenerates it and **verifies its MD5 equals the hash DVC recorded**.
4. `dvc repro --force`: re-runs every stage from scratch.
5. Checks that the reproduced `metrics.json` equals the one committed in the PR.
6. Builds `report.md` (metrics diff and params diff against `main`, the confusion matrix, the pipeline
   graph) and posts it on the PR with `cml comment create`.

### Steps on GitHub

The workflow file must be on `main` before you open the PR. If you already created the branch in (d),
commit the workflow on `main` first (`git checkout main`, then commit `.github/`), then go back to the
branch and run `git rebase main`.

```bash
# 1. Create an EMPTY repository on github.com (no README), then:
git checkout main
git remote add origin https://github.com/<your-username>/iris-dvc-cml.git
git push -u origin main

# 2. Push the experiment branch
git checkout experiment/more-trees
git push -u origin experiment/more-trees
```

3. On GitHub, click **Compare & pull request** → base `main` ← `experiment/more-trees` → **Create pull request**.
4. Open the **Actions** tab and watch "CML experiment report" (about 2 minutes).
5. The PR receives a comment like:

> ## 🔁 Reproduced experiment
> ✅ Metrics reproduced exactly from the committed code, data and parameters.
>
> | Path | Metric | origin/main | workspace | Change |
> |---|---|---|---|---|
> | metrics.json | accuracy | 0.9111 | 0.8889 | -0.0222 |
> | metrics.json | f1_macro | 0.9107 | 0.8878 | -0.0229 |
>
> *(plus the parameters table, confusion matrix image and pipeline graph)*

If the comment step fails with a permissions error, go to **Settings → Actions → General → Workflow
permissions** and select **Read and write permissions**.

### Screenshots to include in your submission
1. Notebook output (accuracy, F1, classification report, confusion matrix)
2. `params.yaml` and the three scripts
3. `cat data/raw/iris.csv.dvc`, `dvc remote list`, `dvc push`
4. `dvc repro` (first run and the "skipping" re-run), `dvc dag`
5. `dvc params diff` and `dvc metrics diff`
6. The green Actions run and the CML comment on the pull request
