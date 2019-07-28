import numpy as np
import pandas as pd

from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

from sklearn.linear_model import LinearRegression
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor

from sklearn.metrics import mean_squared_error

def getData():
    statsDa = pd.read_csv("stats/statsDa.csv")
    census = pd.read_csv("data/census/1AuriNtO1RDRT_data.csv")
    canale = pd.read_csv("data/canale/CanALE_2016.csv")

    data = statsDa.merge(census, how="left", left_on="da", right_on="COL0")
    data = data.merge(canale, how="left", left_on="da", right_on="dauid")

    data.rename(index=str, columns={"COL2": "population density", "COL4": "average age", "COL5": "median income"}, inplace=True)
    
    data["% non-immigrants"] = data["COL6"]/data["COL1"]
    data["% not a visible minority"] = data["COL7"]/data["COL1"]
    data["% postsecondary"] = data["COL9"]/data["COL1"]
    data.drop(columns=["COL0", "dauid", "COL1", "COL3", "COL6", "COL7", "COL8", "COL9"], inplace=True)

    data.replace(".", np.nan, inplace=True)

    tagNaics = pd.read_csv("resources/tagNaics.tsv", sep='\t')
    data["naics"] = data["naics"].astype(str)
    data = data.merge(tagNaics, how="left", left_on="naics", right_on="2012 NAICS US Code").drop(columns=["Seq. No.", "2012 NAICS US Code", "OSM tags"])
    
    return data

def trainModel(data, naics, industry):
    dataNaics = data[(data["naics"] == naics)]
    dataNaics.drop(["da", "naics", "countOsm", "countStatcan", "2012 NAICS US Title"], axis=1, inplace=True)

    dataNaics = dataNaics[~dataNaics.isin([np.nan, np.inf, -np.inf]).any(1)]

    minMaxScaler = MinMaxScaler()
    xNormalized = minMaxScaler.fit_transform(dataNaics.loc[:, dataNaics.columns != "osmCompleteness"])
    yNormalized = minMaxScaler.fit_transform(dataNaics["osmCompleteness"].values.reshape(-1, 1))

    XTrain, XTest, yTrain, yTest = train_test_split(xNormalized, yNormalized, test_size=0.33, random_state=42)

    reg = LinearRegression()
    reg.fit(XTrain, yTrain)

    print("industry: ", industry)
    print(" MSE: ", mean_squared_error(yTest, reg.predict(XTest)))
    print(" MSE for y = {}: ".format(np.mean(yTrain)), mean_squared_error(yTest, [np.mean(yTrain)] * len(yTest)))

def main():
    data = getData()
    data.to_csv("data/data.csv")
    trainModel(data, "722511", "restaurant")

if __name__ == "__main__":
    main()
