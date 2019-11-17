import os
from sklearn.neighbors import KNeighborsClassifier
import numpy as np
import pandas as pd
from joblib import dump

K_VALUE = int(os.getenv("K"))

training_path = os.getenv("TRAINING_PATH")
test_path = os.getenv("TEST_PATH")


validation = os.getenv("VALIDATION", False)

model_path = os.path.join(os.sep, "tmp", "model")

if not validation:
    train = np.array(pd.read_csv(training_path, header=None))
    train_X = train[:, :-1]
    train_y = train[:, -1]

    test = np.array(pd.read_csv(test_path, header=None))
    test_X = train[:, :-1]
    test_y = train[:, -1]

    clf = KNeighborsClassifier(n_neighbors=K_VALUE)
    clf.fit(train_X, train_y)

    dump(clf, model_path)
else:
    clf = load(model_path)

y_hat = clf.predict(test_X)

accuracy = np.mean(train_y == y_hat)

print(accuracy)
