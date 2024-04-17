from api.func import join_strings
from api.settings import PAGE_SIZE
from database import Database
from datetime import datetime
import api.models.types as models
from pprint import pprint


class ModelObject:
    def __init__(self):
        self.db = Database()

    def count(self, table_name: str = "properties", filter: dict = {}):
        total = 0
        if "start_date" in filter and "end_date" in filter:
            query = f"""
            SELECT COUNT(DISTINCT url) FROM { table_name }
            WHERE created_at >= '{ filter["start_date"] }' AND created_at <= '{ filter["end_date"] }';
            """
            total = self.db.get_first(query)
        elif "scraped_at" in filter:
            query = f"""
            SELECT COUNT(DISTINCT url) FROM { table_name }
            WHERE scraped_at = '{ filter['scraped_at'] }';
            """
            total = self.db.get_first(query)
        return total

    def get_properties(self, urls: list):
        columns = [
            "id",
            "source",
            "excluded_by",
            "scraped_at",
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
            "is_debug",
            "is_available",
            "availability_text",
            "tab",
        ]
        query = f"""
        SELECT { ",".join(columns) } FROM dev_properties p
        JOIN (
            SELECT
                url AS source_url,
                scraped_at,
                CASE
                    WHEN excluded_by == '' THEN NULL
                    ELSE excluded_by
                END AS excluded_by
            FROM source
        ) AS s ON s.source_url = p.url
        LEFT JOIN (
            SELECT id AS data_id, is_debug FROM data
        ) AS d ON d.data_id = p.id
        WHERE url IN ({ join_strings(urls) })
        ORDER BY source, url, created_at DESC;
        """
        records = self.db.get_records(query)

        # converting records into dictionary
        records = [{k: v for k, v in zip(columns, values)} for values in records]

        # converting records into Property object
        recent_properties = {}
        for kwargs in records:
            prop = Property(**kwargs)
            if prop.url in recent_properties:
                prop.is_history = True
                recent_properties[prop.url].count += 1
                recent_properties[prop.url].history.append(prop.as_dict())
            else:
                recent_properties[prop.url] = prop
        properties = list(recent_properties.values())
        properties = [p.as_dict() for p in properties]
        return properties

    def all(self, table_name: str = "properties", filter: dict = {}):
        page = filter.get("page", 1)
        new_only = filter.get("new_only", False)
        urls_only = filter.get("urls_only", False)
        start_date = filter.get("start_date", None)
        end_date = filter.get("end_date", None)
        scraped_at = filter.get("scraped_at", None)
        if "properties" in table_name and start_date and end_date and urls_only:
            query = f"""
            SELECT DISTINCT url FROM { table_name }
            WHERE created_at >= '{ start_date }' AND created_at <= '{ end_date }';
            """
            urls = self.db.fetchall(query)
            return urls

        elif "properties" in table_name and start_date and end_date and page != "all":
            query = f"""
            SELECT DISTINCT url FROM { table_name }
            WHERE created_at >= '{ start_date }' AND created_at <= '{ end_date }'
            { "LIMIT {}".format(PAGE_SIZE) if page == 1 else "LIMIT {} OFFSET {}".format(PAGE_SIZE, page*PAGE_SIZE) };
            """
            urls = self.db.fetchall(query)
            properties = self.get_properties(urls)
            return properties

        elif "properties" in table_name and start_date and end_date and page == "all":
            query = f"""
            SELECT DISTINCT url FROM { table_name }
            WHERE created_at >= '{ start_date }' AND created_at <= '{ end_date }';
            """
            urls = self.db.fetchall(query)
            properties = self.get_properties(urls)
            return properties

        elif "properties" in table_name and scraped_at and new_only:
            query = f"""
            SELECT DISTINCT url FROM source
            WHERE scraped_at = '{ scraped_at }';
            """
            urls = self.db.fetchall(query)
            properties = self.get_properties(urls)
            return properties

        elif table_name == "source" and scraped_at and urls_only:
            query = f"""
            SELECT DISTINCT url FROM { table_name }
            WHERE scraped_at = '{ scraped_at }';
            """
            urls = self.db.fetchall(query)
            return urls


class Property:
    id = models.Text()
    source = models.Text()
    excluded_by = models.Text()
    url = models.Text()
    created_at = models.DateTime()
    scraped_at = models.Text()
    image_url = models.Text()
    title = models.Text()
    description = models.Text()
    price = models.Integer()
    currency = models.Text()
    contract_type = models.Text()
    property_type = models.Text()
    leasehold_years = models.Float()
    location = models.Text()
    bedrooms = models.Float()
    bathrooms = models.Float()
    land_size = models.Integer()
    build_size = models.Integer()
    is_debug = models.Text()
    is_available = models.Boolean()
    availability_text = models.Text()
    tab = models.Text()
    objects = ModelObject()
    count: int = 0
    history: list = []
    is_history: bool = False
    labels: list = []

    def __init__(self, **kwargs):
        self.count = 0
        self.history = []
        self.labels = []
        self.is_history = False
        for key, value in kwargs.items():
            try:
                obj = getattr(self, key)
                new_value = obj.set(value)
                setattr(self, key, new_value)
            except AttributeError as err:
                print("[WARNING]:", err)

        # init
        self.scan_errors()

    def as_dict(self):
        columns = [
            "id",
            "source",
            "excluded_by",
            "url",
            "scraped_at",
            "created_at",
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
            "is_debug",
            "is_available",
            "availability_text",
            "tab",
            "history",
            "labels",
        ]
        if self.is_history:
            columns.remove("history")
            columns.remove("labels")
            columns.remove("excluded_by")
        item_dict = {k: getattr(self, k) for k in columns}
        return item_dict

    def scan_errors(self):
        columns = [
            "image_url",
            "description",
            "price",
            "contract_type",
            "property_type",
            "leasehold_years",
            "location",
            "bedrooms",
            "bathrooms",
            "land_size",
            "build_size",
        ]
        # ignore leasehold years if contract type is Freehold
        contract_type = getattr(self, "contract_type")
        if contract_type == "Freehold":
            columns.remove("leasehold_years")
        # find missing values
        for key in columns:
            value = getattr(self, key)
            # check missing value
            if not value:
                self.labels.append(f"missing_{key}")
            else:
                # check invalid value
                if key == "bedrooms" and value > 20:
                    self.labels.append(f"invalid_{key}")
                elif key == "bathrooms" and value > 20:
                    self.labels.append(f"invalid_{key}")
                elif key == "contract_type" and value not in ["Freehold", "Leasehold"]:
                    self.labels.append(f"invalid_{key}")
                elif key == "property_type" and value not in [
                    "Villa",
                    "Loft",
                    "Townhouse",
                    "House",
                    "Apartment",
                ]:
                    self.labels.append(f"invalid_{key}")

        # insert new labels
        db = Database()
        if len(self.labels) > 0:
            rows = ["('{}', '{}')".format(self.url, label) for label in self.labels]
            values = ",\n".join(rows)
            query = f"""
            INSERT OR IGNORE INTO sourcelabels (url, label)
            VALUES { values };
            """
            db.run(query)

        # inverse the existings label with no existings labels (solved)
        query = f"""
        UPDATE sourcelabels SET is_verified=1
        WHERE url = '{self.url}' AND label NOT IN ({ join_strings(self.labels) });
        """
        db.run(query)

    def __repr__(self):
        return f"Property(id='{self.id}')"
