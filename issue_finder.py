query_1 = """
-- check bedrooms_gt_20, bedrooms_eq_12, missing_bedrooms
INSERT OR IGNORE INTO sourcelabels (url, label)
SELECT
	p1.url,
	CASE
		WHEN p2.target IS NULL OR p2.target == 0 THEN 'has_missing_bedrooms'
		WHEN p2.target >= 20 THEN 'bedrooms_gt_20'
	END
FROM properties p1
JOIN (
	SELECT url, MAX(bedrooms) AS target FROM properties
	WHERE is_available = 1
	AND url NOT IN (SELECT url FROM source WHERE is_excluded='true')
	GROUP BY url
) p2 ON p1.url = p2.url
WHERE p2.target IS NULL OR p2.target == 0
OR p2.target >= 20
OR p2.target == 12
GROUP BY p1.url;
"""

query_2 = """
-- check has_missing_bathrooms
INSERT OR IGNORE INTO sourcelabels (url, label)
SELECT
	p1.url,
	CASE
		WHEN p2.target IS NULL OR p2.target == 0 THEN 'has_missing_bathrooms'
		WHEN p2.target >= 20 THEN 'bathrooms_gt_20'
	END
FROM properties p1
JOIN (
	SELECT url, MAX(bathrooms) AS target FROM properties
	WHERE is_available = 1
	AND url NOT IN (SELECT url FROM source WHERE is_excluded='true')
	GROUP BY url
) p2 ON p1.url = p2.url
WHERE p2.target IS NULL OR p2.target == 0
OR p2.target >= 20
GROUP BY p1.url;
"""

query_3 = """
-- check has_missing_contract_type
INSERT OR IGNORE INTO sourcelabels (url, label)
SELECT p1.url, 'has_missing_contract_type'
FROM properties p1
JOIN (
	SELECT url, MAX(contract_type) AS target FROM properties
	WHERE is_available = 1
	AND url NOT IN (SELECT url FROM source WHERE is_excluded='true')
	GROUP BY url
) p2 ON p1.url = p2.url
WHERE p2.target IS NULL
GROUP BY p1.url;
"""

query_4 = """
-- check has_missing_price
INSERT OR IGNORE INTO sourcelabels (url, label)
SELECT p1.url, 'has_missing_price'
FROM properties p1
JOIN (
	SELECT url, MAX(price) AS target FROM properties
	WHERE is_available = 1
	AND url NOT IN (SELECT url FROM source WHERE is_excluded='true')
	GROUP BY url
) p2 ON p1.url = p2.url
WHERE p2.target IS NULL OR p2.target == 0
GROUP BY p1.url;
"""

query_5 = """
-- check has_missing_leasehold_years
INSERT OR IGNORE INTO sourcelabels (url, label)
SELECT p1.url, 'has_missing_leasehold_years'
FROM properties p1
JOIN (
	SELECT url, MAX(leasehold_years) AS target FROM properties
	WHERE is_available = 1
	AND url NOT IN (SELECT url FROM source WHERE is_excluded='true')
    AND contract_type = 'Leasehold'
	GROUP BY url
) p2 ON p1.url = p2.url
WHERE p2.target IS NULL OR p2.target == 0
GROUP BY p1.url;
"""

query_6 = """
-- check has_missing_land_size
INSERT OR IGNORE INTO sourcelabels (url, label)
SELECT p1.url, 'has_missing_land_size'
FROM properties p1
JOIN (
	SELECT url, MAX(land_size) AS target FROM properties
	WHERE is_available = 1
	AND url NOT IN (SELECT url FROM source WHERE is_excluded='true')
	GROUP BY url
) p2 ON p1.url = p2.url
WHERE p2.target IS NULL OR p2.target == 0
GROUP BY p1.url;
"""

query_7 = """
-- check has_missing_build_size
INSERT OR IGNORE INTO sourcelabels (url, label)
SELECT p1.url, 'has_missing_build_size'
FROM properties p1
JOIN (
	SELECT url, MAX(build_size) AS target FROM properties
	WHERE is_available = 1
	AND url NOT IN (SELECT url FROM source WHERE is_excluded='true')
	GROUP BY url
) p2 ON p1.url = p2.url
WHERE p2.target IS NULL OR p2.target == 0
GROUP BY p1.url;
"""

query_8 = """
-- check has_missing_location
INSERT OR IGNORE INTO sourcelabels (url, label)
SELECT p1.url, 'has_missing_location'
FROM properties p1
JOIN (
	SELECT url, MAX(location) AS target FROM properties
	WHERE is_available = 1
	AND url NOT IN (SELECT url FROM source WHERE is_excluded='true')
	GROUP BY url
) p2 ON p1.url = p2.url
WHERE p2.target IS NULL
GROUP BY p1.url;
"""

queries = [
    query_1,
    query_2,
    query_3,
    query_4,
    query_5,
    query_6,
    query_7,
    query_8,
]
