import pandas as pd
import plotly.express as px
import streamlit as st
from databricks import sql

st.set_page_config(page_title="Attention Radar", layout="wide")

REFERENCE_LABS = ["anthropic", "openai", "xai", "google_deepmind", "meta_ai", "microsoft_ai"]


@st.cache_resource
def get_connection():
    return sql.connect(
        server_hostname=st.secrets["DATABRICKS_SERVER_HOSTNAME"],
        http_path=st.secrets["DATABRICKS_HTTP_PATH"],
        access_token=st.secrets["DATABRICKS_TOKEN"],
    )


@st.cache_data(ttl=3600)
def run_query(query: str) -> pd.DataFrame:
    with get_connection().cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
    return pd.DataFrame(rows, columns=columns)


STATUS_SQL = """
SELECT MAX(day_utc) AS latest_full_day, COUNT(DISTINCT entity_id) AS companies_scored
FROM workspace.default.pageviews_zscore
WHERE z IS NOT NULL
"""

FLAGGED_SQL = """
SELECT REPLACE(en_wikipedia_title, '_', ' ') AS company, day_utc, views, z
FROM workspace.default.flagged_days
ORDER BY day_utc DESC, z DESC
"""

LATEST_SQL = """
SELECT entity_id, REPLACE(en_wikipedia_title, '_', ' ') AS company, z
FROM workspace.default.pageviews_zscore
WHERE z IS NOT NULL
  AND day_utc = (SELECT MAX(day_utc) FROM workspace.default.pageviews_zscore WHERE z IS NOT NULL)
"""

DAILY_VIEWS_SQL = """
SELECT entity_id, day_utc, views
FROM workspace.default.pageviews_silver_daily
WHERE entity_id IN ('anthropic', 'openai', 'ssi')
ORDER BY day_utc
"""

HEATMAP_SQL = """
SELECT REPLACE(en_wikipedia_title, '_', ' ') AS company, day_utc, z
FROM workspace.default.pageviews_zscore
WHERE z IS NOT NULL
  AND day_utc >= date_sub((SELECT MAX(day_utc) FROM workspace.default.pageviews_zscore WHERE z IS NOT NULL), 14)
"""

st.title("Attention Radar")
st.caption("Wikipedia pageviews for AI companies, compared with each company's own last 30 days.")

status = run_query(STATUS_SQL)
flagged = run_query(FLAGGED_SQL)

col1, col2 = st.columns(2)
col1.metric("Latest full day loaded", str(status["latest_full_day"].iloc[0]))
col2.metric("Companies scored", int(status["companies_scored"].iloc[0]))

st.subheader(f"Spikes flagged: {len(flagged)}")
st.caption("A spike is a day where z-score is above 3.")
st.dataframe(
    flagged,
    hide_index=True,
    use_container_width=True,
    column_config={
        "views": st.column_config.NumberColumn("Views", format="%d"),
        "z": st.column_config.NumberColumn("z-score", format="%.2f"),
    },
)

st.subheader("Latest day's z-score by company")
latest = run_query(LATEST_SQL)
latest["group"] = latest["entity_id"].isin(REFERENCE_LABS).map(
    {True: "Reference lab", False: "Startup"}
)
for group_name in ["Reference lab", "Startup"]:
    part = latest[latest["group"] == group_name].sort_values("z")
    fig_bar = px.bar(
        part,
        x="z",
        y="company",
        orientation="h",
        height=max(250, 24 * len(part)),
        labels={"z": "z-score", "company": ""},
    )
    st.markdown(f"**{group_name}s**" if group_name == "Startup" else "**Reference labs**")
    st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("Daily views: Anthropic, OpenAI and SSI")
daily = run_query(DAILY_VIEWS_SQL)
fig_line = px.line(
    daily,
    x="day_utc",
    y="views",
    color="entity_id",
    log_y=True,
    labels={"views": "Views (log scale)", "day_utc": "Day"},
)
st.plotly_chart(fig_line, use_container_width=True)

st.subheader("Daily z-score heatmap, all companies")
heat = run_query(HEATMAP_SQL)
pivot = heat.pivot(index="company", columns="day_utc", values="z")
fig_heat = px.imshow(
    pivot,
    color_continuous_scale="RdBu_r",
    color_continuous_midpoint=0,
    aspect="auto",
    labels={"color": "z-score", "x": "Day", "y": ""},
    height=max(500, 20 * len(pivot)),
)
st.plotly_chart(fig_heat, use_container_width=True)
