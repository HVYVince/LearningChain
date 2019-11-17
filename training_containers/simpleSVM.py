import os
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
import numpy as np
import pandas as pd
from joblib import dump


training_path = os.getenv("TRAINING_PATH")
test_path = os.getenv("TEST_PATH")


train = np.array(pd.read_csv(training_path, header=None))
train_X = train[:, :-1]
train_y = train[:, -1]

test = np.array(pd.read_csv(test_path, header=None))
test_X = train[:, :-1]
test_y = train[:, -1]


clf = SVC()
clf.fit(train_X, train_y)


y_hat = clf.predict(test_X)

accuracy = np.mean(train_y == y_hat)

print(accuracy)

model_path = os.path.join(os.sep, "tmp", "model")

dump(clf, model_path)
