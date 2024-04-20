import math
from typing import Mapping
from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime as dt, timedelta
from api.func import compare, join_strings
from api.settings import PAGE_SIZE
from database import Database
from api.models.property import ModelObject, Property
import json
import time

from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import relationship
from sqlalchemy import func, select

from libs.googlespreadsheet import SpreadSheetPipeline

Base = declarative_base()
router = APIRouter()

engine = create_engine("sqlite:///database.db")

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# [ ] Render the result including the history of it


## Object
class Source(Base):
    __tablename__ = "source"

    url = Column(String, primary_key=True)
    source = Column(String, nullable=False)
    scraped_at = Column(String)
    is_excluded = Column(Boolean, nullable=False)
    excluded_by = Column(String)


class Properties(Base):
    __tablename__ = "dev_properties"

    id = Column(Integer, primary_key=True)
    url = Column(String, ForeignKey("source.url"))
    property_type = Column(String)
    created_at = Column(Date, nullable=False)
    source = Column(String)


class ScrapedData(Base):
    __tablename__ = "data"

    id = Column(Integer, primary_key=True)
    url = Column(String)
    created_at = Column(Date)


class DateRange:
    def __init__(self, date: str):
        self.original = dt.strptime(date, r"%Y-%m-%d")
        self.start = self.original.strftime(r"%Y-%m-01")
        self.end = self.original.replace(month=self.original.month + 1).replace(
            day=1
        ) - timedelta(days=1)
        self.end = self.end.strftime(r"%Y-%m-%d")

    def for_source(self):
        return self.original.strftime(r"%m/01/%y")

    def __str__(self):
        return (
            "DateRange("
            f"original='{self.original}',"
            f"start='{self.start}',"
            f"end='{self.end}'"
            ")"
        )


## Function and Utilities
def example_function_here():
    pass


## API Endpoints ##


@router.get("/")  # refactor this
async def query_properties(
    request: Request,
    date: str = dt.now().strftime(r"%Y-%m-01"),
    page: int = 1,
):
    date = DateRange(date)
    filter = dict(
        start_date=date.start,
        end_date=date.end,
        page=page,
    )
    properties = Property.objects.all(filter=filter)
    total_results = Property.objects.count(filter=filter)
    results = dict(
        results=properties,
        max_page=math.ceil(int(total_results) / PAGE_SIZE),
        total_current_results=page * len(properties),
        total_results=total_results,
        page=page,
    )
    return results


@router.get("/new-info")  # refactored
async def query_new_properties(
    date: DateRange = Depends(DateRange),
):
    with Session() as session:
        urls = (
            session.query(Source.url)
            .filter(Source.scraped_at == date.for_source())
            .all()
        )
        urls = [i[0] for i in urls]
    db = Database()
    # calculate listings with issues
    total = {}
    query = f"""
    SELECT
        url,
        SUM(label LIKE 'missing_%'),
        SUM(label LIKE 'invalid_%')
    FROM sourcelabels
    WHERE url IN ({ join_strings(urls) })
    AND is_verified == 0
    GROUP BY url;
    """
    result1 = db.get_records(query)
    total_missing_values = len([i for i in result1 if int(i[1])])
    total_invalid_values = len([i for i in result1 if int(i[2])])
    # calculate listings with solved issue
    query = f"""
    SELECT
        url,
        SUM(label LIKE 'missing_%'),
        SUM(label LIKE 'invalid_%')
    FROM sourcelabels
    WHERE url IN ({ join_strings(urls) })
    AND is_verified > 0
    GROUP BY url;
    """
    result2 = db.get_records(query)
    total_missing_solved = len([i for i in result2 if int(i[1])])
    total_invalid_solved = len([i for i in result2 if int(i[2])])
    # how many url that has missing values?
    for key in ["missing", "invalid"]:
        query = f"""
        SELECT COUNT(DISTINCT url) FROM sourcelabels
        WHERE label LIKE '{key}_%'
        AND url IN ({ join_strings(urls) });
        """
        total[f"urls_with_{key}"] = db.get_first(query)
    print(total)

    # how many url that has invalid values?
    results = dict(
        total_new_extracted=len(urls),
        total_missing_values=total_missing_values,
        total_invalid_values=total_invalid_values,
        total_missing_solved=100 * total_missing_solved / total["urls_with_missing"],
        total_invalid_solved=100 * total_invalid_solved / total["urls_with_invalid"],
    )
    return results


