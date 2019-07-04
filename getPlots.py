from getModels import getData

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def rand_jitter(arr):
    stdev = .01*(max(arr)-min(arr))
    return arr + np.random.randn(len(arr)) * stdev

def printDistribution(data, naics=None, col=None):
    if naics:
        data = data[(data["naics"] == naics) & (data["countStatcan"] > 0)]
        distPlot = sns.distplot(data["osmCompleteness"])
    elif col:
        data = data[col]
        data.replace([np.inf, -np.inf], np.nan, inplace=True)
        data = data.dropna()
        distPlot = sns.distplot(data)

    plt.show()

def printScatter(data, naics, col):
    data = data[(data["naics"] == naics) & (data["countStatcan"] > 0)]
    data["osmCompleteness"] = rand_jitter(data["osmCompleteness"])
    relPlot = sns.relplot(col, "osmCompleteness", size="countStatcan", data=data, alpha=0.5)
    plt.show()

def main():
    data = getData()
    # printDistribution(data, naics=44511)
    # printDistribution(data, col="COL1")
    printScatter(data, naics=44511, col="COL6")

if __name__ == "__main__":
    main()
