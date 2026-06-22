import json
import pandas as pd
import pickle
import re

def pickle_prices():
    with open("AllPrices.json","r",encoding="utf-8") as f:
        price_data = json.load(f)
    print("file read...")


    pickle.dump(price_df, open('pickled_price_df.pkl', 'wb'))
    print("file pickled...")

# pickle_prices
price_df = pickle.load(open('pickled_price_df.pkl','rb'))
data_df = price_df.filter(regex=r"^data\.")

regex_filter = r"^data\.00010d56-fe38-5e35-8aed-518019aa36a5\.paper\.cardmarket\.retail\.normal"
data_df = data_df.filter(regex=regex_filter)

# Remove the filter prefix from headers, then print each column header.
header_prefix_pattern = regex_filter[1:]  # drop leading ^ used only for filtering
data_df.columns = (
    data_df.columns
    .str.replace(rf"^{header_prefix_pattern}", "", regex=True)
    .str.lstrip(".")
)

for column_header in data_df.columns:
    print(column_header)

print()
#with open("output.txt", "wt", encoding='utf-8') as f:
#    for pair in value.items():
#        f.write(f"{str(pair[0])}: {str(pair[1])}\n")
print("done")