@router.get("/total")  # refactored
async def calculate_extracted(date: str = Depends(DateRange)):
    with Session() as session:
        # how many data are being scraped? Count total scraped data from data table within selected period
        query = session.query(func.count(ScrapedData.url)).filter(
            ScrapedData.created_at >= date.start,
            ScrapedData.created_at <= date.end,
        )
        total_scraped = query.scalar()
        # how many new data among the scraped data? Count total scraped data from source table based on date
        query_result = (
            session.query(Source.url)
            .filter(
                Source.scraped_at == date.for_source(),
            )
            .all()
        )
        new_scraped_urls = [i[0] for i in query_result]
        # how many data are being extracted successfully? Count total new rows created on properties table based on selected period
        query = session.query(func.count(Properties.url)).filter(
            Properties.created_at >= date.start,
            Properties.created_at <= date.end,
        )
        total_extracted = query.scalar()
        # how many new data are being extracted successfully? Count total new scraped data being extracted
        query = session.query(func.count(func.distinct(Properties.url))).filter(
            Properties.url.in_(new_scraped_urls)
        )
        total_new_extracted = query.scalar()
        # how many new data are being excluded already? Count total new scraped data that being excluded already
        query = session.query(func.count(Source.url)).filter(
            Source.scraped_at == date.for_source(),
            Source.is_excluded == "true",
        )
        total_new_excluded = query.scalar()

    try:
        extracted_percentage = 100 * total_extracted / total_scraped
    except ZeroDivisionError:
        extracted_percentage = 0

    try:
        new_extracted_percentage = 100 * total_new_extracted / len(new_scraped_urls)
    except ZeroDivisionError:
        new_extracted_percentage = 0

    try:
        new_excluded_percentage = 100 * total_new_excluded / len(new_scraped_urls)
    except ZeroDivisionError:
        new_excluded_percentage = 0

    return dict(
        total_scraped=total_scraped,
        total_new_scraped=len(new_scraped_urls),
        extracted_percentage=extracted_percentage,
        new_extracted_percentage=new_extracted_percentage,
        new_excluded_percentage=new_excluded_percentage,
    )


@router.get("/sheet")
async def missing_urls(
    request: Request,
    date: str = dt.now().strftime(r"%Y-%m-01"),
):
    date = DateRange(date)
    spreadsheet_urls = []
    # get available property urls from the spreadsheet
    for tab in ["DATA", "LUXURY LISTINGS"]:
        gs = SpreadSheetPipeline(
            spreadsheet_name="Q1_MARCH_Working",
            credential="creds.json",
            sheet=tab,
        )
        df = gs.to_dataframe()
        df = df.rename(columns={"Property Link": "url"})
        urls = df[df.Availability == "Available"].url.to_list()
        spreadsheet_urls.extend(urls)

    # remove the empty strings
    spreadsheet_urls = list(filter(lambda url: url != "", spreadsheet_urls))
    # filter not yet downloaded urls from spreadsheet urls
    db = Database("database.db")
    query = f"""
    SELECT url FROM data
    WHERE created_at >= '{date.start}';
    """
    downloaded_urls = db.fetchall(query)
    spreadsheet_urls = [url for url in spreadsheet_urls if url not in downloaded_urls]
    # filter not yet scraped urls from spreadsheet urls
    # query = f"""
    # SELECT url FROM dev_properties
    # WHERE created_at >= '{date.start}';
    # """
    # scraped_urls = db.fetchall(query)
    # spreadsheet_urls = [url for url in spreadsheet_urls if url not in scraped_urls]
    # filter by excluded
    query = f"""
    SELECT url FROM source
    WHERE is_excluded = 'true';
    """
    excluded_urls = db.fetchall(query)
    spreadsheet_urls = [url for url in spreadsheet_urls if url not in excluded_urls]
    query = f"""
    SELECT url, excluded_by FROM source
    WHERE url IN ({ join_strings(spreadsheet_urls) })
    ORDER BY excluded_by DESC;
    """
    records = db.get_records(query)
    not_yet_scraped = [dict(url=i[0], exclusion=i[1]) for i in records]
    not_excluded = sum(
        map(lambda i: 1 if i[1].strip() == "" or i[1] == None else 0, records)
    )
    count_excluded = len(not_yet_scraped) - not_excluded
    return dict(
        count=len(spreadsheet_urls),
        count_excluded=count_excluded,
        results=not_yet_scraped,
    )
    # [ ] Develop API endpoint to check property availability for the unscraped urls in the spreadsheet, if the property does not exists, create one based on the spreadsheet row value


