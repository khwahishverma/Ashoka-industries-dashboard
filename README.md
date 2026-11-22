# Ashoka Industries — Business Analytics Dashboard
**MKT322 (Advanced Business Analytics) — Academic Task 1**

Sales, Purchase and Consumable Expenditure Analytics for Data-Driven Decision Making at Ashoka Industries, Hoshiarpur, Punjab.

---

## 1. Project structure

```
ashoka_industries_dashboard/
├── app.py            # Streamlit UI - analytics and management sections
├── database.py       # Live MySQL connection (cached, error-handled)
├── queries.py        # All SQL retrieval, one function per analysis
├── insights.py       # Dynamic, data-driven findings/recommendations (no hard-coded text)
├── management.py     # Create, view, update and delete operations for management pages
├── utils.py          # Indian currency/date formatting helpers
├── requirements.txt
├── .env.example      # Copy to .env and fill in your MySQL credentials
├── README.md
└── sql/
    └── schema_setup.sql   # Table definitions only; no transaction data
```

**Why this structure differs slightly from the suggested one:** `utils.py` and `insights.py` were split out from `app.py` so that (a) currency/date formatting is identical across every page instead of being redefined per-section, and (b) the "insights" logic — which reads live query results and turns them into plain-language findings — is testable and reusable on its own, separate from UI rendering code. Nothing else changed.

---

## 2. One-time setup

### 2.1 Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2.2 Set up the MySQL database
1. Make sure MySQL Server is running locally.
2. Run the schema script (this is the exact script you already wrote and verified):
   ```bash
   mysql -u root -p < sql/schema_setup.sql
   ```
   This creates the `ashoka_industries` database and its four empty tables. No business transaction data is included in this public repository.
3. Import your three CSVs into their matching tables. Easiest via MySQL Workbench's **Table Data Import Wizard** (right-click table → Import Data), pointing at:
   - `Ashoka_Sales_MySQL_Import.csv` → `sales`
   - `Ashoka_Purchases_MySQL_Import.csv` → `purchases`
   - `Ashoka_Consumables_MySQL_Import.csv` → `consumables`

   (If you already imported these during your SQL phase and the database still exists, you can skip steps 2–3 — just point `.env` at that existing database instead of re-running `schema_setup.sql`, which would drop it.)

### 2.3 Configure credentials
```bash
cp .env.example .env
```
Then edit `.env` with your actual MySQL username/password.

---

## 3. Running the dashboard

```bash
streamlit run app.py
```
This opens the dashboard in your browser (usually `http://localhost:8501`). The sidebar shows a live "Database: Connected" indicator — if it shows "Not connected," double-check `.env`.

### Deploy to Streamlit Community Cloud

1. In Streamlit Community Cloud, choose **Create app**, then select this repository, the `main` branch, and `app.py`.
2. In **Advanced settings → Secrets**, add the following TOML using credentials for a hosted MySQL database:

   ```toml
   DB_HOST = "your-mysql-host"
   DB_PORT = 3306
   DB_USER = "your-mysql-user"
   DB_PASSWORD = "your-mysql-password"
   DB_NAME = "ashoka_industries"
   ```

3. Deploy the app. Do not commit real credentials or transaction CSVs.

The database must be hosted at a network address reachable from Community Cloud. `localhost` refers to the cloud app's own container, not your computer. Import authorized transaction data into the hosted database separately; the public repository includes only an empty schema.

---

## 4. Data privacy

The public repository contains application code and an empty database schema only. Business transaction records, customer details, credentials, and raw CSV data are excluded. Load authorized data into your local MySQL database to use the analytics features.

---

## 5. Screenshots to take for your report/submission

Set the date filter to the full available data range for these unless noted:

1. **Executive Overview** — full page (executive summary + 7 KPI cards + trend chart)
2. **Sales Analytics** — trend + comparison charts side by side
3. **Sales Analytics** — Monthly Sales Ranking table
4. **Sales Analytics** — Top 10 Highest-Value Sales table
5. **Sales Analytics** — Customer-Wise Sales + Sales Value Classification chart
6. **Sales Analytics** — Cumulative Sales chart
7. **Sales Analytics** — Accounting Adjustments table (shows you handled these correctly, separately)
8. **Procurement Analytics** — full page (KPIs + monthly chart + item breakdown)
9. **Consumables Analytics** — full page (KPIs + monthly trend + item breakdown + top 5)
10. **Business Insights & Recommendations** — Sales vs Purchases comparison chart
11. **Business Insights & Recommendations** — Findings/recommendations blocks
12. **Business Insights & Recommendations** — Key Conclusions + Limitations/Future Scope
13. One screenshot with the **date filter narrowed** (e.g. just Q1) to demonstrate interactivity — show the KPIs changing

---

## 6. Dashboard explanation for viva/presentation

**When asked "walk me through your dashboard":**
- "The dashboard connects live to my MySQL database — I'm not displaying static numbers, every KPI and chart runs a query against `ashoka_industries` when the page loads."
- "The sidebar date filter drives everything below it — KPIs, charts, tables, and even the written insights all recompute for whatever range is selected."
- "I deliberately avoided calling anything 'profit' — the dataset only has sales and purchase transaction values, not cost-of-production or inventory data, so I labeled the comparison section 'Sales vs Purchase Value' instead."
- "Accounting adjustments are displayed separately from normal sales figures."
- "The Business Insights page doesn't just show charts — for each finding, I state the finding, its implication, and a recommended action, and all of that text is generated dynamically from the query results, not typed in as static content."

Customer-specific findings are generated from the private database at runtime and are not published in this repository.

---

## 7. Public data boundary

The public repository intentionally omits report-ready figures, customer-specific findings, and source transaction data. The dashboard calculates insights from the database configured by each user at runtime.
