"""
app.py
------
Ashoka Industries — Sales, Purchase and Consumable Expenditure
Analytics Dashboard (MKT322, Academic Task 1).

Run with:  streamlit run app.py
"""

from datetime import date

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

import database as db
import queries as q
import insights as ins
import management as crud
from utils import format_inr, format_lakh, format_qty, format_date_pretty, month_label

# ----------------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Ashoka Industries | Business Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# Design system - premium dark navy / charcoal palette, single teal accent
# ----------------------------------------------------------------------------
NAVY = "#0B1524"
CARD = "#121F33"
CARD_BORDER = "#1F2E45"
ACCENT = "#2DD4BF"
ACCENT_SOFT = "rgba(45, 212, 191, 0.12)"
TEXT_PRIMARY = "#F1F5F9"
TEXT_MUTED = "#94A3B8"
NEGATIVE = "#F87171"

CHART_TEMPLATE = "plotly_dark"
CHART_COLORWAY = [ACCENT, "#38BDF8", "#A78BFA", "#FBBF24", "#F87171"]

st.markdown(f"""
<style>
    .stApp {{
        background-color: {NAVY};
        color: {TEXT_PRIMARY};
    }}
    section[data-testid="stSidebar"] {{
        background-color: #0E1B2E;
        border-right: 1px solid {CARD_BORDER};
    }}
    h1, h2, h3, h4 {{
        color: {TEXT_PRIMARY} !important;
        font-weight: 600 !important;
    }}
    p, span, label, div {{
        color: {TEXT_PRIMARY};
    }}
    .muted {{ color: {TEXT_MUTED}; font-size: 0.88rem; }}

    .kpi-card {{
        background-color: {CARD};
        border: 1px solid {CARD_BORDER};
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        height: 100%;
    }}
    .kpi-label {{
        color: {TEXT_MUTED};
        font-size: 0.80rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.35rem;
    }}
    .kpi-value {{
        color: {TEXT_PRIMARY};
        font-size: 1.55rem;
        font-weight: 700;
        line-height: 1.2;
    }}
    .kpi-sub {{
        color: {ACCENT};
        font-size: 0.78rem;
        margin-top: 0.3rem;
    }}

    .section-card {{
        background-color: {CARD};
        border: 1px solid {CARD_BORDER};
        border-radius: 14px;
        padding: 1.3rem 1.5rem;
        margin-bottom: 1rem;
    }}

    .insight-block {{
        background-color: {ACCENT_SOFT};
        border-left: 3px solid {ACCENT};
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.7rem;
    }}
    .insight-label {{
        color: {ACCENT};
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
    }}

    .header-title {{ font-size: 1.9rem; font-weight: 700; margin-bottom: 0; }}
    .header-sub {{ color: {TEXT_MUTED}; font-size: 0.95rem; margin-top: 0.2rem; }}

    .footer-note {{
        color: {TEXT_MUTED};
        font-size: 0.78rem;
        text-align: center;
        padding-top: 2rem;
        border-top: 1px solid {CARD_BORDER};
        margin-top: 2rem;
    }}

    div[data-testid="stDataFrame"] {{ border: 1px solid {CARD_BORDER}; border-radius: 10px; }}
</style>
""", unsafe_allow_html=True)


