# Local Food Wastage Management System (LFWMS) 🍲

Streamlit + SQLite project to connect surplus food providers with receivers, analyze trends, and reduce food waste.

## Features
- Dashboard KPIs and charts (claims over time, status distribution, listings by food type)
- Browse & filter listings (city, provider, food type, meal type)
- Full CRUD for listings & claims
- SQL Explorer (15+ queries)
- Light green themed UI

## Quickstart
```bash
# Create venv (Windows)
python -m venv .venv
.venv\Scripts\activate

# Install deps
pip install -r requirements.txt

# (Re)create SQLite DB from CSVs
python db\init_db.py

# Run app
streamlit run app.py