@router.get("/sheet/update")
async def update_spreadsheets_value(
    request: Request,
    date: str = dt.now().strftime(r"%Y-%m-01"),
):
    """
    Updating spreadsheet values by comparing it with the scraped column.
    """
    # convert the date into an object
    date = DateRange(date)
    # comparison operations and updates
    tabs = ["DATA", "LUXURY LISTINGS"]
    output = []
    count = 0
    for tab in tabs:

        # Download urls from the spreadsheet
        gs = SpreadSheetPipeline(
            spreadsheet_name="Q1_MARCH_Working",
            credential="creds.json",
            sheet=tab,
        )
        df = gs.to_dataframe()
        urls = df["Property Link"].to_list()

        # find intersected property on properties table
        columns = [
            "url",
            "source",
            "image_url",
            "property_id",
            "title",
            "description",
            "contract_type",
            "property_type",
            "leasehold_years",
            "price",
            "currency",
            "location",
            "bedrooms",
            "bathrooms",
            "build_size",
            "land_size",
            "is_available",
            "availability_text",
            "is_off_plan",
        ]
        query = f"""
        SELECT { ",".join(columns) } FROM dev_properties
        WHERE url IN ({ join_strings(urls) })
        AND url NOT IN (SELECT url FROM source WHERE is_excluded='true')
        AND created_at >= '{ date.start }'
        AND created_at <= '{ date.end }'
        AND is_available=1;
        """
        db = Database("database.db")
        records = db.get_records(query)
        records = {
            values[0]: {k: v for k, v in zip(columns, values)} for values in records
        }

        values = []
        for i in df.index:
            url = df.loc[i, "Property Link"]
            availability = df.loc[i, "Availability"]
            if url in records and availability == "Available":
                count += 1
                is_off_plan = "Yes" if records[url]["is_off_plan"] else "No"
                records[url]["is_off_plan"] = is_off_plan
                row = compare(
                    url,
                    df.loc[i].to_dict(),
                    records[url],
                )
                output.append(
                    dict(
                        url=url,
                        output={k: v for k, v in row.items() if v},
                    )
                )
                values.append(list(row.values()))
            else:
                empty = [None for _ in range(28)]
                values.append(empty)

        # updating the spreadsheet
        cell = "A3" if tab == "LUXURY LISTINGS" else "B3"
        gs.sh.update(range_name=cell, values=values)

    return dict(
        detail="{:,d} rows has been updated!".format(count),
        # result=output,
    )


@router.get("/all")  # refactor this
async def get_all_properties(
    request: Request,
    date: str = dt.now().strftime(r"%Y-%m-01"),
):
    """
    Retrive all properties in the dev_properties database
    WARNING: this endpoint for identifying the issue only
    """
    date = DateRange(date)
    filter = dict(
        start_date=date.start,
        end_date=date.end,
        page="all",
    )
    properties = Property.objects.all(table_name="dev_properties", filter=filter)
    return dict(count=len(properties))


@router.get("/exclusions")  # refactored
async def find_excluded_by(date: DateRange = Depends(DateRange)):
    with Session() as session:
        result = (
            session.query(func.distinct(Properties.url))
            .filter(
                Properties.created_at >= date.start,
                Properties.created_at <= date.end,
            )
            .all()
        )
        unique_urls = [i[0] for i in result]
        query = (
            select(
                Source.excluded_by,
                func.count(Source.url).label("total"),
            )
            .where(
                Source.is_excluded == "true",
                Source.url.in_(unique_urls),
            )
            .group_by(Source.excluded_by)
        )
        result = session.execute(query)
        records = [dict(name=i.excluded_by, count=i.total) for i in result]
    return records


