from typing import Union
from fastapi import APIRouter, Response, Request
from api.func import identify_issue, join_strings
from libs.googlespreadsheet import SpreadSheetPipeline
from database import Database
from pydantic import BaseModel
from math import nan

router = APIRouter()


class QueryItem(BaseModel):
    column: str
    previous_value: str
    new_value: str


class PropertyItem(BaseModel):
    url: str
    # contract_type: str
    property_type: str
    location: str
    currency: str
    price: int
    bedrooms: Union[float, str]
    bathrooms: Union[float, str]
    land_size: Union[int, str]
    build_size: Union[int, str]
    tab: str


@router.get("/spreadsheet-urls")
async def check_spreadsheet(request: Request):
    db = Database("database.db")
    tabs = ["DATA", "LUXURY LISTINGS"]
    urls = []
    for tab in tabs:
        gs = SpreadSheetPipeline(
            spreadsheet_name="Q1_FEBRUARY_Working",
            credential="creds.json",
            sheet=tab,
        )
        df = gs.to_dataframe()
        urls.extend(df["Property Link"].to_list())
    query = f"""
    SELECT DISTINCT p1.url FROM properties p1 -- get unique urls from table properties
    JOIN (
        SELECT url, MAX(created_at) AS max_date FROM properties
        GROUP BY url, created_at ORDER BY created_at DESC
    ) p2 ON p1.url = p2.url AND p1.created_at = p2.max_date
    WHERE p2.max_date >= '2024-03-01';
    """
    results = db.fetchall(query)
    # compare the urls from the spreadsheet and the query
    missing_urls = []
    for url in urls:
        if url not in results:
            missing_urls.append(url)
    missing_urls = list(set(missing_urls))
    return {"urls": missing_urls, "count": len(missing_urls)}


@router.post("/update")
async def update_data(request: Request, item: QueryItem):
    item.column = item.column.replace("-", "_")
    print(item)
    query = f"""
    UPDATE properties SET {item.column} = '{item.new_value}'
    WHERE {item.column} = '{item.previous_value}';
    """
    db = Database("database.db")
    db.run(query)


@router.post("/edit")
async def update_data(request: Request, item: PropertyItem):
    item.bedrooms = item.bedrooms if item.bedrooms > 0 else "NULL"
    item.bathrooms = item.bathrooms if item.bathrooms > 0 else "NULL"
    item.land_size = item.land_size if item.land_size > 0 else "NULL"
    item.build_size = item.build_size if item.build_size > 0 else "NULL"
    db = Database()
    query = f"""
    UPDATE properties
    SET
        property_type='{item.property_type}',
        location='{item.location}',
        currency='{item.currency}',
        price={item.price},
        bedrooms={item.bedrooms},
        bathrooms={item.bathrooms},
        land_size={item.land_size},
        build_size={item.build_size},
        tab='{item.tab}'
    WHERE url='{item.url}';
    """
    db.run(query)


@router.get("/verified")
async def verified_issue(request: Request, url: str, label: str):
    db = Database()
    query = """
    UPDATE sourcelabels SET is_verified = 1
    WHERE url = '{}' AND label = '{}' AND is_verified = 0;
    """
    db.run(query.format(url, label))


@router.get("/debug")
async def set_debug(request: Request, id: str, is_debug: str):
    query = f"""
    UPDATE data SET is_debug = '{is_debug}'
    WHERE id = '{id}';
    """
    db = Database()
    db.run(query)


@router.get("/is-debug")
async def set_debug(request: Request, url: str):
    urls = url.split(",")
    urls = list(map(str.strip, urls))
    urls = list(filter(lambda str: str.startswith("https"), urls))
    urls_as_string = ",".join(["'{}'".format(u) for u in urls])
    query = f"""
    SELECT url FROM data
    WHERE url IN ({urls_as_string}) 
    AND is_debug = 'true';
    """
    db = Database()
    result = db.fetchall(query)
    return {"urls": result}


@router.get("/exclude")
async def exclude_individual_property(request: Request, url: str, by: str):
    query = f"""
    UPDATE source SET is_excluded='true', excluded_by='{by}'
    WHERE url='{url}';
    """
    db = Database()
    db.run(query)


@router.get("/bulk-exclude")
async def exclude_selected_property(request: Request, property_type: str, by: str):
    db = Database()
    query = f"""
    SELECT DISTINCT url FROM properties
    WHERE property_type = '{property_type}'
    AND url NOT IN (SELECT url FROM source WHERE is_excluded='true');
    """
    urls = db.fetchall(query)
    query = f"""
    UPDATE source SET is_excluded='true', excluded_by='{by}'
    WHERE url IN ({join_strings(urls)});
    """
    db.run(query)


@router.get("/define-tab")
async def define_tab_based_on_price(request: Request):
    db = Database()
    query = f"""
    UPDATE properties SET tab = 'LUXURY LISTINGS'
    WHERE (
        (price > 78656000000 AND currency = 'IDR')
        OR
        (price > 5000000 AND currency = 'USD')
    );
    """
    db.run(query)
