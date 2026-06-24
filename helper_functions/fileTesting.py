import json
import pandas as pd


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

# Build a hash-safe key DataFrame so list/dict columns can be deduplicated.
tabular_data = tabular_data.drop_duplicates(subset=["name"],keep="first")
print(tabular_data.head(10))
print(tabular_data.describe())

def write_by_name(card_name):
    test_print = tabular_data.where(tabular_data["name"] == card_name)
    with open("output.txt", "wt", encoding="utf-8") as f:
        for column in test_print.columns:
            f.write(f"{str(column)}: {str(test_print[column].values[0])}\n")


write_by_name("Ancestor's Chosen")
# print("meta_df columns:", len(meta_df.columns))
# print("data_df columns:", len(data_df.columns))
# 
# print(data_df.columns.to_list()[:2])"""