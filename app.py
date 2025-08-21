# app.py
from pathlib import Path
from datetime import datetime, date
import pandas as pd
import streamlit as st
import plotly.express as px
import sqlite3

# Connect to SQLite
conn = sqlite3.connect("lfwms.db", check_same_thread=False)

@st.cache_data
def fetch_df(sql, params=None):
    return pd.read_sql_query(sql, conn, params=params or [])

# Page Config
st.set_page_config(
    page_title="Local Food Wastage Management System",
    page_icon="🍲",
    layout="wide"
)

# Light Green CSS
# Light Green CSS Theme
st.markdown("""
<style>
/* Main background */
.stApp {
    background-color: #f5fff5; /* very light green */
    color: #333333;
    font-family: 'Segoe UI', sans-serif;
}

/* Sidebar */
.css-1d391kg, .css-1cypcdb {
    background-color: #e6ffe6 !important; /* light green sidebar */
    color: #333333 !important;
}

/* Headers */
h1, h2, h3, h4 {
    color: #006600; /* dark green */
    font-weight: bold;
}

/* Buttons */
.stButton>button {
    background-color: #4CAF50; /* medium green */
    color: white;
    border-radius: 8px;
    border: none;
    padding: 0.6em 1.2em;
    font-size: 1em;
    transition: 0.3s;
}

.stButton>button:hover {
    background-color: #45a049; /* darker on hover */
}

/* DataFrames (tables) */
.css-1offfwp, .css-1q8dd3e {
    background-color: #ffffff !important; 
    border: 1px solid #b3ffb3;
    border-radius: 6px;
}

/* Inputs (select, text, etc.) */
.stTextInput>div>div>input,
.stSelectbox>div>div>select {
    border: 1px solid #66cc66;
    border-radius: 6px;
    padding: 6px;
}
</style>
""", unsafe_allow_html=True)


# Helper Functions for DB
DB_PATH = Path(__file__).resolve().parent / "lfwms.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@st.cache_data(show_spinner=False)
def fetch_df(sql, params=None):
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params or [])

def exec_sql(sql, params=None):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or [])
        conn.commit()

def exec_many(sql, rows):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.executemany(sql, rows)
        conn.commit()

# Sidebar
st.sidebar.title("🍲 LFWMS")
page = st.sidebar.radio("Navigate", [
    "Dashboard",
    "Browse Listings",
    "Manage Listings & Claims",
    "Providers",
    "Receivers",
    "SQL Explorer"
])

# KPI Row
def kpi_row():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Providers", int(fetch_df("SELECT COUNT(*) as c FROM Providers")["c"][0]))
    c2.metric("Receivers", int(fetch_df("SELECT COUNT(*) as c FROM Receivers")["c"][0]))
    c3.metric("Listings", int(fetch_df("SELECT COUNT(*) as c FROM Food_Listings")["c"][0]))
    c4.metric("Claims", int(fetch_df("SELECT COUNT(*) as c FROM Claims")["c"][0]))

# ------------------- Dashboard -------------------
if page == "Dashboard":
    st.title("📊 Dashboard")
    kpi_row()
    st.markdown("---")

    claims = fetch_df("""
        SELECT date(Timestamp) AS Day, COUNT(*) AS Count
        FROM Claims
        GROUP BY date(Timestamp)
        ORDER BY Day;
    """)
    if not claims.empty:
        fig = px.line(claims, x="Day", y="Count", markers=True, title="Claims Over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No claims data available to plot.")

    c1, c2 = st.columns(2)

    with c1:
        status = fetch_df("""
            SELECT Status, COUNT(*) AS Count
            FROM Claims
            GROUP BY Status;
        """)
        if not status.empty:
            st.subheader("Claims by Status")
            fig = px.pie(status, names="Status", values="Count", hole=0.45)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        ft = fetch_df("""
            SELECT fl.Food_Type, COUNT(*) AS Count
            FROM Food_Listings fl
            GROUP BY fl.Food_Type;
        """)
        if not ft.empty:
            st.subheader("Listings by Food Type")
            fig2 = px.bar(ft, x="Food_Type", y="Count")
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    st.subheader("⏰ Near-Expiry Items (next 3 days)")
    near = fetch_df("""
        SELECT fl.Food_ID, fl.Food_Name, fl.Quantity, fl.Expiry_Date, 
               fl.Location, fl.Provider_ID
        FROM Food_Listings fl
        WHERE date(fl.Expiry_Date) <= date('now', '+3 day')
        ORDER BY fl.Expiry_Date;
    """)
    st.dataframe(near, use_container_width=True)

