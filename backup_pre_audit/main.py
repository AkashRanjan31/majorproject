"""
main.py
-------
Run the full project pipeline from one file.
"""

from src.evaluate import evaluate_model
from src.load_data import analyze_dataset, load_dataset
from src.train_model import train_model


def main() -> None:
    """Analyze data, train the model, and evaluate it."""
    dataset = load_dataset()
    analyze_dataset(dataset)
    train_model()
    evaluate_model()


if __name__ == "__main__":
    main()
