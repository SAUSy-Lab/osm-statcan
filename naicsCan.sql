UPDATE businesses
SET "naicsCan" = can
FROM "usCan"
WHERE us = naics

UPDATE businesses
SET "naicsCan" = naics
WHERE "naicsCan" IS NULL
