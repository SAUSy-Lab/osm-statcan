select UpdateGeometrySRID('public', 'das', 'geom', 4326) ;
  
ALTER TABLE planet_osm_line
ALTER COLUMN way
TYPE Geometry(LineString, 4326) 
USING ST_Transform(way, 4326);

ALTER TABLE planet_osm_point
ALTER COLUMN way
TYPE Geometry(Point, 4326) 
USING ST_Transform(way, 4326);

ALTER TABLE planet_osm_polygon
ALTER COLUMN way
TYPE Geometry(Polygon, 4326) 
USING ST_Transform(way, 4326);

create table lookupDa as
select osm_id, dauid from planet_osm_line
join das
on ST_Intersects(way, geom)
union
select osm_id, dauid from planet_osm_point
join das
on ST_Intersects(way, geom)
union
select osm_id, dauid from planet_osm_polygon
join das
on ST_Intersects(way, geom)

UPDATE businesses
SET da = cast(dauid as integer)
FROM lookupDa
WHERE id=osm_id
