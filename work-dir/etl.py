from pyspark.sql import SparkSession
import json
import pandas as pd
import pickle

spark = SparkSession.builder.appName("ExamplePySparkApp").getOrCreate()

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

temp_price_df = pickle.load("data/pickled_price_df.pkl")

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
tabular_data = tabular_data.set_index('uuid').join(temp_price_df.set_index('uuid'))

# If column may contain empty lists, empty strings, or nulls
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





spark.stop()