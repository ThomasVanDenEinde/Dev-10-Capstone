Project Summary:
This project aims to answer a number of data reliant questions (see technical report) related to Magic: The Gathering card and pricing data.
These questions are answered by combining multiple datasets from MTGJSON.com, cleaning the data using the Pandas library,
uploading the cleaned data to a new database specially developed for this project, and pulling from this database using SQLAlchemy to be used in visualizations.

Project Limitations:
MTGJSON.com only stores 90 days worth of sales data at any given time and the same limit is present in this project.
This project only considers cards that have corrosponding sales data, which is not 100% of cards.
Many older cards (printed pre 2020) lack exact print date and are not considered in date visualizations.
