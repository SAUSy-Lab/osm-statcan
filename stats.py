import pandas as pd
import shapefile
import configparser
import psycopg2

class Stats(object):
    def __init__(self):
        dasSf = shapefile.Reader("resources/boundaries/das4326/das4326.shp")
        self.das = [shapeRecord.record.DAUID for shapeRecord in dasSf.shapeRecords()]

        config = configparser.ConfigParser()
        config.read("config/config.ini")
        self.conn = psycopg2.connect(
            host=config["credentials"]["host"],
            database=config["credentials"]["database"],
            user=config["credentials"]["user"],
            password=config["credentials"]["password"],
        )

        self.bcStatcan = pd.read_csv("data/statcan/bc.csv", index_col=0, dtype=int)
    
    def getBcOsm(self, da):
        sql = """
        SELECT "naicsCan" AS naics, count(*) AS "countOsm" FROM businesses
        WHERE CAST(dauid AS INTEGER) = {0} AND "naicsCan" != -1
        GROUP BY "naicsCan"
        """.format(da)
        
        return pd.read_sql(sql, con=self.conn, index_col="naics")
    
    def getBcStatcan(self, da):
        return self.bcStatcan[da] if da in self.bcStatcan else pd.DataFrame()

    def getStatsLocal(self, da):
        def getCountStatcan(row, bcStatcanLocal):
            length = 6 - len(str(row.name))
            return bcStatcanLocal[bcStatcanLocal.index.astype(str).str.contains("^" + str(row.name) + "([0-9]){" + str(length) + "}$")].sum()   

        bcOsmLocal = self.getBcOsm(da=da)
        bcStatcanLocal = self.getBcStatcan(da=da)
        
        if not bcOsmLocal.empty and not bcStatcanLocal.empty:
            statsLocal = bcOsmLocal
            statsLocal["countStatcan"] = statsLocal.apply(getCountStatcan, axis=1, args=(bcStatcanLocal,))
            statsLocal["osmCompleteness"] = statsLocal["countOsm"] / statsLocal["countStatcan"]

            statsLocal.index = pd.MultiIndex.from_tuples([[da, k] for k, v in statsLocal.iterrows()], names=["da", "naics"])

            return statsLocal

    def getStats(self):
        stats = [self.getStatsLocal(da=da) for da in self.das]
        stats = list(filter(lambda x: x is not None, stats))

        return pd.concat(stats)

def main():
    getStats = Stats()
    statsCma = getStats.getStats()
    statsCma.to_csv("stats/statsDa.csv")

if __name__ == "__main__":
    main()
