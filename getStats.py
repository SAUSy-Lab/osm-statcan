import pandas as pd
import shapefile
import configparser
import psycopg2
import os
class GetStats(object):
    def __init__(self):
        cmasSf = shapefile.Reader("resources/boundaries/cmas4326/cmas4326.shp")
        self.cmas = {shapeRecord.record.CMAUID: set() for shapeRecord in cmasSf.shapeRecords()}

        dasSf = shapefile.Reader("resources/boundaries/das4326/das4326.shp")
        self.das = [shapeRecord.record.DAUID for shapeRecord in dasSf.shapeRecords()]

        for shapeRecord in dasSf.shapeRecords():
            if shapeRecord.record.CMAUID in self.cmas:
                self.cmas[shapeRecord.record.CMAUID].add(shapeRecord.record.DAUID)

        config = configparser.ConfigParser()
        config.read("config/config.ini")
        self.conn = psycopg2.connect(
            host=config["credentials"]["host"],
            database=config["credentials"]["database"],
            user=config["credentials"]["user"],
            password=config["credentials"]["password"],
        )

        self.bcStatcan = pd.read_csv("data/statcan/bc.csv", index_col=0, dtype=int)
    
    def getBcOsm(self, cma=None, da=None):
        if cma:
            sql = """select "naicsCan" as naics, count(*) as "countOsm" from businesses
            where cma = {0} and "naicsCan" != -1
            group by "naicsCan\"""".format(cma)
        elif da:
            sql = """select "naicsCan" as naics, count(*) as "countOsm" from businesses
            where da = {0} and "naicsCan" != -1
            group by "naicsCan\"""".format(da)
        
        return pd.read_sql(sql, con=self.conn, index_col="naics")
    
    def getBcStatcan(self, cma=None, da=None):
        if cma:
            return self.bcStatcan[self.bcStatcan.columns.intersection(self.cmas[cma])].sum(1)
        elif da:
            return self.bcStatcan[da] if da in self.bcStatcan else pd.DataFrame()

    def getStatsLocal(self, cma=None, da=None):
        def getCountStatcan(row, bcStatcanLocal):
            length = 6 - len(str(row.name))
            return bcStatcanLocal[bcStatcanLocal.index.astype(str).str.contains("^" + str(row.name) + "([0-9]){" + str(length) + "}$")].sum()

        if cma:
            bcOsmLocal = self.getBcOsm(cma=cma)
            bcStatcanLocal = self.getBcStatcan(cma=cma)
        elif da:
            bcOsmLocal = self.getBcOsm(da=da)
            bcStatcanLocal = self.getBcStatcan(da=da)
        
        if not bcOsmLocal.empty and not bcStatcanLocal.empty:
            statsLocal = bcOsmLocal
            statsLocal["countStatcan"] = statsLocal.apply(getCountStatcan, axis=1, args=(bcStatcanLocal,))
            statsLocal["osmCompleteness"] = statsLocal["countOsm"] / statsLocal["countStatcan"]
            statsLocal["error"] = abs(statsLocal["countStatcan"] - statsLocal["countOsm"]) / statsLocal["countStatcan"]

            boundary = cma if cma else da
            boundaryType = "cma" if cma else "da"
            statsLocal.index = pd.MultiIndex.from_tuples([[boundary, k] for k, v in statsLocal.iterrows()], names=[boundaryType, "naics"])

            return statsLocal

    def getStats(self, type):
        if type == "cma":
            stats = [self.getStatsLocal(cma=cma) for cma in self.cmas]
        elif type == "da":
            stats = [self.getStatsLocal(da=da) for da in self.das]
        
        stats = list(filter(lambda x: x is not None, stats))

        return pd.concat(stats)

def main():
    getStats = GetStats()
    statsCma = getStats.getStats("cma")
    statsCma.to_csv("stats/statsCma.csv")
    statsDa = getStats.getStats("da")
    statsDa.to_csv("stats/statsDa.csv")

if __name__ == "__main__":
    main()
