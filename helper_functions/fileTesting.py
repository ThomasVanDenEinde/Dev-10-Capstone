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
    

def get_card_dict(series_name):
    value = data_df.at[0, series_name]
        
    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
        return value[0]
    return {}


tabular_data = pd.DataFrame(
    {
        "name": names,
        "colorIdentity": colorIdentitys,
        "colors": colors,
        "convertedManaCost": convertedManaCosts,
        "isFunny": isFunny,
        "layout": layouts,
        "manaCost": manacosts,
        "manaValue": manaValues,
        "printings": printings,
        "subtypes": subtypes,
        "supertypes": supertypes,
        "text": text,
        "types": types,
        "card_id":uuid
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


with open("data/pickled_price_df.pkl", "rb") as file:
    temp_price_df = pickle.load(file)

price_df = pd.DataFrame.from_dict(temp_price_df, orient="index")
price_df = price_df.reset_index().rename(columns={"index": "uuid"})

# price_df["price"] = price_df[["cardmarket","tcgplayer","manapool","cardkingdom"]].mean(axis=1, skipna=True) 

tabular_data = tabular_data.merge(
    price_df,
    how="left",
    left_on="card_id",
    right_on="uuid",
)


empty_mask = tabular_data["colorIdentity"].apply(
    lambda v: v is None
    or (isinstance(v, str) and v == "")
    or (isinstance(v, list) and len(v) == 0)
)
tabular_data.loc[empty_mask, "colorIdentity"] = "colorless"

tabular_data["isFunny"] = tabular_data["isFunny"].fillna(False)
tabular_data["isFunny"] = tabular_data["isFunny"].apply(lambda x: bool(x))

tabular_data["manaCost"] = tabular_data["manaCost"].fillna("{0}")

tabular_data["text"] = tabular_data["text"].fillna("")

print_null_and_empty_summary(tabular_data)
name = tabular_data["name"][tabular_data["price"].notna() | tabular_data["price"].notnull()]
print(name)
write_by_name(name)

# print("meta_df columns:", len(meta_df.columns))
# print("data_df columns:", len(data_df.columns))
# 
# print(data_df.columns.to_list()[:2])"""