"""
naive_bayes.py
--------------
Gaussian Naive Bayes Classifier.
"""
from sklearn.naive_bayes import GaussianNB


def build() -> GaussianNB:
    return GaussianNB()
