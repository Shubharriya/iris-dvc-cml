"""Stage 3 – evaluate on the test set: metrics.json + confusion matrix plot."""
import json
import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, f1_score

test = pd.read_csv("data/prepared/test.csv")
X, y = test.drop(columns="target"), test["target"]
model = pickle.load(open("models/model.pkl", "rb"))
pred = model.predict(X)

metrics = {
    "accuracy": round(accuracy_score(y, pred), 4),
    "f1_macro": round(f1_score(y, pred, average="macro"), 4),
}
json.dump(metrics, open("metrics.json", "w"), indent=2)
print(metrics)

ConfusionMatrixDisplay.from_predictions(
    y, pred, display_labels=["setosa", "versicolor", "virginica"], cmap="Blues", colorbar=False
)
plt.title("Confusion matrix (test set)")
plt.tight_layout()
plt.savefig("confusion_matrix.png", dpi=120)
