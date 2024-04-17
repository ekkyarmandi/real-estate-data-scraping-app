query_properties = """
SELECT
    p1.source,
    p1.created_at,
    p1.url,
    p1.image_url,
    p1.title,
    p1.description,
    p1.price,
    p1.currency,
    p1.contract_type,
    p1.property_type,
    p1.leasehold_years,
    p1.location,
    p1.bedrooms,
    p1.bathrooms,
    p1.land_size,
    p1.build_size,
    p1.is_available,
    p1.availability_text,
    p1.tab
FROM properties p1
JOIN (
    SELECT url, MAX(created_at) AS max_date FROM properties
    GROUP BY url, created_at ORDER BY created_at DESC
) p2 ON p1.url = p2.url AND p1.created_at = p2.max_date
WHERE p1.created_at >= '2024-03-01'
AND p1.url IN (
    SELECT url FROM source
    WHERE is_excluded = 'false'
)
AND contract_type != ''
AND property_type != '';
"""

query_missing_properties = """
SELECT
    p1.source,
    p1.created_at,
    p1.url,
    p1.image_url,
    p1.title,
    p1.description,
    p1.price,
    p1.currency,
    p1.contract_type,
    p1.property_type,
    p1.leasehold_years,
    p1.location,
    p1.bedrooms,
    p1.bathrooms,
    p1.land_size,
    p1.build_size,
    p1.is_available,
    p1.availability_text,
    p1.tab
FROM properties p1
JOIN (
    SELECT url, MAX(created_at) AS max_date FROM properties
    GROUP BY url, created_at ORDER BY created_at DESC
) p2 ON p1.url = p2.url AND p1.created_at = p2.max_date
WHERE p1.created_at >= '2024-03-01'
AND p1.url IN (
    SELECT url FROM source
    WHERE is_excluded = 'false'
)
AND p1.url IN ({})
AND contract_type != ''
AND property_type != '';
"""

query_item = """
SELECT
    source,
    created_at,
	url,
	FIRST_VALUE(image_url) OVER (PARTITION BY image_url) AS image_url,
    title,
	FIRST_VALUE(description) OVER (PARTITION BY description) AS description,
    MAX(price) AS price,
	FIRST_VALUE(currency) OVER (PARTITION BY currency) AS currency,
	FIRST_VALUE(contract_type) OVER (PARTITION BY contract_type) AS contract_type,
	FIRST_VALUE(property_type) OVER (PARTITION BY property_type) AS property_type,
    MAX(leasehold_years) AS leasehold_years,
	FIRST_VALUE(location) OVER (PARTITION BY location) AS location,
    MIN(bedrooms) AS bedrooms,
    MIN(bathrooms) AS bathrooms,
    MAX(land_size) AS land_size,
    MAX(build_size) AS build_size,
    is_available,
    availability_text,
    tab
FROM properties
WHERE url = '{}'
GROUP BY url;
"""

get_labels_query = """
SELECT DISTINCT label FROM sourcelabels
WHERE url = '{}' AND is_verified = 0;
"""