# ------------------- Browse Listings -------------------
elif page == "Browse Listings":
    st.title("🥦 Browse Listings")
    kpi_row()
    st.markdown("---")

    cities = fetch_df("SELECT DISTINCT fl.Location as City FROM Food_Listings fl ORDER BY City;")["City"].dropna().tolist()
    providers = fetch_df("SELECT DISTINCT fl.Provider_ID FROM Food_Listings fl ORDER BY fl.Provider_ID;")["Provider_ID"].dropna().tolist()
    food_types = fetch_df("SELECT DISTINCT fl.Food_Type FROM Food_Listings fl ORDER BY fl.Food_Type;")["Food_Type"].dropna().tolist()
    meal_types = fetch_df("SELECT DISTINCT fl.Meal_Type FROM Food_Listings fl ORDER BY fl.Meal_Type;")["Meal_Type"].dropna().tolist()

    fc1, fc2, fc3, fc4 = st.columns(4)
    sel_city = fc1.multiselect("City", options=cities)
    sel_provider = fc2.multiselect("Provider ID", options=providers)
    sel_foodtype = fc3.multiselect("Food Type", options=food_types)
    sel_meal = fc4.multiselect("Meal Type", options=meal_types)

    where = []
    params = []

    if sel_city:
        where.append("fl.Location IN (%s)" % ",".join(["?"] * len(sel_city)))
        params += sel_city
    if sel_provider:
        where.append("fl.Provider_ID IN (%s)" % ",".join(["?"] * len(sel_provider)))
        params += sel_provider
    if sel_foodtype:
        where.append("fl.Food_Type IN (%s)" % ",".join(["?"] * len(sel_foodtype)))
        params += sel_foodtype
    if sel_meal:
        where.append("fl.Meal_Type IN (%s)" % ",".join(["?"] * len(sel_meal)))
        params += sel_meal

    base_sql = """
    SELECT fl.Food_ID, fl.Food_Name, fl.Quantity, fl.Expiry_Date, fl.Location,
           fl.Food_Type, fl.Meal_Type,
           p.Provider_ID, p.Name as Provider_Name, p.Contact as Provider_Contact
    FROM Food_Listings fl
    LEFT JOIN Providers p ON p.Provider_ID = fl.Provider_ID
    """
    if where:
        base_sql += " WHERE " + " AND ".join(where)
    base_sql += " ORDER BY date(fl.Expiry_Date) ASC;"

    listings = fetch_df(base_sql, params)
    st.dataframe(listings, use_container_width=True)

