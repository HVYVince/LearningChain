FROM python:stretch
WORKDIR /app
COPY requirements.txt .
COPY data data/

ENV TRAINING_PATH="/app/data/mnist_train.csv"
ENV TEST_PATH="/app/data/mnist_test.csv"

RUN pip install -r requirements.txt