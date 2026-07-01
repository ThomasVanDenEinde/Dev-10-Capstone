from dash import Dash, dash_table, html, dcc, Input, Output, callback
import plotly.express as px
from pyspark.sql import SparkSession
from pathlib import Path
from sqlalchemy import create_engine, text
import pandas as pd
import numpy as np
import os
from dynaconf import Dynaconf

app = Dash()


def build_engine():
    settings = Dynaconf(envvar_prefix="DB", load_dotenv=True)
    return create_engine(settings.ENGINE_URL, echo=False)


engine = build_engine()

cards_df = pd.read_sql_query(
"""
SELECT c.card_id,
    c.name,
    c.is_funny,
    c.layout,
    c.text,
    c.print_date,
    c.power,
    c.toughness,
    ct.sub_types,
    ct.types,
    ct.super_types,
    cm.color_id,
    cm.colors,
    cm.cmc,
    cm.mana_cost,
    cm.mana_value
FROM card c
JOIN card_types ct ON c.card_id = ct.card_id
JOIN card_mana cm ON ct.card_id = cm.card_id
""",
engine,
)


def parse_whole_stat(value):
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    if "*" in text or text.startswith("-"):
        return None

    if text.startswith("+"):
        text = text[1:].strip()

    try:
        number = float(text)
    except ValueError:
        return None

    if not number.is_integer():
        return None

    return int(number)


def get_power_creep():
    year = 2020
    
    keyword_abilities = [
    "Adapt", "Affinity", "Alliance", "Annihilator", "Ascend", "Assist", 
    "Aura swap", "Banding", "Battle cry", "Bestow", "Bloodthirst", "Boast", 
    "Bushido", "Buyback", "Cascade", "Champion", "Changeling", "Cipher", 
    "Conspire", "Convoke", "Crew", "Cycling", "Dash", "Deathtouch", 
    "Defender", "Delve", "Dethrone", "Devour", "Double strike", "Dredge", 
    "Echo", "Enchant", "Enlist", "Entwine", "Epic", "Equip", "Escalate", 
    "Escape", "Exhume", "Exploit", "Extort", "Fading", "Fear", "First strike", 
    "Flash", "Flashback", "Flying", "Forecast", "Fortify", "Goad", "Graft", 
    "Gravestorm", "Haunt", "Haste", "Hexproof", "Hidden agenda", "Horsemanship", 
    "Indestructible", "Infect", "Intimidate", "Investigate", "Jump-start", 
    "Kicker", "Landwalk", "Lifelink", "Living weapon", "Madness", "Manifest", 
    "Menace", "Mentor", "Miracle", "Modular", "Morph", "Mutate", "Myriad", 
    "Ninjutsu", "Offering", "Outlast", "Overload", "Persist", "Phasing", 
    "Poisonous", "Proliferate", "Protection", "Prowess", "Prowl", "Rampage", 
    "Reach", "Rebound", "Recover", "Reinforce", "Renown", "Replicate", "Riot", 
    "Ripple", "Sacrifice", "Scry", "Shadow", "Shroud", "Skulk", "Soulbond", 
    "Split second", "Storm", "Sunburst", "Surge", "Surveil", "Suspend", 
    "Swampwalk", "Tempting offer", "Totem armor", "Toxic", "Trample", 
    "Transmute", "Tribal", "Undying", "Unearth", "Vanishing", "Vigilance", 
    "Ward"
    ]
    special_abilities = [
        "destroy target", "draw", "search your library", "add"
    ]
    all_keywords = [kw.lower() for kw in keyword_abilities + special_abilities]

    def keyword_points(text_value):
        if pd.isna(text_value):
            return 0
        text_lower = str(text_value).lower()
        return sum(1 for kw in all_keywords if kw in text_lower)

    creature_df = cards_df[
        cards_df["types"].str.contains(r"\bcreature\b", case=False, na=False)
    ].copy()

    creature_df["power_int"] = creature_df["power"].apply(parse_whole_stat)
    creature_df["toughness_int"] = creature_df["toughness"].apply(parse_whole_stat)
    creature_df = creature_df[
        creature_df["power_int"].notna() & creature_df["toughness_int"].notna()
    ].copy()
    creature_df["keyword_points"] = creature_df["text"].apply(keyword_points)
    creature_df["power points"] = (
        creature_df["power_int"]
        + creature_df["toughness_int"]
        + creature_df["keyword_points"]
    )

    pre_2010_df = creature_df[
        pd.to_datetime(creature_df["print_date"], errors="coerce")
        < pd.Timestamp(f"{year}-01-01")
    ].copy()
    post_2010_df = creature_df[
        pd.to_datetime(creature_df["print_date"], errors="coerce")
        >= pd.Timestamp(f"{year}-01-01")
    ].copy()

    fig_pre2010 = px.scatter(
        pre_2010_df,
        x="cmc",
        y="power points",
        hover_name="name",
        opacity=0.35,
        title=f"creature power 'pointage' for cards pre-{year}"
    )
    
    fig_post2010 = px.scatter(
        post_2010_df,
        x="cmc",
        y="power points",
        hover_name="name",
        opacity=0.35,
        title=f"creature power 'pointage' for cards post-{year}"
    )

    combined_df = pd.concat(
        [
            pre_2010_df.assign(era=f"pre-{year}"),
            post_2010_df.assign(era=f"post-{year}"),
        ],
        ignore_index=True,
    )
    fig_combined = px.scatter(
        combined_df,
        x="cmc",
        y="power points",
        hover_name="name",
        color="era",
        opacity=0.35,
        color_discrete_map={f"pre-{year}": "royalblue", f"post-{year}": "tomato"},
        title=f"creature power 'pointage' pre/post-{year}",
    )

    fig_pre2010.update_xaxes(range=[0, 15])
    fig_pre2010.update_yaxes(range=[0, 40])
    fig_post2010.update_xaxes(range=[0, 15])
    fig_post2010.update_yaxes(range=[0, 40])
    fig_combined.update_xaxes(range=[0, 15])
    fig_combined.update_yaxes(range=[0, 40])

    def add_quadratic_trendline(fig, source_df, line_name, line_color=None):
        trend_df = source_df[["cmc", "power points"]].dropna().copy()
        if len(trend_df) >= 3:
            trend_df = trend_df.sort_values("cmc")
            coefficients = np.polyfit(trend_df["cmc"], trend_df["power points"], 2)
            polynomial = np.poly1d(coefficients)
            fig.add_scatter(
                x=trend_df["cmc"],
                y=polynomial(trend_df["cmc"]),
                mode="lines",
                name=line_name,
                line={"color": line_color} if line_color else None,
            )

    add_quadratic_trendline(fig_pre2010, pre_2010_df, "Quadratic Trend")
    add_quadratic_trendline(fig_post2010, post_2010_df, "Quadratic Trend")
    add_quadratic_trendline(
        fig_combined,
        pre_2010_df,
        f"Quadratic Trend pre-{year}",
        "royalblue",
    )
    add_quadratic_trendline(
        fig_combined,
        post_2010_df,
        f"Quadratic Trend post-{year}",
        "tomato",
    )
    return fig_pre2010, fig_post2010, fig_combined


