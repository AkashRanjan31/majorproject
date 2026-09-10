"""
mlp.py
------
Multi-Layer Perceptron Classifier with StandardScaler pipeline.
"""
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("model", MLPClassifier(
            hidden_layer_sizes=(256, 128, 64),
            activation="relu",
            max_iter=500,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
        )),
    ])