def kpi_card(label, value, sub=None):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {sub_html}
        </div>
    """, unsafe_allow_html=True)


def section_header(title, subtitle=None):
    st.markdown(f"### {title}")
    if subtitle:
        st.markdown(f'<p class="muted">{subtitle}</p>', unsafe_allow_html=True)


def insight_block(label, text):
    st.markdown(f"""
        <div class="insight-block">
            <div class="insight-label">{label}</div>
            <div>{text}</div>
        </div>
    """, unsafe_allow_html=True)


def style_fig(fig, height=380):
    fig.update_layout(
        template=CHART_TEMPLATE,
        plot_bgcolor=CARD,
        paper_bgcolor=CARD,
        font=dict(color=TEXT_PRIMARY, size=12),
        margin=dict(l=10, r=10, t=50, b=10),
        height=height,
        colorway=CHART_COLORWAY,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor=CARD_BORDER, showgrid=True)
    fig.update_yaxes(gridcolor=CARD_BORDER, showgrid=True)
    return fig


# ----------------------------------------------------------------------------
# Sidebar - branding, connection status, filters, navigation
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## Ashoka Industries")
    st.markdown('<p class="muted">Business Analytics Dashboard</p>', unsafe_allow_html=True)
    st.markdown("---")

    connected, status_msg = db.get_status()
    if connected:
        st.success("Database: Connected", icon="🟢")
    else:
        st.error(f"Database: Not connected", icon="🔴")
        st.caption(status_msg)

    st.markdown("---")
    st.markdown("#### Filters")

    if connected:
        min_date, max_date = q.get_date_bounds()
    else:
        min_date = max_date = date.today()

    date_range = st.date_input(
        "Select Reporting Period",
        value=(min_date, max_date),
        key="dashboard_date_filter",
    )

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_date, end_date = date_range
    elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
        start_date = end_date = date_range[0]
    elif isinstance(date_range, date):
        start_date = end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    st.markdown("---")
    page = st.radio(
        "Navigate",
        [
            "Executive Overview",
            "Sales Analytics",
            "Procurement Analytics",
            "Consumables Analytics",
            "Business Insights & Recommendations",
            "Sales Management",
            "Purchase Management",
            "Consumables Management",
            "Sales Adjustments Management",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("MKT322 — Advanced Business Analytics")
    st.caption("Academic Task 1 · Ashoka Industries, Hoshiarpur")

if not connected:
    st.warning(
        "The dashboard cannot reach the MySQL database. Verify `.env` credentials, "
        "confirm the `ashoka_industries` database is running, then refresh this page."
    )
    st.stop()

if start_date > end_date:
    st.error("Start date must be before end date.")
    st.stop()

# ----------------------------------------------------------------------------
# Shared header
# ----------------------------------------------------------------------------
st.markdown(f"""
<div class="header-title">Sales, Purchase & Consumable Expenditure Analytics</div>
<div class="header-sub">Ashoka Industries, Hoshiarpur, Punjab &nbsp;·&nbsp;
Reporting period: {format_date_pretty(start_date)} – {format_date_pretty(end_date)}</div>
""", unsafe_allow_html=True)
st.write("")


# ============================================================================
# PAGE: EXECUTIVE OVERVIEW
# ============================================================================
if page == "Executive Overview":
    section_header("Executive Summary")
    for line in ins.executive_summary_lines(start_date, end_date):
        st.markdown(f"- {line}")

    st.write("")
    section_header("Key Performance Indicators")

    total_sales = q.get_total_sales(start_date, end_date)
    total_purchases = q.get_total_purchases(start_date, end_date)
    total_consumables = q.get_total_consumables(start_date, end_date)
    total_qty = q.get_total_quantity_sold(start_date, end_date)
    txn_count = q.get_sales_transaction_count(start_date, end_date)
    avg_invoice = q.get_avg_invoice_value(start_date, end_date)
    purchase_txn = q.get_purchase_transaction_count(start_date, end_date)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Total Sales", format_inr(total_sales), format_lakh(total_sales))
    with c2:
        kpi_card("Total Purchases", format_inr(total_purchases), format_lakh(total_purchases))
    with c3:
        kpi_card("Total Consumable Expenditure", format_inr(total_consumables), format_lakh(total_consumables))
    with c4:
        kpi_card("Total Quantity Sold", format_qty(total_qty), "units")
    with c5:
        kpi_card("Sales Transactions", f"{txn_count:,}", f"{purchase_txn:,} purchase txns")

    st.write("")
    c6, c7 = st.columns(2)
    with c6:
        kpi_card("Average Invoice Value", format_inr(avg_invoice))
    with c7:
        monthly_sales = q.get_monthly_sales(start_date, end_date)
        if not monthly_sales.empty:
            hi = monthly_sales.loc[monthly_sales["monthly_sales"].idxmax()]
            lo = monthly_sales.loc[monthly_sales["monthly_sales"].idxmin()]
            kpi_card(
                "Highest / Lowest Monthly Sales",
                f"{format_inr(hi['monthly_sales'])} / {format_inr(lo['monthly_sales'])}",
                f"{month_label(hi['month'])} vs {month_label(lo['month'])}",
            )

    st.write("")
    section_header("Monthly Sales Trend")
    monthly_sales = q.get_monthly_sales(start_date, end_date)
    if not monthly_sales.empty:
        monthly_sales["month_label"] = monthly_sales["month"].apply(month_label)
        fig = go.Figure(go.Scatter(
            x=monthly_sales["month_label"], y=monthly_sales["monthly_sales"],
            mode="lines+markers", line=dict(color=ACCENT, width=3), marker=dict(size=8),
            hovertemplate="%{x}<br>Sales: ₹%{y:,.2f}<extra></extra>",
        ))
        st.plotly_chart(style_fig(fig, height=340), use_container_width=True)
    else:
        st.info("No sales data available for the selected date range.")


# ============================================================================
# PAGE: SALES ANALYTICS
# ============================================================================
elif page == "Sales Analytics":
    section_header("Monthly Sales Trend")
    monthly_sales = q.get_monthly_sales(start_date, end_date)
    if not monthly_sales.empty:
        monthly_sales["month_label"] = monthly_sales["month"].apply(month_label)
        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure(go.Scatter(
                x=monthly_sales["month_label"], y=monthly_sales["monthly_sales"],
                mode="lines+markers", line=dict(color=ACCENT, width=3), marker=dict(size=9),
                hovertemplate="%{x}<br>Sales: ₹%{y:,.2f}<extra></extra>",
            ))
            fig.update_layout(title="Monthly Sales Trend")
            st.plotly_chart(style_fig(fig), use_container_width=True)
        with col2:
            fig2 = go.Figure(go.Bar(
                x=monthly_sales["month_label"], y=monthly_sales["monthly_sales"],
                marker_color=ACCENT,
                hovertemplate="%{x}<br>Sales: ₹%{y:,.2f}<extra></extra>",
            ))
            fig2.update_layout(title="Monthly Sales Comparison")
            st.plotly_chart(style_fig(fig2), use_container_width=True)
    else:
        st.info("No sales data available for the selected date range.")

    section_header("Monthly Sales Ranking")
    ranked = q.get_monthly_sales_ranked(start_date, end_date)
    if not ranked.empty:
        ranked_display = ranked.copy()
        ranked_display["month"] = ranked_display["month"].apply(month_label)
        ranked_display["total_sales"] = ranked_display["total_sales"].apply(format_inr)
        ranked_display.columns = ["Month", "Sales Value", "Rank"]
        st.dataframe(ranked_display, use_container_width=True, hide_index=True)

    section_header("Top 10 Highest-Value Sales")
    top_sales = q.get_top_sales(start_date, end_date, n=10)
    if not top_sales.empty:
        disp = top_sales.copy()
        disp["sale_date"] = disp["sale_date"].apply(format_date_pretty)
        disp["amount"] = disp["amount"].apply(format_inr)
        disp.columns = ["Date", "Bill No.", "Customer", "Quantity", "Amount"]
        st.dataframe(disp, use_container_width=True, hide_index=True)

    col_a, col_b = st.columns(2)
    with col_a:
        section_header("Customer-Wise Sales")
        cust = q.get_customer_wise_sales(start_date, end_date)
        if not cust.empty:
            if len(cust) == 1:
                st.info(f"All recorded sales in this period are to **{cust.iloc[0]['customer_name']}**. "
                        f"The dataset does not show customer diversification.")
            disp_c = cust.copy()
            disp_c["total_sales"] = disp_c["total_sales"].apply(format_inr)
            disp_c.columns = ["Customer", "Transactions", "Quantity", "Total Sales"]
            st.dataframe(disp_c, use_container_width=True, hide_index=True)

    with col_b:
        section_header("Sales Value Classification")
        classification = q.get_sales_classification(start_date, end_date)
        if not classification.empty:
            counts = classification["sales_category"].value_counts().reindex(
                ["High Value", "Medium Value", "Lower Value"]
            ).fillna(0)
            fig3 = go.Figure(go.Bar(
                x=counts.index, y=counts.values, marker_color=[ACCENT, "#38BDF8", "#94A3B8"],
                hovertemplate="%{x}: %{y} transactions<extra></extra>",
            ))
            fig3.update_layout(title="Transactions by Value Band (₹1L / ₹2L thresholds)")
            st.plotly_chart(style_fig(fig3, height=330), use_container_width=True)

    section_header("Cumulative Sales")
    cum = q.get_cumulative_sales(start_date, end_date)
    if not cum.empty:
        cum["sale_date_fmt"] = pd.to_datetime(cum["sale_date"])
        fig4 = go.Figure(go.Scatter(
            x=cum["sale_date_fmt"], y=cum["cumulative_sales"],
            mode="lines", line=dict(color=ACCENT, width=2.5), fill="tozeroy",
            fillcolor=ACCENT_SOFT,
            hovertemplate="%{x|%d %b %Y}<br>Cumulative: ₹%{y:,.2f}<extra></extra>",
        ))
        fig4.update_layout(title="Cumulative Sales Over the Period")
        st.plotly_chart(style_fig(fig4, height=340), use_container_width=True)

    section_header("Accounting Adjustments (excluded from normal sales analysis)",
                    "Kept separate per the business's accounting treatment — not included in any KPI or chart above.")
    adj = q.get_sales_adjustments(start_date, end_date)
    if not adj.empty:
        disp_adj = adj.copy()
        disp_adj["adjustment_date"] = disp_adj["adjustment_date"].apply(format_date_pretty)
        disp_adj["amount"] = disp_adj["amount"].apply(format_inr)
        disp_adj.columns = ["Date", "Reference", "Description", "Amount", "Type"]
        st.dataframe(disp_adj, use_container_width=True, hide_index=True)


# ============================================================================
# PAGE: PROCUREMENT ANALYTICS
# ============================================================================
elif page == "Procurement Analytics":
    monthly_purchases = q.get_monthly_purchases(start_date, end_date)
    purchase_by_item = q.get_purchase_by_item(start_date, end_date)
    purchase_txn = q.get_purchase_transaction_count(start_date, end_date)
    total_purchases = q.get_total_purchases(start_date, end_date)

    c1, c2 = st.columns(2)
    with c1:
        kpi_card("Total Purchase Value", format_inr(total_purchases), format_lakh(total_purchases))
    with c2:
        kpi_card("Purchase Transactions", f"{purchase_txn:,}")

    st.write("")
    section_header("Monthly Purchase Value")
    if not monthly_purchases.empty:
        monthly_purchases["month_label"] = monthly_purchases["month"].apply(month_label)
        fig = go.Figure(go.Bar(
            x=monthly_purchases["month_label"], y=monthly_purchases["monthly_purchases"],
            marker_color="#38BDF8",
            hovertemplate="%{x}<br>Purchases: ₹%{y:,.2f}<extra></extra>",
        ))
        st.plotly_chart(style_fig(fig, height=350), use_container_width=True)
    else:
        st.info("No purchase data available for the selected date range.")

    section_header("Purchase Value by Item")
    if not purchase_by_item.empty:
        fig2 = go.Figure(go.Bar(
            y=purchase_by_item["item_name"], x=purchase_by_item["total_purchase_value"],
            orientation="h", marker_color="#38BDF8",
            hovertemplate="%{y}<br>Value: ₹%{x:,.2f}<extra></extra>",
        ))
        fig2.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(style_fig(fig2, height=max(300, 40 * len(purchase_by_item))), use_container_width=True)

        disp = purchase_by_item.copy()
        disp["total_purchase_value"] = disp["total_purchase_value"].apply(format_inr)
        disp.columns = ["Item", "Purchase Records", "Total Purchase Value"]
        st.dataframe(disp, use_container_width=True, hide_index=True)


# ============================================================================
# PAGE: CONSUMABLES ANALYTICS
# ============================================================================
elif page == "Consumables Analytics":
    monthly_consumables = q.get_monthly_consumables(start_date, end_date)
    consumable_by_item = q.get_consumable_by_item(start_date, end_date)
    top5 = q.get_top_consumable_items(start_date, end_date, n=5)
    total_consumables = q.get_total_consumables(start_date, end_date)
    consumable_txn = q.get_consumable_transaction_count(start_date, end_date)

    c1, c2 = st.columns(2)
    with c1:
        kpi_card("Total Consumable Expenditure", format_inr(total_consumables), format_lakh(total_consumables))
    with c2:
        kpi_card("Consumable Transactions", f"{consumable_txn:,}")

    st.write("")
    section_header("Monthly Consumable Expenditure")
    if not monthly_consumables.empty:
        monthly_consumables["month_label"] = monthly_consumables["month"].apply(month_label)
        fig = go.Figure(go.Scatter(
            x=monthly_consumables["month_label"], y=monthly_consumables["monthly_consumables"],
            mode="lines+markers", line=dict(color="#A78BFA", width=3), marker=dict(size=9),
            hovertemplate="%{x}<br>Expenditure: ₹%{y:,.2f}<extra></extra>",
        ))
        st.plotly_chart(style_fig(fig, height=340), use_container_width=True)
    else:
        st.info("No consumable data available for the selected date range.")

    col_a, col_b = st.columns([3, 2])
    with col_a:
        section_header("Consumable Expenditure by Item")
        if not consumable_by_item.empty:
            fig2 = go.Figure(go.Bar(
                y=consumable_by_item["item_name"], x=consumable_by_item["total_expenditure"],
                orientation="h", marker_color="#A78BFA",
                hovertemplate="%{y}<br>Expenditure: ₹%{x:,.2f}<extra></extra>",
            ))
            fig2.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(style_fig(fig2, height=max(300, 35 * len(consumable_by_item))), use_container_width=True)

    with col_b:
        section_header("Top 5 Consumable Items")
        if not top5.empty:
            disp = top5.copy()
            disp["total_expenditure"] = disp["total_expenditure"].apply(format_inr)
            disp.columns = ["Item", "Expenditure"]
            st.dataframe(disp, use_container_width=True, hide_index=True)

            # Pareto share, only when mathematically meaningful (2+ items)
            if len(consumable_by_item) > 1:
                total = consumable_by_item["total_expenditure"].sum()
                cum_share = (consumable_by_item["total_expenditure"].cumsum() / total * 100).round(1)
                st.caption(
                    f"The top {min(3, len(consumable_by_item))} item(s) account for "
                    f"{cum_share.iloc[min(2, len(cum_share)-1)]}% of total consumable expenditure."
                )


# ============================================================================
# PAGE: BUSINESS INSIGHTS & RECOMMENDATIONS
# ============================================================================
elif page == "Business Insights & Recommendations":
    section_header("Sales vs Purchases", "A comparison of transaction values only — not a profit, margin or cash-flow calculation.")
    svp = q.get_sales_vs_purchases(start_date, end_date)
    if not svp.empty:
        svp["month_label"] = svp["month"].apply(month_label)
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Sales Value", x=svp["month_label"], y=svp["sales_value"], marker_color=ACCENT))
        fig.add_trace(go.Bar(name="Purchase Value", x=svp["month_label"], y=svp["purchase_value"], marker_color="#38BDF8"))
        fig.update_layout(barmode="group", title="Monthly Sales Value vs Purchase Value")
        st.plotly_chart(style_fig(fig, height=380), use_container_width=True)

        disp = svp[["month_label", "sales_value", "purchase_value"]].copy()
        disp["sales_value"] = disp["sales_value"].apply(format_inr)
        disp["purchase_value"] = disp["purchase_value"].apply(format_inr)
        disp.columns = ["Month", "Sales Value", "Purchase Value"]
        st.dataframe(disp, use_container_width=True, hide_index=True)
    else:
        st.info("Insufficient overlapping monthly data to compare sales and purchase values.")

    st.write("")
    section_header("Business Insights")
    recs = ins.recommendations(start_date, end_date)
    for r in recs:
        insight_block("Finding", r["finding"])
        st.markdown(f"<div class='muted'>Implication: {r['implication']}</div>", unsafe_allow_html=True)
        st.markdown(f"**Recommended action:** {r['action']}")
        st.write("")

    st.write("")
    section_header("Key Conclusions")
    for c in ins.key_conclusions(start_date, end_date):
        st.markdown(f"- {c}")

    st.write("")
    section_header(
        "Verified Revenue Generation & Business Implementation",
        "Framework for documenting real-world implementation, per the assignment's 20-mark component."
    )
    st.markdown("""
    <div class="section-card">
    This section distinguishes <b>proposed</b> implementation from <b>verified</b> implementation and revenue,
    in line with academic integrity requirements. No revenue figures are populated here unless supported by
    genuine evidence from the business.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Implementation Log (fill in as recommendations are actually implemented)"):
        log_cols = ["Recommendation Implemented", "Date", "Business Action Taken",
                    "Measurable Result", "Revenue Generated", "Proof/Documentation", "Client Confirmation"]
        empty_log = pd.DataFrame(columns=log_cols)
        st.dataframe(empty_log, use_container_width=True, hide_index=True)
        st.caption(
            "Status: **No verified implementation or revenue recorded yet.** "
            "Populate this table only once genuine proof (invoice, business confirmation, etc.) exists."
        )

    st.write("")
    col_l, col_f = st.columns(2)
    with col_l:
        section_header("Limitations")
        st.markdown("""
        <div class="section-card">
        <ul>
        <li>Analysis covers six months of transaction data (Jan–Jun 2026) as supplied by the business.</li>
        <li>Limited to records provided; no complete production, inventory, or product-level sales datasets are available.</li>
        <li>Profitability, margin, and ROI cannot be directly calculated from sales and purchase values alone.</li>
        <li>Findings represent the available transaction period and the source data's structure.</li>
        </ul>
        This provides a structured foundation for deeper analytics once additional operational data becomes available.
        </div>
        """, unsafe_allow_html=True)
    with col_f:
        section_header("Future Scope")
        st.markdown("""
        <div class="section-card">
        <ul>
        <li>Inventory and production data integration</li>
        <li>Product-level sales analysis</li>
        <li>Supplier performance analysis</li>
        <li>Cost and profitability analysis (once cost data is available)</li>
        <li>Demand forecasting and anomaly detection</li>
        <li>Automated monthly management reporting</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# PAGES: CRUD MANAGEMENT
# ============================================================================
elif page in ["Sales Management", "Purchase Management", "Consumables Management", "Sales Adjustments Management"]:
    category = {
        "Sales Management": "Sales",
        "Purchase Management": "Purchases",
        "Consumables Management": "Consumables",
        "Sales Adjustments Management": "Sales Adjustments",
    }[page]
    cfg = crud.TABLES[category]
    section_header(category + " Management", "Create, view, update, and delete database records.")
    records = crud.get_records(category)
    if not records.empty:
        st.dataframe(records, use_container_width=True, hide_index=True)
    else:
        st.info("No records currently found in this table.")

    tab_add, tab_edit, tab_delete = st.tabs(["Add Record", "Edit Record", "Delete Record"])

    def render_fields(prefix, existing=None):
        values = {}
        for field, label, kind in cfg["fields"]:
            old = existing.get(field) if existing is not None else None
            if kind == "date":
                default = pd.to_datetime(old).date() if old is not None and not pd.isna(old) else pd.Timestamp.today().date()
                values[field] = st.date_input(label, value=default, key=f"{prefix}_{field}")
            elif kind == "number":
                try:
                    default = float(old) if old is not None and not pd.isna(old) else 0.0
                except (ValueError, TypeError):
                    default = 0.0
                values[field] = st.number_input(label, value=default, min_value=0.0, key=f"{prefix}_{field}")
            else:
                default = "" if old is None or pd.isna(old) else str(old)
                values[field] = st.text_input(label, value=default, key=f"{prefix}_{field}")
        return values

    with tab_add:
        with st.form(f"add_{category}"):
            add_values = render_fields(f"add_{category}")
            submitted = st.form_submit_button("Add Record", type="primary")
            if submitted:
                success, message = crud.add_record(category, add_values)
                if success:
                    st.success(message)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(message)

    with tab_edit:
        if records.empty:
            st.info("There are no records available to edit.")
        else:
            pk = cfg["pk"]
            choices = records[pk].tolist()
            selected_id = st.selectbox("Select record ID to edit", choices, key=f"edit_select_{category}")
            selected = records.loc[records[pk] == selected_id].iloc[0].to_dict()
            with st.form(f"edit_{category}"):
                edit_values = render_fields(f"edit_{category}", selected)
                submitted = st.form_submit_button("Save Changes", type="primary")
                if submitted:
                    success, message = crud.update_record(category, selected_id, edit_values)
                    if success:
                        st.success(message)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(message)

    with tab_delete:
        if records.empty:
            st.info("There are no records available to delete.")
        else:
            pk = cfg["pk"]
            selected_id = st.selectbox("Select record ID to delete", records[pk].tolist(), key=f"delete_select_{category}")
            selected = records.loc[records[pk] == selected_id].iloc[0]
            st.warning("Selected record:")
            st.dataframe(selected.to_frame().T, use_container_width=True, hide_index=True)
            confirm = st.checkbox("I confirm that I want to permanently delete this record.", key=f"confirm_delete_{category}")
            if st.button("Delete Record", type="primary", disabled=not confirm, key=f"delete_btn_{category}"):
                success, message = crud.delete_record(category, selected_id)
                if success:
                    st.success(message)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(message)


# ----------------------------------------------------------------------------
# Footer
# ----------------------------------------------------------------------------
st.markdown("""
<div class="footer-note">
MKT322 — Advanced Business Analytics · Academic Task 1 · Ashoka Industries, Hoshiarpur, Punjab<br>
Dashboard built with Streamlit, Plotly and a live MySQL connection. All figures are calculated directly from the database.
</div>
""", unsafe_allow_html=True)
