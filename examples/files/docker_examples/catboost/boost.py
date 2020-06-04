#!/usr/bin/env python3
from catboost import CatBoostClassifier
from catboost.datasets import titanic
import random
random.seed(42)

vars = [
    ('iterations', int),
    ('learning_rate', float),
    ('l2_leaf_reg', float),
    ('bagging_temperature', float),
    ('subsample', float),
    ('random_strength', float),
    ('depth', int),
    ('min_data_in_leaf', int),
    ('rsm', float),
]


def main(**args):
    titanic_train, _ = titanic()
    titanic_train.fillna(-999, inplace=True)
    cols = [
        'Pclass',
        'Name',
        'Sex',
        'Age',
        'SibSp',
        'Parch',
        'Ticket',
        'Fare',
        'Cabin',
        'Embarked'
    ]
    train_sz = int(titanic_train.shape[0] * 0.1)
    x_train = titanic_train[:train_sz][cols]
    y_train = titanic_train[:train_sz]['Survived'].astype(int)
    x_test = titanic_train[train_sz:][cols]
    y_test = titanic_train[train_sz:]['Survived'].astype(int)
    try:
        model = CatBoostClassifier(random_seed=42, **args)
        model.fit(x_train, y_train, [1, 2, 6, 8, 9], silent=True)
        accuracy = model.score(x_test, y_test)
        print(-accuracy)
    except:
        print(0)


if __name__ == '__main__':
    args = dict()
    for var, var_type in vars:
        args[var] = var_type(input())
    main(**args)