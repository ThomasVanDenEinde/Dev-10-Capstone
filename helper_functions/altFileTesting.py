import json
import pandas as pd
import pickle
import re

def pickle_prices():
    print("reading raw json...")
    with open("data/AllPrices.json","r",encoding="utf-8") as f:
        price_data = json.load(f)
    print("file read...")
    try:
        k = 'data'
        price_df = price_data.get(k)
    except:
        print(f"getting '{k}' FAILED... Printing alternative keys:")
        for key in price_data.keys():
            print(key)
        return
    try:
        uuid = "00010d56-fe38-5e35-8aed-518019aa36a5"
        price_df = price_df.get(uuid)
        print("Finding sample prices by uuid success!\nPickling...")
        pickle.dump(price_df, open('data/pickled_price_df.pkl', 'wb'))
        print("file pickled...")
    except:
        print(f"getting '{uuid}' FAILED... Printing alternative keys:")
        for key in price_df.keys():
            print(key)

pickle_prices()

