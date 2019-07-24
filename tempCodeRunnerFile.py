import pandas as pd
import configparser
import psycopg2
import re

class QueryOsm(object):
    def __init__(self):
        self.tagNaics = pd.read_csv("resources/tagNaics.tsv", sep='\t')
        self.tagNaics.dropna(subset=["OSM tags"], inplace=True)

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
        self.tagNaics.apply(self.queryNaics, axis=1)

    def queryNaics(self, row):
        naics = row["2012 NAICS US Code"]
        tags = row["OSM tags"]
        tags = tags.replace(" OR ", "||")
        tags = tags.replace(" ", "&&")
        tags = tags.replace("||", " OR ")
        tags = tags.replace("&&", " AND ")
        tags = re.sub(r"([A-Za-z0-9_]*)=([A-Za-z0-9_]*)", r"\1='\2'", tags)

        sql = """
        INSERT into businesses
        SELECT osm_id, dauid, {0} as naics FROM (
            SELECT osm_id, way FROM planet_osm_point
            WHERE {1}
            UNION
            SELECT osm_id, way FROM planet_osm_line
            WHERE {1}
            UNION
            SELECT osm_id, way FROM planet_osm_polygon
            WHERE {1}
        ) table0
        JOIN das
        ON ST_WITHIN(way, geom)
        """.format(naics, tags)

        cur = self.conn.cursor()
        try:
            cur.execute(sql)
        except Exception as e:
            print(e)
        self.conn.commit()
        cur.close()

def main():
    queryOsm = QueryOsm()
    queryOsm.queryOsm()

if __name__ == "__main__":
    main()