@router.get("/labels")  # refactor this
async def find_missing_and_invalid_labels(
    date: DateRange = Depends(DateRange),
):
    # initiate the object
    db = Database()
    filter = dict(
        start_date=date.start,
        end_date=date.end,
        urls_only=True,
    )
    urls = Property.objects.all(
        table_name="dev_properties",
        filter=filter,
    )
    # query the sourcelabels
    keywords = ["missing", "invalid"]
    labels = {k: None for k in keywords}
    for key in keywords:
        query_missings = f"""
        SELECT
            (SELECT name FROM labels WHERE id=label),
            label,
            COUNT(*)
        FROM sourcelabels
        WHERE label LIKE '{ key }%' AND url IN ({ join_strings(urls) })
        AND is_verified = 0 GROUP BY label;
        """
        records = db.get_records(query_missings)
        labels[key] = [dict(name=i[0], label=i[1], count=i[2]) for i in records]
    return labels


@router.get("/label/{label:path}/verify")
async def verified_property_label(request: Request, id: str, label: str):
    db = Database()
    url = db.get_first(f"SELECT url FROM dev_properties WHERE id='{id}'")
    if url:
        db.run(
            f"UPDATE sourcelabels SET is_verified=1 WHERE url='{url}' AND label='{label}';"
        )
        return dict(ok=True)
    raise HTTPException(status_code=403, detail="URL not found")


@router.get("/label/{label:path}")  # refactor this
def get_properties_with_issues(
    label: str,
    date: str = dt.now().strftime(r"%Y-%m-01"),
    page: int = 1,
    is_exclusion: bool = False,
):
    # declaration
    db = Database()
    date = DateRange(date)
    # query urls based on labels
    if not is_exclusion:
        query = f""" 
        SELECT DISTINCT url FROM sourcelabels
        WHERE is_verified=0 AND label='{ label }';
        """
        urls = db.fetchall(query)
    else:
        # query urls the excluded property
        query = f"""
        SELECT DISTINCT url FROM source
        WHERE excluded_by = '{ label }' AND url IN (
            SELECT DISTINCT url FROM dev_properties
        );
        """
        urls = db.fetchall(query)
    # filter urls by date
    query = f"""
    SELECT COUNT(DISTINCT url) FROM dev_properties
    WHERE created_at >= '{ date.start }' AND created_at <= '{ date.end }' AND url IN ({ join_strings(urls) });
    """
    count = db.get_first(query)
    max_page = math.ceil(int(count) / PAGE_SIZE)
    # paginate the result
    query = f"""
    SELECT url FROM dev_properties
    WHERE created_at >= '{ date.start }' AND created_at <= '{ date.end }' AND url IN ({ join_strings(urls) })
    ORDER BY source
    { "LIMIT {}".format(PAGE_SIZE) if page == 1 else "LIMIT {} OFFSET {}".format(PAGE_SIZE, page*PAGE_SIZE) };
    """
    urls = db.fetchall(query)
    # query the property in the dataset
    obj = ModelObject()
    properties = obj.get_properties(urls)
    return dict(
        page=page,
        max_page=max_page,
        count=len(urls),
        results=properties,
    )


@router.delete("/property")
async def delete_property_data(request: Request, id: str):
    db = Database()
    # delete data from data table
    url = db.get_first(f"SELECT url FROM dev_properties WHERE id='{id}';")
    db.run("DELETE FROM data WHERE url='{}';".format(url))
    # delete data from properties table
    db.run("DELETE FROM dev_properties WHERE url='{}';".format(url))
    db.run("DELETE FROM properties WHERE url='{}';".format(url))
    # verified all the issue
    db.run("UPDATE sourcelabels SET is_verified=1 WHERE url='{}';".format(url))
    return dict(url=url, status="deleted")