def get_complexity_creep():
    complexity_df = cards_df.copy()
    date_series = complexity_df["date"] if "date" in complexity_df.columns else complexity_df["print_date"]
    complexity_df["year"] = pd.to_datetime(date_series, errors="coerce").dt.year
    complexity_df["txt_len"] = complexity_df["text"].str.len()

    fig = px.scatter(
        complexity_df,
        x="year",
        y="txt_len",
        hover_name="txt_len",
        opacity=0.3,
        title=f"complexity (amount of text on card) by year",
        trendline="ols"
    )
    fig.update_yaxes(range=[0, 650])
    return fig

def get_price_by_characteristic():
    sql = """WITH latest_price AS (
    SELECT DISTINCT ON (cp.card_id)
        cp.card_id,
        cp.price,
        cp."date" AS price_date
    FROM capstone.card_price cp
    ORDER BY cp.card_id, cp."date" DESC
    ),
    features AS (
        SELECT
            c.card_id,
            c.name,
            c.print_date,
            lp.price,
            lp.price_date,
            COALESCE(NULLIF(cm.colors, ''), 'Colorless') AS colors,
            cm.cmc,
            CASE
                WHEN cm.cmc <= 2 THEN '0-2'
                WHEN cm.cmc <= 4 THEN '3-4'
                WHEN cm.cmc <= 6 THEN '5-6'
                ELSE '7+'
            END AS cmc_bucket,
            CASE
                WHEN COALESCE(ct.types, '') ILIKE '%creature%' THEN 'Creature'
                ELSE 'Non-Creature'
            END AS card_class
        FROM latest_price lp
        JOIN capstone.card c ON c.card_id = lp.card_id
        LEFT JOIN capstone.card_types ct ON ct.card_id = c.card_id
        LEFT JOIN capstone.card_mana cm ON cm.card_id = c.card_id
        WHERE lp.price IS NOT NULL
    )
    SELECT *
    FROM features
    WHERE cmc IS NOT NULL;"""
    
    with engine.connect() as conn:
        df = pd.read_sql_query(text(sql), conn)

    fig = px.box(
        df,
        x="cmc_bucket",
        y="price",
        color="card_class",
        points="all",   # show underlying points too
        hover_data=["name", "colors", "cmc", "price_date"],
        title="Price Distribution by Mana Bucket and Card Class",
        labels={"cmc_bucket": "CMC Bucket", "price": "Latest Price"}
    )

    # fig.update_yaxes(type="log")  # optional: helps if prices are highly skewed
    fig.update_layout(boxmode="group")
    return fig


