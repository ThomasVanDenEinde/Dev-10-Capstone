from pyspark.sql import SparkSession
import json
import pandas as pd
import pickle
import gc
import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    BooleanType,
    DateType,
    IntegerType,
    DecimalType,
)


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

spark = (SparkSession.builder.appName("ExamplePySparkApp")
         .config("spark.jars.packages", "org.postgresql:postgresql:42.7.3")
         .getOrCreate())


def load_local_spark_defaults(project_root):
    defaults = {}
    conf_path = project_root / "conf" / "spark-defaults.conf"
    if not conf_path.exists():
        return defaults

    for raw_line in conf_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        key, value = parts
        defaults[key.strip()] = value.strip()

    return defaults


LOCAL_SPARK_DEFAULTS = load_local_spark_defaults(PROJECT_ROOT)


def get_spark_config(key):
    try:
        return spark.conf.get(key)
    except Exception:
        env_key = key.upper().replace(".", "_")
        env_value = os.getenv(env_key)
        if env_value:
            return env_value
        return LOCAL_SPARK_DEFAULTS.get(key)

with open(DATA_DIR / "AllPrintings.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    
data_df = data.get('data')
    
names = []
colorIdentitys=[]
colors=[]
convertedManaCosts=[]
isFunny=[]
layouts=[]
manacosts=[]
manaValues=[]
printings=[]
subtypes=[]
supertypes=[]
text=[]
types=[]
date=[]
uuid=[]
power=[]
toughness=[]
print_date=[]


for block in data_df.keys():
    cards = data_df.get(block).get("cards")
    for card in cards:
        names.append(card.get("name"))
        colorIdentitys.append(card.get("colorIdentity"))
        colors.append(card.get("colors"))
        convertedManaCosts.append(card.get("convertedManaCost"))
        isFunny.append(card.get("isFunny"))
        layouts.append(card.get("layout"))
        manacosts.append(card.get("manaCost"))
        manaValues.append(card.get("manaValue"))
        printings.append(card.get("printings"))
        subtypes.append(card.get("subtypes"))
        supertypes.append(card.get("supertypes"))
        text.append(card.get("text"))
        types.append(card.get("types"))
        uuid.append(card.get("uuid"))
        power.append(card.get("power"))
        toughness.append(card.get("toughness"))
        print_date.append(card.get("originalReleaseDate"))
    

def get_card_dict(series_name):
    value = data_df.at[0, series_name]
        
    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
        return value[0]
    return {}


tabular_data = pd.DataFrame(
    {
        "name": names,
        "color_id": colorIdentitys,
        "colors": colors,
        "convertedManaCost": convertedManaCosts,
        "is_funny": isFunny,
        "layout": layouts,
        "mana_cost": manacosts,
        "mana_value": manaValues,
        "printings": printings,
        "sub_types": subtypes,
        "super_types": supertypes,
        "text": text,
        "types": types,
        "card_id":uuid,
        "power": power,
        "toughness":toughness,
        "print_date":print_date
    }
)

tabular_data = tabular_data.drop_duplicates(subset=["name"],keep="first")

def print_null_and_empty_summary(df):
    summary = []

    for column in df.columns:
        series = df[column]
        null_count = int(series.isna().sum())

        # Count empty strings and empty lists in object-like columns.
        empty_count = int(series.apply(lambda v: v == "" or v == []).sum())

        summary.append(
            {
                "column": column,
                "null_values": null_count,
                "empty_strings_or_lists": empty_count,
            }
        )

    print("\nPer-column null/empty summary:")
    print(pd.DataFrame(summary).to_string(index=False))



def write_by_name(card_name):
    test_print = tabular_data.where(tabular_data["name"] == card_name)
    with open("output.txt", "wt", encoding="utf-8") as f:
        for column in test_print.columns:
            f.write(f"{str(column)}: {str(test_print[column].values[0])}\n")


def normalize_print_date(value):
    if value is None:
        return None

    if isinstance(value, dict):
        for key in ("date", "value", "text", "original"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return None

    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                return item.strip()
        return None

    if isinstance(value, str):
        return value.strip() or None

    return str(value)

with open(DATA_DIR / "AllPrices.json", "r", encoding="utf-8") as f:
    temp_price_df = json.load(f).get('data')
#ith open("data/pickled_price_df.pkl", "rb") as file:
#   temp_price_df = pickle.load(file)


stores = ["cardmarket","tcgplayer","manapool","cardkingdom"]


def extract_price_series(store_payload, use_foil):
    if not isinstance(store_payload, dict):
        return {}

    if use_foil:
        foil_series = store_payload.get("foil", {}).get("normal")
        if isinstance(foil_series, dict):
            return foil_series
        retail_foil_series = store_payload.get("retail", {}).get("foil")
        if isinstance(retail_foil_series, dict):
            return retail_foil_series
        return {}

    retail_normal_series = store_payload.get("retail", {}).get("normal")
    if isinstance(retail_normal_series, dict):
        return retail_normal_series
    return {}


raw_price_data = []

for card_uuid, payload in temp_price_df.items():
    paper_payload = payload.get("paper", {}) if isinstance(payload, dict) else {}

    has_any_nonfoil = any(
        isinstance(
            paper_payload.get(store, {}).get("retail", {}).get("normal"),
            dict,
        )
        and len(paper_payload.get(store, {}).get("retail", {}).get("normal")) > 0
        for store in stores
    )
    foil_mode = not has_any_nonfoil

    store_series = {
        store: extract_price_series(paper_payload.get(store, {}), foil_mode)
        for store in stores
    }

    all_dates = sorted(
        {
            date
            for series in store_series.values()
            for date in series.keys()
        }
    )

    for date in all_dates:
        row = {
            "uuid": card_uuid,
            "date": date,
            "is_foil_price": foil_mode,
        }
        for store in stores:
            row[store] = store_series[store].get(date)
        raw_price_data.append(row)

price_df = pd.DataFrame(raw_price_data)
if not price_df.empty:
    price_df["price"] = price_df[stores].mean(axis=1, skipna=True)
else:
    price_df = pd.DataFrame(
        columns=["uuid", "date", *stores, "price", "is_foil_price"]
    )

price_df["price"] = price_df["price"].apply(lambda x: round(x, 2))

intersect_count = len(
    set(price_df["uuid"].dropna().unique())
    & set(tabular_data["card_id"].dropna().unique())
)
print(f"intersecting uuid/card_id count: {intersect_count}")

shared_ids = set(price_df["uuid"].dropna().unique()) & set(
    tabular_data["card_id"].dropna().unique()
)
tabular_data = tabular_data[tabular_data["card_id"].isin(shared_ids)].copy()
price_df = price_df[price_df["uuid"].isin(shared_ids)].copy()
printings_by_card_id = tabular_data.set_index("card_id")["printings"].to_dict()
print(
    f"filtered rows => tabular_data: {len(tabular_data)}, price_df: {len(price_df)}"
)

jdbc_options = {
    "url": get_spark_config("spark.postgresql.capstone.url"),
    "user": get_spark_config("spark.postgresql.capstone.user"),
    "password": get_spark_config("spark.postgresql.capstone.password"),
    "driver": "org.postgresql.Driver",
}

missing_jdbc_keys = [
    key for key in ("url", "user", "password") if not jdbc_options.get(key)
]
if missing_jdbc_keys:
    raise ValueError(
        "Missing JDBC config values for: "
        + ", ".join(missing_jdbc_keys)
        + ". Set Spark SQL conf, environment variables, or conf/spark-defaults.conf."
    )
print("Inserting into cards...")
cards_pd = tabular_data.copy()

cards_pd["is_funny"] = cards_pd["is_funny"].astype("boolean").fillna(False)
cards_pd["is_funny"] = cards_pd["is_funny"].astype(bool)
cards_pd["print_date"] = cards_pd["print_date"].apply(normalize_print_date)
cards_pd["print_date"] = pd.to_datetime(
    cards_pd["print_date"], errors="coerce"
).dt.date
cards_pd["print_date"] = cards_pd["print_date"].where(
    cards_pd["print_date"].notna(), None
)

card_schema = StructType(
    [
        StructField("card_id", StringType(), True),
        StructField("name", StringType(), True),
        StructField("is_funny", BooleanType(), True),
        StructField("layout", StringType(), True),
        StructField("text", StringType(), True),
        StructField("print_date", DateType(), True),
        StructField("power", StringType(), True),
        StructField("toughness", StringType(), True),
    ]
)

card_input = cards_pd[
    [
        "card_id",
        "name",
        "is_funny",
        "layout",
        "text",
        "print_date",
        "power",
        "toughness",
    ]
].copy()

card_spark_df = spark.createDataFrame(card_input, schema=card_schema)
card_spark_df.write.format("jdbc").options(**jdbc_options, dbtable="card").mode(
    "append"
).save()


# =============== card_types ===============
print("Inserting into card types...")

def normalize_type_values(value):
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if value is None:
        return None
    return str(value)


cards_pd["sub_types"] = cards_pd["sub_types"].apply(normalize_type_values)
cards_pd["types"] = cards_pd["types"].apply(normalize_type_values)
cards_pd["super_types"] = cards_pd["super_types"].apply(normalize_type_values)

type_schema = StructType(
    [
        StructField("card_id", StringType(), True),
        StructField("sub_types", StringType(), True),
        StructField("types", StringType(), True),
        StructField("super_types", StringType(), True),
    ]
)

type_input = cards_pd[
    [
        "card_id",
        "sub_types",
        "types",
        "super_types",
    ]
].copy()

type_spark_df = spark.createDataFrame(type_input, schema=type_schema)
type_spark_df.write.format("jdbc").options(**jdbc_options, dbtable="card_types").mode(
    "append"
).save()


# =============== card_mana ===============
print("Inserting into card mana...")


def normalize_list_to_string(value, max_len=None):
    if isinstance(value, list):
        text_value = ",".join(str(item) for item in value)
    elif value is None:
        return None
    else:
        text_value = str(value)

    if max_len is not None:
        return text_value[:max_len]
    return text_value


def to_decimal_2(value):
    if value is None or pd.isna(value):
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        return None


mana_pd = tabular_data.copy()
mana_pd["color_id"] = mana_pd["color_id"].apply(
    lambda v: normalize_list_to_string(v, 10)
)
mana_pd["colors"] = mana_pd["colors"].apply(
    lambda v: normalize_list_to_string(v, 20)
)
mana_pd["mana_cost"] = mana_pd["mana_cost"].apply(
    lambda v: "" if v is None else str(v)[:20]
)
mana_pd["cmc"] = (
    pd.to_numeric(mana_pd["convertedManaCost"], errors="coerce").fillna(0).round().astype(int)
)
mana_pd["mana_value"] = (
    pd.to_numeric(mana_pd["mana_value"], errors="coerce").fillna(0).round().astype(int)
)

mana_schema = StructType(
    [
        StructField("card_id", StringType(), True),
        StructField("color_id", StringType(), True),
        StructField("colors", StringType(), True),
        StructField("cmc", IntegerType(), True),
        StructField("mana_cost", StringType(), True),
        StructField("mana_value", IntegerType(), True),
    ]
)

mana_input = mana_pd[
    [
        "card_id",
        "color_id",
        "colors",
        "cmc",
        "mana_cost",
        "mana_value",
    ]
].copy()

mana_spark_df = spark.createDataFrame(mana_input, schema=mana_schema)
mana_spark_df.write.format("jdbc").options(**jdbc_options, dbtable="card_mana").mode(
    "append"
).save()


# =============== card_price ===============
print("Inserting into pricing...")

price_out_pd = price_df[["uuid", "date", "price"]].copy()
price_out_pd = price_out_pd.rename(columns={"uuid": "card_id"})
price_out_pd["printings"] = price_out_pd["card_id"].map(printings_by_card_id)
price_out_pd["date"] = pd.to_datetime(price_out_pd["date"], errors="coerce").dt.date
price_out_pd["printings"] = price_out_pd["printings"].apply(lambda v: normalize_list_to_string(v, 100))
price_out_pd["price"] = pd.to_numeric(price_out_pd["price"], errors="coerce")
price_out_pd["price"] = price_out_pd["price"].apply(to_decimal_2)
price_out_pd = price_out_pd.dropna(subset=["card_id", "price", "date"]).copy()

price_schema = StructType(
    [
        StructField("card_id", StringType(), True),
        StructField("price", DecimalType(8, 2), True),
        StructField("date", DateType(), True),
        StructField("printings", StringType(), True),
    ]
)

price_input = price_out_pd[
    [
        "card_id",
        "price",
        "date",
        "printings",
    ]
].copy()

chunk_size = 200000
for start in range(0, len(price_input), chunk_size):
    chunk = price_input.iloc[start:start + chunk_size].copy()
    price_spark_df = spark.createDataFrame(chunk, schema=price_schema)
    price_spark_df.write.format("jdbc").options(**jdbc_options, dbtable="card_price").mode(
        "append"
    ).save()
    print(f"Inserted pricing rows: {start + len(chunk)} / {len(price_input)}")

del price_input
gc.collect()



spark.stop()