# ------------------- Manage Listings & Claims -------------------
elif page == "Manage Listings & Claims":
    st.title("🛠️ Manage Listings & Claims")
    st.caption("Create, update, or delete records. All changes affect the SQLite database.")

    tabs = st.tabs(["➕ Add Listing", "✏️ Update Listing", "🗑️ Delete Listing",
                    "➕ Add Claim", "✏️ Update Claim Status", "🗑️ Delete Claim"])

    # ---- Add Listing ----
    with tabs[0]:
        st.subheader("Add New Listing")
        with st.form("add_listing"):
            food_id = st.number_input("Food_ID (unique)", min_value=1, step=1)
            food_name = st.text_input("Food_Name")
            qty = st.number_input("Quantity", min_value=1, step=1)
            exp = st.date_input("Expiry_Date", value=date.today())
            provider_id = st.number_input("Provider_ID", min_value=1, step=1)
            provider_type = st.text_input("Provider_Type")
            location = st.text_input("Location (City)")
            food_type = st.text_input("Food_Type")
            meal_type = st.text_input("Meal_Type")
            submit = st.form_submit_button("Add Listing")
        if submit:
            try:
                exec_sql("""
                    INSERT INTO Food_Listings
                    (Food_ID, Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, [food_id, food_name, qty, str(exp), provider_id, provider_type, location, food_type, meal_type])
                st.success("Listing added.")
            except sqlite3.IntegrityError as e:
                st.error(f"DB error: {e}")

    # ---- Update Listing ----
    with tabs[1]:
        st.subheader("Update Listing")
        ids = fetch_df("SELECT fl.Food_ID FROM Food_Listings fl ORDER BY fl.Food_ID;")["Food_ID"].tolist()
        if ids:
            sel = st.selectbox("Select Food_ID", ids)
            current = fetch_df("SELECT * FROM Food_Listings WHERE Food_ID = ?;", [sel])
            if not current.empty:
                row = current.iloc[0]
                with st.form("upd_listing"):
                    food_name = st.text_input("Food_Name", row["Food_Name"])
                    qty = st.number_input("Quantity", min_value=1, step=1, value=int(row["Quantity"]))
                    exp = st.date_input("Expiry_Date", value=pd.to_datetime(row["Expiry_Date"]).date())
                    provider_id = st.number_input("Provider_ID", min_value=1, step=1, value=int(row["Provider_ID"]))
                    provider_type = st.text_input("Provider_Type", row["Provider_Type"] or "")
                    location = st.text_input("Location", row["Location"] or "")
                    food_type = st.text_input("Food_Type", row["Food_Type"] or "")
                    meal_type = st.text_input("Meal_Type", row["Meal_Type"] or "")
                    submit = st.form_submit_button("Update")
                if submit:
                    exec_sql("""
                        UPDATE Food_Listings
                        SET Food_Name=?, Quantity=?, Expiry_Date=?, Provider_ID=?, Provider_Type=?, Location=?, Food_Type=?, Meal_Type=?
                        WHERE Food_ID=?;
                    """, [food_name, qty, str(exp), provider_id, provider_type, location, food_type, meal_type, sel])
                    st.success("Listing updated.")
        else:
            st.info("No listings to update.")

    # ---- Delete Listing ----
    with tabs[2]:
        st.subheader("Delete Listing")
        ids = fetch_df("SELECT fl.Food_ID FROM Food_Listings fl ORDER BY fl.Food_ID;")["Food_ID"].tolist()
        if ids:
            sel = st.selectbox("Food_ID to delete", ids, key="del_listing")
            if st.button("Delete Listing", type="primary"):
                exec_sql("DELETE FROM Food_Listings WHERE Food_ID=?;", [sel])
                st.success(f"Listing {sel} deleted.")
        else:
            st.info("No listings to delete.")

    # ---- Add Claim ----
    with tabs[3]:
        st.subheader("Add Claim")
        with st.form("add_claim"):
            claim_id = st.number_input("Claim_ID (unique)", min_value=1, step=1)
            food_id = st.number_input("Food_ID", min_value=1, step=1, key="ac_food")
            receiver_id = st.number_input("Receiver_ID", min_value=1, step=1)
            status = st.selectbox("Status", ["Pending", "Completed", "Cancelled"])
            ts = st.text_input("Timestamp (ISO)", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            submit = st.form_submit_button("Add Claim")
        if submit:
            try:
                exec_sql("""
                    INSERT INTO Claims (Claim_ID, Food_ID, Receiver_ID, Status, Timestamp)
                    VALUES (?, ?, ?, ?, ?);
                """, [claim_id, food_id, receiver_id, status, ts])
                st.success("Claim added.")
            except sqlite3.IntegrityError as e:
                st.error(f"DB error: {e}")

    # ---- Update Claim Status ----
    with tabs[4]:
        st.subheader("Update Claim Status")
        ids = fetch_df("SELECT c.Claim_ID FROM Claims c ORDER BY c.Claim_ID;")["Claim_ID"].tolist()
        if ids:
            sel = st.selectbox("Select Claim_ID", ids)
            st.write(fetch_df("SELECT * FROM Claims WHERE Claim_ID=?;", [sel]))
            new_status = st.selectbox("New Status", ["Pending", "Completed", "Cancelled"], key="uc_status")
            if st.button("Update Status"):
                exec_sql("UPDATE Claims SET Status=? WHERE Claim_ID=?;", [new_status, sel])
                st.success("Status updated.")
        else:
            st.info("No claims to update.")

    # ---- Delete Claim ----
    with tabs[5]:
        st.subheader("Delete Claim")
        ids = fetch_df("SELECT c.Claim_ID FROM Claims c ORDER BY c.Claim_ID;")["Claim_ID"].tolist()
        if ids:
            sel = st.selectbox("Claim_ID to delete", ids, key="del_claim")
            if st.button("Delete Claim", type="primary"):
                exec_sql("DELETE FROM Claims WHERE Claim_ID=?;", [sel])
                st.success(f"Claim {sel} deleted.")
        else:
            st.info("No claims to delete.")

# ------------------- Providers Page -------------------
elif page == "Providers":
    st.title("🏢 Providers")
    st.dataframe(fetch_df("SELECT * FROM Providers ORDER BY Provider_ID;"), use_container_width=True)

# ------------------- Receivers Page -------------------
elif page == "Receivers":
    st.title("🙋 Receivers")
    st.dataframe(fetch_df("SELECT * FROM Receivers ORDER BY Receiver_ID;"), use_container_width=True)

# ------------------- SQL Explorer -------------------
elif page == "SQL Explorer":
    st.title("🛠️ SQL Explorer")
    st.caption("Run custom SQL queries directly on the database.")

    query = st.text_area("Enter SQL Query", height=150, placeholder="e.g., SELECT * FROM Providers LIMIT 5;")

    if st.button("Run Query", type="primary"):
        try:
            df = fetch_df(query)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                with st.expander("Preview as Chart"):
                    if st.checkbox("Enable Chart View"):
                        st.bar_chart(df.select_dtypes(include="number"))
            else:
                st.info("✅ Query executed, but no rows returned.")
        except Exception as e:
            st.error(f"❌ Error: {e}")

