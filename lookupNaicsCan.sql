update businesses
set "naicsCan" = can
from "usCan"
where us = naics

update businesses
set "naicsCan" = naics
where "naicsCan" is null
