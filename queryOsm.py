import pandas as pd
import shapefile
import configparser
import psycopg2
import regex
import overpass

from collections import OrderedDict

class QueryOsm(object):
    def __init__(self):
        cmasSf = shapefile.Reader("resources/boundaries/cmas4326/cmas4326.shp")
        self.cmas = {
            shapeRecord.record.CMAUID : " ".join("{} {}".format(point[1], point[0])
                                                for point in shapeRecord.shape.points)
            for shapeRecord in cmasSf.shapeRecords()
        }
        self.cmas = OrderedDict(sorted(self.cmas.items(), key=lambda t: t[0]))

        self.tagNaics = pd.read_csv("resources/tagNaics.tsv", sep='\t')
        self.tagNaics.dropna(subset=["OSM tags"], inplace=True)

        self.api = overpass.API(endpoint="https://lz4.overpass-api.de/api/interpreter", timeout=3600)
        self.setId = 0

        config = configparser.ConfigParser()
        config.read("config/config.ini")
        self.conn = psycopg2.connect(
            host=config["credentials"]["host"],
            database=config["credentials"]["database"],
            user=config["credentials"]["user"],
            password=config["credentials"]["password"],
        )

    def __del__(self):
        self.conn.close()

    def queryOsm(self):
        for cma in list(self.cmas.keys()):
            self.queryCma(cma)

    def queryCma(self, cma):
        self.tagNaics.apply(self.queryNaics, axis=1, args=[cma])

    def queryNaics(self, row, cma):
        query = self.getQl(row["OSM tags"], poly=self.cmas[cma], recurse=False)[0]
        queryRecurse = self.getQl(row["OSM tags"], poly=self.cmas[cma], recurse=True)[0]

        try:
            responseGeojson = self.api.get(query)
        except:
            print("Failed geojson query for cma: {0} and naics: {1}".format(cma, row["2012 NAICS US Code"]))
            return

        sql = """INSERT INTO public.businesses(id, cma, naics)
        VALUES(%s, %s, %s);"""
        cur = self.conn.cursor()
        for feature in responseGeojson["features"]:
            try:
                cur.execute(sql, (feature['id'], str(cma), row["2012 NAICS US Code"]))
            except:
                print("Failed INSERT for id: {0}, cma: {1}, and naics: {2}".format(feature['id'], cma, row["2012 NAICS US Code"]))
        self.conn.commit()
        cur.close()

        try:
            responseXml = self.api.get(queryRecurse, responseformat="xml")
        except:
            print("Failed xml query for cma: {0} and naics: {1}".format(cma, row["2012 NAICS US Code"]))
            return

        if responseGeojson["features"]:
            with open("data/osm/{0}_{1}.osm".format(str(cma), row["2012 NAICS US Code"]), mode="w", encoding="utf-8") as f:
                f.write(responseXml)

    def getQl(self, turbo, poly, recurse, out=True):
        if '(' in turbo:
            nestedTurbo = regex.findall('\(((?>[^()]|(?R))*)\)', turbo)[0]
            nestedQl, nestedSetId = self.getQl(nestedTurbo, poly=poly, recurse=recurse, out=False)

            turbo = regex.sub("\(((?>[^()]|(?R))*)\)", str(nestedSetId), turbo)

        def getQlTurboTag(turboTag):
            if turboTag.isdigit():
                return "\n\tnode{0};\n\tway{0};\n".format(".i" + str(turboTag))

            operator = "!=" if "!=" in turboTag else "="
            kv = turboTag.split(operator)
            if kv[1] == "*":
                return  '\n\tnode["{0}"]({1});\n\tway["{0}"]({1});\n'.format(kv[0], 'poly:"' + poly + '"')
            else:
                return '\n\tnode["{0}"{1}"{2}"]({3});\n\tway["{0}"{1}"{2}"]({3});\n'.format(kv[0], operator, kv[1], 'poly:"' + poly + '"')

        turbo = turbo.replace(" OR ", "||").replace(" ", "&&")

        ql = ""
        setIds = []

        for turboSet in turbo.split("&&"):
            # union
            ql += '(' + "".join(getQlTurboTag(turboTag) for turboTag in turboSet.split("||")) + ")" + "->{};\n".format(".u" + str(self.setId))
            setIds.append(".u" + str(self.setId))

            self.setId += 1

        # intersect
        ql += "(node{0};\nway{0};\n)->{1};\n".format("".join(setIds), ".i" + str(self.setId))
        
        if out:
            if recurse:
                ql += "({0};>;)->{0};\n".format(".i" + str(self.setId))
            ql += "{} out;\n".format(".i" + str(self.setId))

        self.setId += 1

        try:
            return nestedQl + ql, self.setId - 1
        except:
            return ql, self.setId - 1

def main():
    queryOsm = QueryOsm()
    queryOsm.queryOsm()

if __name__ == "__main__":
    main()
