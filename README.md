# Ashoka Industries — Business Analytics Dashboard

Streamlit dashboard for Ashoka Industries, Hoshiarpur, Punjab. Existing pages,
date filters, KPIs, charts, insights, and add/edit/delete management sections
are retained. Supabase is the cloud database; MySQL is needed only for the
one-time data transfer.

## 1. Install and configure locally

```powershell
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Keep any existing `.env` (it may contain your local MySQL settings), and add
your Supabase project URL and **server-side secret/service-role key** to it.
Do not commit `.env`.
The publishable API key is not a substitute for the server-side key because
the app needs private table access and CRUD. Do not put a service-role/secret
key in source code, a public repository, or browser-side code.

## 2. Create the Supabase tables

In the Supabase project, open **SQL Editor**, paste the contents of
[`sql/schema_setup.sql`](./sql/schema_setup.sql), and run it. It creates the
four tables (`sales`, `purchases`, `consumables`, `sales_adjustments`) and
enables row-level security without granting anonymous or authenticated users
access. The Streamlit server connects using the server-side key.

## 3. Transfer existing MySQL data

Make sure the local MySQL database is running and `.env` points to the
database containing your current records. Then run:

```powershell
python migrate_to_supabase.py
```

The script copies all four tables in batches, preserves each primary-key ID,
and verifies that Supabase confirms every row. It uses upsert, so it can be
rerun safely after an interrupted transfer; it does not delete source records.
The source MySQL dependency is retained for this one-time script.

After a successful transfer, run these statements in Supabase SQL Editor so
newly added records receive IDs above the imported IDs:

```sql
SELECT setval(pg_get_serial_sequence('public.sales', 'sale_id'),
    GREATEST(COALESCE((SELECT MAX(sale_id) FROM public.sales), 1), 1),
    EXISTS (SELECT 1 FROM public.sales));
SELECT setval(pg_get_serial_sequence('public.purchases', 'purchase_id'),
    GREATEST(COALESCE((SELECT MAX(purchase_id) FROM public.purchases), 1), 1),
    EXISTS (SELECT 1 FROM public.purchases));
SELECT setval(pg_get_serial_sequence('public.consumables', 'consumable_id'),
    GREATEST(COALESCE((SELECT MAX(consumable_id) FROM public.consumables), 1), 1),
    EXISTS (SELECT 1 FROM public.consumables));
SELECT setval(pg_get_serial_sequence('public.sales_adjustments', 'adjustment_id'),
    GREATEST(COALESCE((SELECT MAX(adjustment_id) FROM public.sales_adjustments), 1), 1),
    EXISTS (SELECT 1 FROM public.sales_adjustments));
```

## 4. Run locally

```powershell
streamlit run app.py
```

The sidebar shows whether Supabase is connected. Table data is fetched through
the Supabase API in pages and cached briefly; management writes clear the
dashboard cache so the updated records appear immediately.

## 5. Deploy on Streamlit Community Cloud

1. Push the code (not `.env` or transaction exports) to the GitHub repository.
2. Create or reopen the app in Streamlit Community Cloud, select the repository,
   branch, and `app.py`.
3. In **App settings → Secrets**, add TOML using your project URL and the
   server-side key from **Supabase → Project Settings → API Keys → Secret key**
   (or the legacy `service_role` key):

   ```toml
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_SERVICE_ROLE_KEY = "your-server-side-secret-key"
   ```

4. Set the Streamlit app access to **Private** and invite only intended users.
   The app has no separate login, so anyone allowed to open it can use its
   dashboard and management pages.
5. Deploy/reboot the app. Streamlit Cloud installs `requirements.txt`
   automatically. Confirm the sidebar reports **Database: Connected**, then
   check the date range, KPIs, charts, and each management section.

Keep the server-side key only in Streamlit Secrets or an environment variable.
Never add it to GitHub. Do not add permissive anonymous Supabase policies for
these business records.

## Data privacy

The repository contains application code and an empty schema only. Transaction
records remain in the configured databases; no customer-specific data or
credentials should be committed.
