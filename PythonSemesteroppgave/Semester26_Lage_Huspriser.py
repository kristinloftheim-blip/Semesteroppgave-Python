import math
import pandas as pd
import numpy as np



def faktor_distance(x1:int, y1:int, x2:int, y2:int) ->float:
    dist = np.sqrt((x1-x2)**2 + (y1-y2)**2)
    return math.exp(-dist*0.1)

def factor_position(x:int, y:int)->float:
    w = (1
         + 1.5 * faktor_distance(40, 58, x, y)  # Sentrum
         + 0.5 * faktor_distance(40, 20, x, y)  # Fana
         )
    return w

def factor_standard(standard:int)->float:
    return np.sqrt(standard)

def factor_small(m2):
    t = (m2 - 50) / (200 - 50)     # normalize 50→300 to 0→1
    t = np.clip(t, 0.5, 1)           # keep inside range
    return 1 - 0.5 * t             # linear inverse

def norm_price(m2:int)->float:
    factor = factor_small(m2)
    return m2 *  75.000 * factor

def factor_house_type(t:int)->float:
    if t==1:
        return 0.7
    if t==2:
        return 1.0
    if t==3:
        return 1.2
    return 1

def make_house_price(x:int, y:int, house_type:int, standard:int, m2:int)->float:
    price = (factor_position(x, y)
             *factor_house_type(house_type)
             *factor_standard(standard)
             *norm_price(m2))
    return price

np.random.seed(1234)
samples = 256
xs = np.random.randint(0, 100, samples)
ys = np.random.randint(0, 100, samples)
house_types = np.round(np.random.uniform(1, 4, samples)).astype(int)
standards = np.random.uniform(1.0, 4.0, samples)
m2s = np.random.randint(30, 250, samples)
sales_price = np.zeros(samples, dtype=int)
print(f" x0, y0 : {xs[0]}, {ys[0]}")
for i in range(samples) :
    sales_price[i] = make_house_price(xs[i], ys[i], house_types[i], standards[i], m2s[i]) * np.random.uniform(0.95, 1.05)

# DataFrame
df = pd.DataFrame({
    "x": xs,
    "y": ys,
    "m2": m2s,
    "house_type": house_types,
    "standard": np.round(standards, 1),
    "sales_price": sales_price
})

df.to_csv("House_Prices.csv", index=False)

# print(df.head())
print("CSV file 'House_Prices.csv' created successfully.")
print(f"Sentrum (leil, 100m2, god std) = {make_house_price(40, 58, 3, 3, 100):>10,.0f}") # Sentrum !
print(f"Åsane (leil, 100m2, god std)   = {make_house_price(40, 78, 3, 3, 100):>10,.0f}") # Sentrum !