def get_price_volatility_by_color():
    sql = """WITH priced_cards AS (
    SELECT
        DATE_TRUNC('week', cp."date")::date AS week_start,
        CASE
            WHEN cm.color_id IS NULL OR BTRIM(cm.color_id) = '' THEN 0
            ELSE CARDINALITY(STRING_TO_ARRAY(REPLACE(cm.color_id, ' ', ''), ','))
        END AS color_count,
        cp.price
    FROM capstone.card_price cp
    JOIN capstone.card_mana cm ON cm.card_id = cp.card_id
)
SELECT
    week_start,
    CASE
        WHEN color_count = 0 THEN 'Colorless'
        WHEN color_count = 1 THEN 'Mono-colored'
        ELSE color_count::text || ' colors'
    END AS color_amount,
    STDDEV_SAMP(price) AS price_volatility,
    COUNT(*) AS sample_size
FROM priced_cards
GROUP BY 1, 2
HAVING COUNT(*) >= 3
ORDER BY 1, 2;"""

    with engine.connect() as conn:
        df = pd.read_sql_query(text(sql), conn)

    if df.empty:
        return px.scatter(title="Price Volatility Over Time by Color Amount (no data after grouping)")

    fig = px.line(
        df,
        x="week_start",
        y="price_volatility",
        color="color_amount",
        hover_data=["sample_size"],
        title="Weekly Price Volatility by Color Amount",
        labels={"price_volatility": "Price Volatility (Std Dev)", "week_start": "Week"},
    )
    fig.update_xaxes(type="date", tickformat="%Y-%m-%d")
    return fig


def get_four_color_anomaly_component():
    sql = """WITH priced_cards AS (
    SELECT
        cp."date"::date AS price_date,
        DATE_TRUNC('week', cp."date")::date AS week_start,
        cp.card_id,
        c.name,
        cp.price,
        CASE
            WHEN cm.color_id IS NULL OR BTRIM(cm.color_id) = '' THEN 0
            ELSE CARDINALITY(STRING_TO_ARRAY(REPLACE(cm.color_id, ' ', ''), ','))
        END AS color_count
    FROM capstone.card_price cp
    JOIN capstone.card_mana cm ON cm.card_id = cp.card_id
    JOIN capstone.card c ON c.card_id = cp.card_id
),
four_color_weekly AS (
    SELECT
        week_start,
        AVG(price) AS week_avg_price,
        STDDEV_SAMP(price) AS week_stddev_price,
        COUNT(*) AS sample_size
    FROM priced_cards
    WHERE color_count = 4
    GROUP BY week_start
    HAVING COUNT(*) >= 3
),
peak_week AS (
    SELECT *
    FROM four_color_weekly
    ORDER BY week_stddev_price DESC NULLS LAST
    LIMIT 1
)
SELECT
    p.week_start,
    p.price_date,
    p.card_id,
    p.name,
    p.price,
    pw.week_avg_price,
    pw.week_stddev_price,
    pw.sample_size,
    ABS(p.price - pw.week_avg_price) AS abs_deviation
FROM priced_cards p
JOIN peak_week pw ON pw.week_start = p.week_start
WHERE p.color_count = 4
ORDER BY abs_deviation DESC, p.price DESC
LIMIT 25;"""

    with engine.connect() as conn:
        df = pd.read_sql_query(text(sql), conn)

    if df.empty:
        return html.Div(
            "No 4-color anomaly rows found (not enough 4-color samples per week).",
            style={"padding": "1rem", "width": "95%"},
        )

    peak_week = str(df.loc[0, "week_start"])
    peak_stddev = float(df.loc[0, "week_stddev_price"])
    sample_size = int(df.loc[0, "sample_size"])

    display_df = df.copy()
    for col in ["price", "week_avg_price", "week_stddev_price", "abs_deviation"]:
        display_df[col] = display_df[col].round(2)

    return html.Div(
        [
            html.H4("4-Color Volatility Outlier Drilldown"),
            html.P(
                f"Peak week: {peak_week} | Weekly std dev: {peak_stddev:.2f} | Sample size: {sample_size}. "
                "Rows are sorted by absolute deviation from that week's average price."
            ),
            dash_table.DataTable(
                columns=[{"name": c, "id": c} for c in display_df.columns],
                data=display_df.to_dict("records"),
                page_size=10,
                sort_action="native",
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "padding": "6px"},
            ),
        ],
        style={"padding": "1rem", "width": "95%"},
    )


