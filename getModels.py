import numpy as np
import pandas as pd

from sklearn.base import TransformerMixin
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error

class DataFrameImputer(TransformerMixin):
    def fit(self, X, y=None):

        self.fill = pd.Series([X[c].value_counts().index[0]
            if X[c].dtype == np.dtype('O') else X[c].mean() for c in X],
            index=X.columns)

        return self

    def transform(self, X, y=None):
        return X.fillna(self.fill)

def getData():
    statsDa = pd.read_csv("stats/statsDa.csv")
    census = pd.read_csv("data/census/census.csv")
    canale = pd.read_csv("data/canale/CanALE_2016.csv")

    data = statsDa.merge(census, left_on="da", right_on="COL0")
    data = data.merge(canale, how="left", left_on="da", right_on="dauid")

    data = data[["naics", "countOsm", "countStatcan", "osmCompleteness", "ale_index", "COL1", "COL6", "COL74", "COL512", "COL708", "COL1057"]]
    
    data.rename(index=str, columns={"COL6": "population density", "COL74": "median income"}, inplace=True)
    data["% non-immigrants"] = data["COL512"]/data["COL1"]
    data["% not a visible minority"] = data["COL708"]/data["COL1"]
    data["% postsecondary"] = data["COL1057"]/data["COL1"]

    data.drop(columns=["COL1", "COL512", "COL708", "COL1057"], inplace=True)

    data.to_csv("data/data.csv")

    data.replace(".", np.nan, inplace=True)

    return data

def trainModels(naicss, data):
    imputer = DataFrameImputer()
    minMaxScaler = MinMaxScaler()
    reg = LinearRegression()
    # reg = ElasticNet()
    # reg = SVR(gamma='scale', C=1.0, epsilon=0.2)
    # reg = RandomForestRegressor(max_depth=5, random_state=0, n_estimators=100)

    for naics in naicss:
        dataNaics = data[(data["naics"] == naics) & (data["countStatcan"] > 0)]
        dataNaics.drop(["naics", "countStatcan", "countOsm"], axis=1, inplace=True)
        
        xImputed = imputer.fit_transform(dataNaics.loc[:, dataNaics.columns != "osmCompleteness"])
        xNormalized = minMaxScaler.fit_transform(xImputed)
        yNormalized = minMaxScaler.fit_transform(dataNaics["osmCompleteness"].values.reshape(-1, 1))

        XTrain, XTest, yTrain, yTest = train_test_split(xImputed, dataNaics["osmCompleteness"], test_size=0.33, random_state=42)

        reg.fit(XTrain, yTrain)

        print("industry: ", naicss[naics])
        print(" MSE: ", mean_squared_error(yTest, reg.predict(XTest)))
        print(" MSE for y = {}: ".format(np.mean(yTrain)), mean_squared_error(yTest, [np.mean(yTrain)] * len(yTest)))

def main():
    naicss = {
        44511: "Grocery Stores",
        44512: "Convenience Stores",
        44611: "Pharmacies",
        447: "Gas Stations",
        4481: "Clothing Stores",
        5221: "Bank",
        51912: "Libraries",
        6111: "Schools",
        6211: "Doctors",
        722511: "Restaurants",
        722512: "Fast Food",
        8131: "Religious Organizations",
        812114: "Barber Shops",
        812115: "Salons"
    }

    data = getData()
    trainModels(naicss, data)

if __name__ == "__main__":
    main()
