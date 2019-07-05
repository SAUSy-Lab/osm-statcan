SELECT UpdateGeometrySRID('public', 'das', 'geom', 4326) ;

ALTER TABLE planet_osm_point
ALTER COLUMN way
TYPE Geometry(Point, 4326) 
USING ST_Transform(way, 4326);

ALTER TABLE planet_osm_line
ALTER COLUMN way
TYPE Geometry(LineString, 4326) 
USING ST_Transform(way, 4326);

ALTER TABLE planet_osm_polygon
ALTER COLUMN way
TYPE Geometry(Polygon, 4326) 
USING ST_Transform(way, 4326);
