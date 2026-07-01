# Working Plan:
## Questions to awnser:
- Has power creep accelerated over time?
- Wizards of the Coast made an attempt to reign back complexity of certain sets. Is this verifiable?
- Can card pricing over time be used to visualize past staples being crept out of play?
- does the legality of cards substantially influence price?
- Wizards made a decision to not print cards to demand after a certain date. Can this date be pin-pointed by visualizing cost data?
- which is rising faster: estimated card cost via inflation or actual card cost?

## Questions from peers:
- What is power creep? what is complexity creep?

## Machine learning ideas:
- color pips be used to predict power/toughness?
- can the amount of text / keywords be used to predict power/toughness?
- can the amount of reprints be used to predict card price?

# Datasets:
- Both datasets were downloaded from MTGJSON.com
- Both datasets were accessed on 6/19/2026
- APA formated sources:

# Tasks:
- Data exploration and familiarization 
    - completed: **6/19**
- Data importation
    - completed: **6/22**
- Schema diagram
    - completed: **6/23**
- Data cleaning in Airflow via Pandas (for primary set) and Spark (for larger secondary set)
    - estimated: **6/24**
    - completed: 
- Airflow DAGs ()
- Database creation
    - estimated: **6/25**
    - completed:
- ETL (see ETL document)
    - estimated: **6/29**
    - completed:

1 how has card complexity changed over time
2 how has card power changed over time
3 which card characteristics are associated with higher prices?
4 which color groups have highest price volatility over time
5 do newer prints command higher prices at the same man value?