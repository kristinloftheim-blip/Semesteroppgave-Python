import numpy as np
import pandas as pd
from pandas import DataFrame
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge, RidgeCV
from sklearn.metrics import r2_score, mean_absolute_error

def build_and_train_model():
    global model
    df:DataFrame = pd.read_csv("House_Prices.csv")

    # --- Load your data ---
    Y = df["sales_price"].values
    X = df[y_columns]
    X["x2"] = X["x"] ** 1.5
    X["y2"] = X["y"] ** 1.5

    # --- Polynomial expansion ---
    X_poly = poly.fit_transform(X)
    x_train, x_test, y_train, y_test = train_test_split(X_poly, Y, test_size=0.25, random_state=42)

    model.fit(x_train, y_train)
    y_pred = model.predict(x_test).astype(int)

    # Check model quality
    l_test:list[int] = y_test.tolist()
    l_pred:list[int] = y_pred.tolist()
    for i in range(0, min(len(l_test),10)):
        print(f"Price: {l_test[i]:>10,.0f}  Predicted: {l_pred[i]:>10,.0f}")
    print(f"R-squared: {r2_score(y_test, y_pred):.2f}")
    print(f"MAE      : {mean_absolute_error(y_test, y_pred):.0f}")

def predict_price(x, y, m2:int,house_type, standard) -> float:
    # Build a single sample
    x_house = pd.DataFrame([[x, y,m2,house_type,standard]],columns=y_columns)
    x_house['x2'] = x_house['x']**1.5 # Weith position more.
    x_house['y2'] = x_house['y']**1.5
    x_poly = poly.transform(x_house)
    pred = model.predict(x_poly)[0]
    return float(pred)


y_columns=["x","y","m2","house_type","standard"]
p_degree = 3
model = LinearRegression()

poly = PolynomialFeatures(degree=p_degree)
build_and_train_model()

print(f"m2  {predict_price(100,100, 200,1, 1)}") # just test one..
