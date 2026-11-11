"""Write the Iris dataset to data/raw/iris.csv (run once; the file is then tracked with DVC)."""
from pathlib import Path

from sklearn.datasets import load_iris

out = Path("data/raw/iris.csv")
out.parent.mkdir(parents=True, exist_ok=True)
df = load_iris(as_frame=True).frame
df.columns = ["sepal_length", "sepal_width", "petal_length", "petal_width", "target"]
df.to_csv(out, index=False)
print(f"wrote {len(df)} rows to {out}")
