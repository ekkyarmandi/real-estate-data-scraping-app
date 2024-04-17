from math import ceil
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from api.func import get_statistics, identify_issue, join_strings

# from api.path_utils import RequestPathExtension
from api.settings import PAGE_SIZE
from database import Database
from datetime import datetime
from api.queries import *
from api.routers import apis, dashboard
from libs.googlespreadsheet import SpreadSheetPipeline

app = FastAPI()

templates = Jinja2Templates(directory="./api/templates")

app.mount("/api/templates", StaticFiles(directory="./api/templates"), name="static")
app.mount("/api/scripts", StaticFiles(directory="./api/scripts"), name="scripts")

# app.add_template_extension(RequestPathExtension)

app.include_router(apis.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1/dashboard")

# Register the custom filter function
templates.env.filters["separate"] = lambda n: "{:,d}".format(int(n))

COLUMNS = [
    "source",
    "created_at",
    "url",
    "image_url",
    "title",
    "description",
    "price",
    "currency",
    "contract_type",
    "property_type",
    "leasehold_years",
    "location",
    "bedrooms",
    "bathrooms",
    "land_size",
    "build_size",
    "is_available",
    "availability_text",
    "tab",
]


@app.get("/")
def home(request: Request):
    from libs.missing import count

    current_date = datetime.now().strftime(r"%Y-%m-%d")
    # query property types
    db = Database("database.db")
    # query properties
    properties = []
    for props in db.get_records(query_properties):
        properties.append({k: v for k, v in zip(COLUMNS, props)})
    # end

    urls = [i["url"] for i in properties]

    # count for missing properties
    missing_title = {
        "bedrooms_gt_20": "Has Bedrooms ≥ 20",
        "bathrooms_gt_20": "Has Bathrooms ≥ 20",
        "has_missing_bedrooms": "Has Missing Bedrooms",
        "has_missing_bathrooms": "Has Missing Bathrooms",
        "has_missing_contract_type": "Has Missing Contract Type",
        "has_incorect_contract_type": "Has Incorrect Contract Type",
        "has_missing_price": "Has Missing Price",
        "has_missing_leasehold_years": "Has Missing Leasehold Years",
        "has_missing_land_size": "Has Missing Land Size",
        "has_missing_build_size": "Has Missing Build Size",
        "has_missing_location": "Has Missing Location",
    }
    missing_attributes = [
        dict(
            path=key,
            name=name,
            count=count(key, urls),
        )
        for key, name in missing_title.items()
    ]

    # count for missing contract type and property type
    property_types = {}
    contract_types = {}
    for p in properties:
        # count for property types
        pt = p["property_type"]
        ct = p["contract_type"]
        if pt not in property_types:
            property_types[pt] = 1
        elif pt in property_types:
            property_types[pt] += 1
        # count for contract types
        if ct not in contract_types:
            contract_types[ct] = 1
        elif ct in contract_types:
            contract_types[ct] += 1
    contract_types = [dict(name=k, count=v) for k, v in contract_types.items()]
    property_types = [dict(name=k, count=v) for k, v in property_types.items()]

    # count for already exlcuded
    urls = []
    for p in properties:
        urls.append(p["url"])
    urls_as_string = ",".join(["'{}'".format(u) for u in urls])
    query = f"""
    SELECT COUNT(*) FROM source
    WHERE is_excluded = 'true'
    AND url IN ({urls_as_string});
    """
    total_excluded = db.get_first(query)
    # count new value
    query = f"""
    SELECT COUNT(*) FROM source
    WHERE scraped_at = '03/01/24';
    """
    total_new = db.get_first(query)

    context = dict(
        request=request,
        current_date=current_date,
        total_property=len(properties),
        excluded=dict(
            total=total_excluded,
            perc=100 * total_excluded / len(properties),
        ),
        new=dict(
            total=total_new,
            perc=100 * total_new / len(properties),
        ),
        property_types=property_types,
        contract_types=contract_types,
        missing_attributes=missing_attributes,
        stats=get_statistics(properties),
    )

    # trigger issue identifier
    identify_issue()

    return templates.TemplateResponse("index.html", context)


@app.get("/spreadsheet-urls")
def missing_urls(request: Request, urls=[]):
    """
    Show the missing URLs in the data table
    compare to the spreadsheet Property Link columns
    """
    # db = Database("database.db")
    # tabs = ["DATA", "LUXURY LISTINGS"]
    # urls = []
    # for tab in tabs:
    #     gs = SpreadSheetPipeline(
    #         spreadsheet_name="Q1_FEBRUARY_Working",
    #         credential="creds.json",
    #         sheet=tab,
    #     )
    #     df = gs.to_dataframe()
    #     urls.extend(df["Property Link"].to_list())
    # urls_as_string = ",".join(["'{}'".format(u) for u in urls])
    # query = f"""
    # SELECT p1.url FROM properties p1
    # JOIN (
    #     SELECT url, MAX(created_at) AS max_date FROM properties
    #     GROUP BY url, created_at ORDER BY created_at DESC
    # ) p2 ON p1.url = p2.url AND p1.created_at = p2.max_date
    # WHERE p1.url NOT IN ({urls_as_string})
    # AND p2.max_date >= '2024-03-01';
    # """
    # urls = db.fetchall(query)
    urls = list(map(str.strip, urls.split(",")))
    context = dict(
        request=request,
        title="Missing URLs in the Data Table (Unscraped)",
        properties=[],
        urls=urls,
        count=len(urls),
    )
    return templates.TemplateResponse("missing_urls_only.html", context)


@app.get("/missing/{key:path}")
def missing(request: Request, key: str, page: int = 1):
    # initialize the database object
    db = Database()

    # query the urls with issue
    query = f"""
    SELECT url FROM sourcelabels
    WHERE label='{key}' AND is_verified=0;
    """

    urls_of_missings = db.fetchall(query)
    urls_as_string = join_strings(urls_of_missings)
    print("total urls:", len(urls_of_missings))

    # count total missings
    query = f"""
    SELECT COUNT(DISTINCT url) FROM properties
    WHERE created_at >= '2024-03-01'
    AND url IN ({urls_as_string});
    """
    total_missings = db.get_first(query)
    print("total missings:", total_missings)

    # query properties based on urls of missing
    query = f"""
    SELECT DISTINCT url FROM properties
    WHERE created_at >= '2024-03-01'
    AND url IN ({urls_as_string})
    """
    offset = 0
    if page == 1:
        query += "LIMIT {};".format(PAGE_SIZE)
    elif page > 1:
        offset = (page - 1) * PAGE_SIZE
        query += "LIMIT {} OFFSET {};".format(PAGE_SIZE, offset)
    urls = db.fetchall(query)
    properties = []
    for url in urls:
        p = db.get_record(query_item.format(url))
        p = {k: v for k, v in zip(COLUMNS, p)}
        p["labels"] = db.fetchall(
            f"SELECT DISTINCT label FROM sourcelabels WHERE url='{url}' AND is_verified=0;"
        )
        properties.append(p)
    print("total properties:", len(properties))

    missing_title = {
        "bedrooms_gt_20": "Has Bedrooms ≥ 20",
        "bathrooms_gt_20": "Has Bathrooms ≥ 20",
        "has_missing_bedrooms": "Has Missing Bedrooms",
        "has_missing_bathrooms": "Has Missing Bathrooms",
        "has_missing_contract_type": "Has Missing Contract Type",
        "has_incorect_contract_type": "Has Incorrect Contract Type",
        "has_missing_price": "Has Missing Price",
        "has_missing_leasehold_years": "Has Missing Leasehold Years",
        "has_missing_land_size": "Has Missing Land Size",
        "has_missing_build_size": "Has Missing Build Size",
        "has_missing_location": "Has Missing Location",
    }

    context = dict(
        request=request,
        title=missing_title[key],
        properties=properties,
        total_missings=total_missings,
        current_total=offset + len(properties),
        current_page=page,
        max_page=ceil(total_missings / PAGE_SIZE),
    )
    return templates.TemplateResponse("detail.html", context)


@app.get("/contract-type/")
def contract_type(request: Request, value: str):
    # query the properties url
    query = f"""
    SELECT p1.url FROM properties p1
    JOIN (
        SELECT url, MAX(created_at) AS max_date FROM properties
        GROUP BY url, created_at ORDER BY created_at DESC
    ) p2 ON p1.url = p2.url AND p1.created_at = p2.max_date
    WHERE created_at >= '2024-03-01'
    AND contract_type = '{value}';
    """
    db = Database("database.db")
    urls = db.fetchall(query)
    #
    context = dict(
        request=request,
        sub_title=value,
        urls=urls,
    )
    return templates.TemplateResponse("category/contract.html", context)


@app.get("/property-type/")
def contract_type(request: Request, value: str):
    # query the properties url
    query = f"""
    SELECT p1.url FROM properties p1
    JOIN (
        SELECT url, MAX(created_at) AS max_date FROM properties
        GROUP BY url, created_at ORDER BY created_at DESC
    ) p2 ON p1.url = p2.url AND p1.created_at = p2.max_date
    WHERE created_at >= '2024-03-01'
    AND property_type = '{value}';
    """
    db = Database("database.db")
    urls = db.fetchall(query)
    #
    properties = []
    for url in urls:
        prop = db.get_record(query_item.format(url))
        prop = {k: v for k, v in zip(COLUMNS, prop)}
        # get url issue labels
        properties.append(prop)

    context = dict(
        request=request,
        sub_title=value,
        properties=properties,
        urls=urls,
    )
    return templates.TemplateResponse("category/property.html", context)


@app.get("/max-listing")
def max_listing(request: Request):
    # query properties
    properties = []
    db = Database()
    for props in db.get_records(query_properties):
        properties.append({k: v for k, v in zip(COLUMNS, props)})
    stats = get_statistics(properties)
    # IDR	USD	Bedrooms	Bathrooms	Land Size	Build Size	Leasehold Years
    urls = []
    for i, value in enumerate(stats["q3"]):
        match i:
            case 0:
                print("IDR")
                query = f"""
                SELECT p1.url FROM properties p1
                JOIN (
                    SELECT url, MAX(created_at) AS max_date FROM properties
                    GROUP BY url, created_at ORDER BY created_at DESC
                ) p2 ON p1.url = p2.url AND p1.created_at = p2.max_date
                WHERE p1.created_at >= '2024-03-01'
                AND p1.url NOT IN (SELECT url FROM source WHERE is_excluded='true')
                AND currency = 'IDR'
                AND price > {value};
                """
                urls.extend(db.fetchall(query))
            case 1:
                print("USD")
                query = f"""
                SELECT p1.url FROM properties p1
                JOIN (
                    SELECT url, MAX(created_at) AS max_date FROM properties
                    GROUP BY url, created_at ORDER BY created_at DESC
                ) p2 ON p1.url = p2.url AND p1.created_at = p2.max_date
                WHERE p1.created_at >= '2024-03-01'
                AND p1.url NOT IN (SELECT url FROM source WHERE is_excluded='true')
                AND currency = 'USD'
                AND price > {value};
                """
                urls.extend(db.fetchall(query))
            case 2:
                print("Bedrooms")
                query = f"""
                SELECT p1.url FROM properties p1
                JOIN (
                    SELECT url, MAX(created_at) AS max_date FROM properties
                    GROUP BY url, created_at ORDER BY created_at DESC
                ) p2 ON p1.url = p2.url AND p1.created_at = p2.max_date
                WHERE p1.created_at >= '2024-03-01'
                AND p1.url NOT IN (SELECT url FROM source WHERE is_excluded='true')
                AND bedrooms > {value};
                """
                urls.extend(db.fetchall(query))
            case 3:
                print("Bathrooms")
                query = f"""
                SELECT p1.url FROM properties p1
                JOIN (
                    SELECT url, MAX(created_at) AS max_date FROM properties
                    GROUP BY url, created_at ORDER BY created_at DESC
                ) p2 ON p1.url = p2.url AND p1.created_at = p2.max_date
                WHERE p1.created_at >= '2024-03-01'
                AND p1.url NOT IN (SELECT url FROM source WHERE is_excluded='true')
                AND bathrooms > {value};
                """
                urls.extend(db.fetchall(query))
            case 4:
                print("Land Size")
                query = f"""
                SELECT p1.url FROM properties p1
                JOIN (
                    SELECT url, MAX(created_at) AS max_date FROM properties
                    GROUP BY url, created_at ORDER BY created_at DESC
                ) p2 ON p1.url = p2.url AND p1.created_at = p2.max_date
                WHERE p1.created_at >= '2024-03-01'
                AND p1.url NOT IN (SELECT url FROM source WHERE is_excluded='true')
                AND land_size > {value};
                """
                urls.extend(db.fetchall(query))
            case 5:
                print("Build Size")
                query = f"""
                SELECT p1.url FROM properties p1
                JOIN (
                    SELECT url, MAX(created_at) AS max_date FROM properties
                    GROUP BY url, created_at ORDER BY created_at DESC
                ) p2 ON p1.url = p2.url AND p1.created_at = p2.max_date
                WHERE p1.created_at >= '2024-03-01'
                AND p1.url NOT IN (SELECT url FROM source WHERE is_excluded='true')
                AND build_size > {value};
                """
                urls.extend(db.fetchall(query))
            case 6:
                print("Leasehold Years")
                query = f"""
                SELECT p1.url FROM properties p1
                JOIN (
                    SELECT url, MAX(created_at) AS max_date FROM properties
                    GROUP BY url, created_at ORDER BY created_at DESC
                ) p2 ON p1.url = p2.url AND p1.created_at = p2.max_date
                WHERE p1.created_at >= '2024-03-01'
                AND p1.url NOT IN (SELECT url FROM source WHERE is_excluded='true')
                AND leasehold_years > {value};
                """
                urls.extend(db.fetchall(query))
    urls_as_string = ",".join(["'{}'".format(u) for u in urls])
    query = f"""
    SELECT 
        source,
        created_at,
        p1.url,
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
    FROM properties p1
    JOIN (
        SELECT url, MAX(created_at) AS max_date FROM properties
        GROUP BY url, created_at ORDER BY created_at DESC
    ) p2 ON p1.url = p2.url AND p1.created_at = p2.max_date
    WHERE p1.created_at >= '2024-03-01'
    AND p1.url IN ({urls_as_string})
    GROUP BY p1.url;
    """
    q3_properties = []
    for p in db.get_records(query):
        q3_properties.append({k: v for k, v in zip(COLUMNS, p)})
    print(len(q3_properties))
    context = dict(
        request=request,
        properties=q3_properties,
    )
    return templates.TemplateResponse("outlier.html", context)


@app.get("/dashboard")
def dashboard(request: Request):
    import json

    db = Database()
    exclusions = db.fetchall(
        "SELECT DISTINCT excluded_by FROM source WHERE excluded_by != '';"
    )
    context = dict(
        request=request,
        exclusions=exclusions,
    )
    return templates.TemplateResponse("dashboard.html", context)
