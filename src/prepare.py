"""Stage 1 – split the raw data into train and test sets."""
from pathlib import Path

import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

params = yaml.safe_load(open("params.yaml"))["prepare"]

df = pd.read_csv("data/raw/iris.csv")
train, test = train_test_split(
    df,
    test_size=params["test_size"],
    random_state=params["random_state"],
    stratify=df["target"],          # keep the 3 classes balanced in both sets
)

out = Path("data/prepared")
out.mkdir(parents=True, exist_ok=True)
train.to_csv(out / "train.csv", index=False)
test.to_csv(out / "test.csv", index=False)
print(f"train: {len(train)} rows, test: {len(test)} rows")
