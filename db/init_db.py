import sqlite3
import pandas as pd

# File paths
providers_csv = "data/providers_data.csv"
receivers_csv = "data/receivers_data.csv"
food_listings_csv = "data/food_listings_data.csv"
claims_csv = "data/claims_data.csv"

# Connect to SQLite (creates file if not exists)
conn = sqlite3.connect("lfwms.db")
cursor = conn.cursor()

# Load CSVs into pandas
providers = pd.read_csv(providers_csv)
receivers = pd.read_csv(receivers_csv)
food_listings = pd.read_csv(food_listings_csv)
claims = pd.read_csv(claims_csv)

# Save to database
providers.to_sql("Providers", conn, if_exists="replace", index=False)
receivers.to_sql("Receivers", conn, if_exists="replace", index=False)
food_listings.to_sql("Food_Listings", conn, if_exists="replace", index=False)
claims.to_sql("Claims", conn, if_exists="replace", index=False)

print("✅ Database initialized successfully with all 4 tables!")

conn.close()
