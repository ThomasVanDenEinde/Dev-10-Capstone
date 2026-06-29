import json
import pandas as pd
import pickle

with open("data/AllPrintings.json", "r", encoding="utf-8") as f:
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

with open("data/AllPrices.json","r",encoding="utf-8") as f:
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
print(
    f"filtered rows => tabular_data: {len(tabular_data)}, price_df: {len(price_df)}"
)


card_price_df = tabular_data.merge(
    price_df,
    how="inner",
    left_on="card_id",
    right_on="uuid",
)
card_price_df["layout"] = card_price_df["layout"].apply(lambda x: ', '.join(x))
card_price_df["is_funny"] = card_price_df["is_funny"].fillna(False)
card_price_df["is_funny"] = card_price_df["is_funny"].astype(bool, errors='raise')
card_price_df["print_date"] = pd.to_datetime(card_price_df["print_date"]).dt.strftime('%Y-%m-%dT%H:%M:%SZ')

for column in card_price_df[["card_id",
                                               "sub_types",
                                               "types",
                                               "super_types",
                                               ]].columns:
    print(f"{column}: {card_price_df[column].dtype}")

