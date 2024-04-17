import numpy as np
import pandas as pd


def get_statistics(properties):
    # conver the data into dataframe
    df = pd.DataFrame(properties)
    df = df[df.is_available == 1]

    # describe the data statiscally
    usd_idx = df[df.currency == "USD"].index
    idr_idx = df[df.currency == "IDR"].index
    df["price_idr"] = df["price"]
    df["price_usd"] = df["price"]
    df.loc[usd_idx, "price_idr"] = np.nan
    df.loc[idr_idx, "price_usd"] = np.nan
    df.drop(columns="price", inplace=True)
    df.drop(columns="is_available", inplace=True)
    stats = df.describe().transpose().to_dict()
    sorted_cols = [
        "price_idr",
        "price_usd",
        "bedrooms",
        "bathrooms",
        "land_size",
        "build_size",
        "leasehold_years",
    ]
    for k in stats:
        stats[k] = [stats[k][v] for v in sorted_cols]
    p25 = stats["25%"]
    p50 = stats["50%"]
    p75 = stats["75%"]
    stats["p25"] = p25
    del stats["25%"]
    stats["p50"] = p50
    del stats["50%"]
    stats["p75"] = p75
    del stats["75%"]
    return stats


def join_strings(values: list):
    return ",".join(["'{}'".format(u) for u in values])


def identify_issue():
    from .issue_finder import queries
    from database import Database
    import time

    start = time.time()

    db = Database()
    for query in queries:
        db.run(query)

    sec = time.time() - start
    print("[i] Identifying issue in the database {:.2f} sec".format(sec))


def compare(url, row, item_b):

    def converting(value, data_type):
        try:
            if data_type in [int, float]:
                value = value.replace(",", "")
            return data_type(value)
        except ValueError:
            return None

    # converting df into dictionary
    item_a = dict(
        source=row["Source A"],
        url=url,
        image_url=row["Image"],
        property_id=row["ID"],
        title=row["Title"],
        description=row["Description"],
        contract_type=row["Contract Type"],
        property_type=row["Property Type"],
        leasehold_years=row["Years"],
        # location=row["Location"],
        bedrooms=row["Bedrooms"],
        bathrooms=row["Bathrooms"],
        build_size=row["Build Size (SQM)"],
        land_size=row["Land Size (SQM)"],
        availability_text=row["Availability"],
        is_off_plan="Yes" if row["Off plan"] else "No",
    )
    item_a["leasehold_years"] = converting(item_a["leasehold_years"], float)
    item_a["bedrooms"] = converting(item_a["bedrooms"], float)
    item_a["bathrooms"] = converting(item_a["bathrooms"], float)
    item_a["build_size"] = converting(item_a["build_size"], int)
    item_a["land_size"] = converting(item_a["land_size"], int)

    # compare the columns
    # print(url)
    diff_columns = []
    for key in item_a:
        value_a = item_a[key]
        value_b = item_b[key]
        if item_a[key] != item_b[key]:
            # print("[" + key + "]", value_a, "vs", value_b)
            diff_columns.append(key)
    # print("-" * 50)

    # return the values for rows
    sheet_columns = {
        "source": "Source A",
        "property_id": "ID",
        "location": "Location",
        "contract_type": "Contract Type",
        "property_type": "Property Type",
        "leasehold_years": "Years",
        "bedrooms": "Bedrooms",
        "bathrooms": "Bathrooms",
        "land_size": "Land Size (SQM)",
        "build_size": "Build Size (SQM)",
        "availability_text": "Availability",
        "url": "Property Link",
        "image_url": "Image",
        "title": "Title",
        "description": "Description",
        "is_off_plan": "Off plan",
    }
    output = {
        "Source A": None,
        "Source B": None,
        "ID": None,
        "Duplicate": None,
        "Region": None,
        "Location": None,
        "Contract Type": None,
        "Property Type": None,
        "Years": None,
        "Bedrooms": None,
        "Bathrooms": None,
        "Land Size (SQM)": None,
        "Build Size (SQM)": None,
        "Price": None,
        "Price ($)": None,
        "Price/SQM ($)": None,
        "Price/Year ($)": None,
        "Availability": None,
        "Sold Date": None,
        "Scrape Date": None,
        "List Date": None,
        "Days listed": None,
        "Property Link": None,
        "Image": None,
        "Title": None,
        "Description": None,
        "Off plan": None,
    }
    for col in diff_columns:
        scol = sheet_columns[col]
        output[scol] = item_b[col]
    # adding price to the output
    output["Price"] = item_b["price"] if item_b["currency"] == "IDR" else None
    output["Price ($)"] = item_b["price"] if item_b["currency"] == "USD" else None
    output["Off plan"] = item_b["is_off_plan"]

    return output