@router.patch("/property/cancel-exclusion")
async def cancel_property_exclusion(request: Request, id: str):
    db = Database()
    # query the excluded by status
    url = db.get_first(f"SELECT url FROM dev_properties WHERE id='{id}';")
    result = db.get_record(
        f"SELECT is_excluded, excluded_by FROM source WHERE url='{url}'"
    )
    if result:
        is_excluded, excluded_by = result
        # cancel the exclusion the url
        db.run(
            f"UPDATE source SET is_excluded='false', excluded_by='' WHERE url='{url}'"
        )
        # return the query result as response data
        if is_excluded:
            return dict(url=url, status="'{}' exclusion canceled".format(excluded_by))
    raise HTTPException(
        status_code=404, detail="cancelation failed. the url never been excluded."
    )


@router.patch("/source/exclusion")
async def update_source_excluded_by(
    request: Request,
    id: str,
    new_value: str,
):
    db = Database()
    url = db.get_first(f"SELECT url FROM dev_properties WHERE id='{id}';")
    if url:
        db.run(
            f"UPDATE source SET is_excluded='true',excluded_by='{new_value}' WHERE url='{url}';"
        )
        return dict(url=url, status="the property has been updated")
    raise HTTPException(
        status_code=404, detail="exclusion is failed. the url never exists."
    )


@router.put("/property")
async def update_property(request: Request):

    # get request data
    body_data = await request.body()
    decode_data = body_data.decode("utf-8")
    data = json.loads(decode_data)
    data = {k: None if v == "null" or v == "" else v for k, v in data.items()}

    # update database
    columns = [
        # "description",
        # "image_url",
        # "is_available",
        # "availability_text",
    ]

    str = lambda value: f"'{value}'"

    query = f"""
    UPDATE dev_properties SET
        title={str(data['title']) if data["title"] else "NULL"},
        price={data['price'] if data["price"] else "NULL"},
        currency={str(data['currency']) if data["currency"] else "'IDR'"},
        contract_type={str(data['contract']) if data["contract"] else "NULL"},
        property_type={str(data['type']) if data["type"] else "NULL"},
        leasehold_years={data['years'] if data["years"] else "NULL"},
        bedrooms={data['bedrooms'] if data["bedrooms"] else "NULL"},
        bathrooms={data['bathrooms'] if data["bathrooms"] else "NULL"},
        build_size={data['build_size'] if data["build_size"] else "NULL"},
        land_size={data['land_size'] if data["land_size"] else "NULL"},
        location={str(data['location']) if data["location"] else "NULL"}
    WHERE id='{data["id"]}';
    """
    db = Database()
    db.run(query)

    # print back new data
    return data


@router.get("/property-types")  # refactored
async def find_property_types(date: DateRange = Depends(DateRange)):
    with Session() as session:
        query = (
            select(
                Properties.property_type,
                func.count(func.distinct(Properties.url)).label("total"),
            )
            .where(
                Properties.property_type != "",
                Properties.created_at >= date.start,
                Properties.created_at <= date.end,
            )
            .group_by(Properties.property_type)
            .order_by(func.count(func.distinct(Properties.url)).desc())
        )
        records = session.execute(query)
        records = [dict(name=i.property_type, count=i.total) for i in records]
    return records


@router.get("/property-types/unit")  # refactored
async def get_property_types(
    page: int = 1,
    type: str = "Villa",
    date: DateRange = Depends(DateRange),
):
    with Session() as session:
        filter_condition = [
            Properties.property_type == type,
            Properties.created_at >= date.start,
            Properties.created_at <= date.end,
        ]
        # count total urls
        total_urls = (
            session.query(func.count(func.distinct(Properties.url)))
            .filter(*filter_condition)
            .scalar()
        )
        max_page = math.ceil(total_urls / PAGE_SIZE)
        # query unique urls
        query = (
            select(func.distinct(Properties.url))
            .filter(*filter_condition)
            .limit(PAGE_SIZE)
            .offset(0 if page == 1 else page * PAGE_SIZE)
        )
        urls = [i[0] for i in session.execute(query).all()]
    properties = Property.objects.get_properties(urls)
    return dict(
        count=len(properties),
        page=page,
        max_page=max_page,
        results=properties,
    )