def get_price_by_era_and_cmc():
    sql = """WITH latest_price AS (
    SELECT DISTINCT ON (cp.card_id)
        cp.card_id,
        cp.price,
        cp."date" AS price_date
    FROM capstone.card_price cp
    ORDER BY cp.card_id, cp."date" DESC
)
SELECT
    c.card_id,
    c.name,
    c.print_date,
    lp.price,
    cm.cmc,
    CASE
        WHEN cm.cmc <= 2 THEN '0-2'
        WHEN cm.cmc <= 4 THEN '3-4'
        WHEN cm.cmc <= 6 THEN '5-6'
        ELSE '7+'
    END AS cmc_bucket,
    CASE
        WHEN c.print_date < DATE '2000-01-01' THEN 'pre-2000'
        WHEN c.print_date < DATE '2010-01-01' THEN '2000s'
        WHEN c.print_date < DATE '2020-01-01' THEN '2010s'
        ELSE '2020+'
    END AS print_era
FROM latest_price lp
JOIN capstone.card c ON c.card_id = lp.card_id
JOIN capstone.card_mana cm ON cm.card_id = lp.card_id
WHERE c.print_date IS NOT NULL
  AND lp.price IS NOT NULL
  AND cm.cmc IS NOT NULL;"""

    with engine.connect() as conn:
        df = pd.read_sql_query(text(sql), conn)

    fig = px.box(
        df,
        x="cmc_bucket",
        y="price",
        color="print_era",
        points="all",
        hover_data=["name", "cmc", "print_date"],
        title="Price by Print Era Within CMC Buckets",
        labels={"cmc_bucket": "CMC Bucket", "price": "Latest Price", "print_era": "Print Era"},
    )
    fig.update_layout(boxmode="group")
    fig.update_yaxes(type="log")
    return fig
    

power_fig_pre_2010, power_fig_post_2010, power_fig_combined = get_power_creep()
four_color_anomaly_component = get_four_color_anomaly_component()
app.layout = [   
    html.Div([
        dcc.Graph(id="power_pre_2010",figure=power_fig_pre_2010)],
        style={"display": "flex", "justifyContent": "center", "alignItems": "center", "height": "100vh"}),
    html.Div([
        dcc.Graph(id="power_post_2010",figure=power_fig_post_2010)],
        style={"display": "flex", "justifyContent": "center", "alignItems": "center", "height": "100vh"}),
    html.Div([
        dcc.Graph(id="power_combined",figure=power_fig_combined)],
        style={"display": "flex", "justifyContent": "center", "alignItems": "center", "height": "100vh"}),
    html.Div([
        dcc.Graph(id="complexity",figure=get_complexity_creep())],
        style={"display": "flex", "justifyContent": "center", "alignItems": "center", "height": "100vh"}),
    html.Div([
        dcc.Graph(id="price_characteristic",figure=get_price_by_characteristic())],
        style={"display": "flex", "justifyContent": "center", "alignItems": "center", "height": "100vh"}),
    html.Div([
        dcc.Graph(id="price_volatility_color",figure=get_price_volatility_by_color())],
        style={"display": "flex", "justifyContent": "center", "alignItems": "center", "height": "100vh"}),
    html.Div([
        four_color_anomaly_component],
        style={"display": "flex", "justifyContent": "center", "alignItems": "flex-start", "minHeight": "35vh"}),
    html.Div([
        dcc.Graph(id="price_era_cmc",figure=get_price_by_era_and_cmc())],
        style={"display": "flex", "justifyContent": "center", "alignItems": "center", "height": "100vh"}),
    ]

if __name__ == "__main__":
    app.run(debug=True)
