import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import json
import os
import anthropic
from datetime import date

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="INVNTRY",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #050508;
    color: #e2e8f0;
}

.stApp { background: #050508; }

.wordmark {
    font-size: 1.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 0.06em;
    margin-bottom: 0.25rem;
}

.stat-card {
    background: #0f0f14;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    position: relative;
    overflow: hidden;
}

.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 10px 10px 0 0;
}

.stat-card-1::before { background: linear-gradient(90deg, #818cf8, transparent); }
.stat-card-2::before { background: linear-gradient(90deg, #34d399, transparent); }
.stat-card-3::before { background: linear-gradient(90deg, #fbbf24, transparent); }
.stat-card-4::before { background: linear-gradient(90deg, #f87171, transparent); }

.stat-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 0.4rem;
}

.stat-num { font-size: 2rem; font-weight: 800; line-height: 1; margin-bottom: 0.2rem; }
.stat-sub { font-size: 0.7rem; color: #475569; }

.inv-table { width: 100%; border-collapse: collapse; }
.inv-table th {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #334155;
    padding: 0.75rem 0.75rem;
    text-align: left;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.inv-table td {
    padding: 0.85rem 0.75rem;
    font-size: 0.875rem;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    vertical-align: middle;
}
.inv-table tr:hover { background: rgba(255,255,255,0.02); }

.item-name { font-weight: 600; color: #f1f5f9; }
.item-sku { font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: #475569; }

.cat-pill {
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 100px;
    font-size: 0.65rem;
    font-weight: 600;
}

.ai-msg-user {
    background: rgba(129,140,248,0.1);
    border: 1px solid rgba(129,140,248,0.2);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    margin-left: 2rem;
    color: #c7d2fe;
    font-size: 0.875rem;
}

.ai-msg-assistant {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    margin-right: 2rem;
    color: #94a3b8;
    font-size: 0.875rem;
    line-height: 1.6;
}

section[data-testid="stSidebar"] {
    background: #080810 !important;
    border-right: 1px solid rgba(255,255,255,0.05);
}

.stTextInput input, .stNumberInput input, .stSelectbox select {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #e2e8f0 !important;
    border-radius: 6px !important;
}

.stButton button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border-radius: 6px !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #64748b !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] { color: #818cf8 !important; }

hr { border-color: rgba(255,255,255,0.05) !important; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(129,140,248,0.2); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ─── Save / Load ─────────────────────────────────────────────────────────────
SAVE_FILE = "inventory_save.json"

INITIAL_ITEMS = [
    {"id": 1, "name": "Wireless Keyboard",      "sku": "TECH-001", "category": "Electronics", "qty": 45, "price": 79.99,  "supplier": "TechCorp",    "threshold": 10},
    {"id": 2, "name": "Ergonomic Chair",         "sku": "FURN-002", "category": "Furniture",   "qty": 8,  "price": 349.00, "supplier": "OfficeWorld", "threshold": 5},
    {"id": 3, "name": "USB-C Hub",               "sku": "TECH-003", "category": "Electronics", "qty": 3,  "price": 59.99,  "supplier": "TechCorp",    "threshold": 10},
    {"id": 4, "name": "Standing Desk",           "sku": "FURN-004", "category": "Furniture",   "qty": 12, "price": 599.00, "supplier": "OfficeWorld", "threshold": 3},
    {"id": 5, "name": "Laptop Stand",            "sku": "TECH-005", "category": "Electronics", "qty": 27, "price": 44.99,  "supplier": "GadgetHub",   "threshold": 8},
    {"id": 6, "name": "Noise-Cancel Headphones", "sku": "TECH-006", "category": "Electronics", "qty": 0,  "price": 199.99, "supplier": "SoundCo",     "threshold": 5},
    {"id": 7, "name": "Monitor Arm",             "sku": "TECH-007", "category": "Electronics", "qty": 19, "price": 89.00,  "supplier": "GadgetHub",   "threshold": 6},
    {"id": 8, "name": "Storage Cabinet",         "sku": "FURN-008", "category": "Furniture",   "qty": 4,  "price": 229.00, "supplier": "OfficeWorld", "threshold": 3},
]

def load_inventory():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return [dict(i) for i in INITIAL_ITEMS]

def save_inventory(items):
    with open(SAVE_FILE, "w") as f:
        json.dump(items, f)

CATEGORY_COLORS = {
    "Electronics": "#818cf8",
    "Furniture":   "#fb923c",
    "Supplies":    "#34d399",
    "Clothing":    "#f472b6",
    "Other":       "#94a3b8",
}

PLOT_BG   = "#080810"
PLOT_GRID = "rgba(255,255,255,0.04)"

def get_status(item):
    if item["qty"] == 0:
        return "out", "#f87171", "OUT OF STOCK"
    if item["qty"] <= item["threshold"]:
        return "low", "#fbbf24", f"LOW (min {item['threshold']})"
    return "ok", "#4ade80", "In Stock"

# ─── Session State ────────────────────────────────────────────────────────────
if "inventory" not in st.session_state:
    st.session_state.inventory = load_inventory()
if "next_id" not in st.session_state:
    all_ids = [i["id"] for i in st.session_state.inventory]
    st.session_state.next_id = max(all_ids) + 1 if all_ids else 1
if "show_add" not in st.session_state:
    st.session_state.show_add = False
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None
if "delete_id" not in st.session_state:
    st.session_state.delete_id = None
if "ai_messages" not in st.session_state:
    st.session_state.ai_messages = []

items = st.session_state.inventory

# ─── Stats ────────────────────────────────────────────────────────────────────
total_skus   = len(items)
total_value  = sum(i["qty"] * i["price"] for i in items)
low_stock    = sum(1 for i in items if 0 < i["qty"] <= i["threshold"])
out_of_stock = sum(1 for i in items if i["qty"] == 0)

# ─── Header ───────────────────────────────────────────────────────────────────
col_logo, col_date, col_save, col_add = st.columns([3, 2, 1, 1])
with col_logo:
    st.markdown('<div class="wordmark">WELCOME TO SWAG INVNTRY</div>', unsafe_allow_html=True)
with col_date:
    st.markdown(f'<p style="color:#334155;font-family:\'IBM Plex Mono\',monospace;font-size:0.7rem;margin-top:0.9rem">{date.today().strftime("%b %d, %Y")}</p>', unsafe_allow_html=True)
with col_save:
    if st.button("💾 Save", use_container_width=True):
        save_inventory(items)
        st.toast("Inventory saved!", icon="✅")
with col_add:
    if st.button("＋ Add Item", type="primary", use_container_width=True):
        st.session_state.show_add = True
        st.session_state.edit_id = None

st.markdown('<hr style="margin:0.5rem 0 1rem"/>', unsafe_allow_html=True)

# ─── Stat Cards ───────────────────────────────────────────────────────────────
s1, s2, s3, s4 = st.columns(4)
with s1:
    st.markdown(f"""
    <div class="stat-card stat-card-1">
        <div class="stat-label">Total SKUs</div>
        <div class="stat-num" style="color:#818cf8">{total_skus}</div>
        <div class="stat-sub">items tracked</div>
    </div>""", unsafe_allow_html=True)
with s2:
    st.markdown(f"""
    <div class="stat-card stat-card-2">
        <div class="stat-label">Inventory Value</div>
        <div class="stat-num" style="color:#34d399">${total_value:,.2f}</div>
        <div class="stat-sub">at current prices</div>
    </div>""", unsafe_allow_html=True)
with s3:
    st.markdown(f"""
    <div class="stat-card stat-card-3">
        <div class="stat-label">Low Stock</div>
        <div class="stat-num" style="color:#fbbf24">{low_stock}</div>
        <div class="stat-sub">below threshold</div>
    </div>""", unsafe_allow_html=True)
with s4:
    st.markdown(f"""
    <div class="stat-card stat-card-4">
        <div class="stat-label">Out of Stock</div>
        <div class="stat-num" style="color:#f87171">{out_of_stock}</div>
        <div class="stat-sub">need reorder</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_inv, tab_analytics, tab_ai = st.tabs(["INVENTORY", "ANALYTICS", "AI ASSISTANT"])

# ════════════════════════════════════════════════════════════════════════════
# INVENTORY TAB
# ════════════════════════════════════════════════════════════════════════════
with tab_inv:
    with st.container():
        f1, f2, f3 = st.columns([2, 1.5, 1.5])
        with f1:
            search = st.text_input("🔍 Search", placeholder="Name, SKU, supplier…", label_visibility="collapsed")
        with f2:
            categories = sorted(set(i["category"] for i in items))
            cat_filter = st.selectbox("Category", ["All"] + categories, label_visibility="collapsed")
        with f3:
            stock_filter = st.selectbox("Stock", ["All", "In Stock", "Low Stock", "Out of Stock"], label_visibility="collapsed")

        filtered = []
        for item in items:
            q = search.lower()
            match_search = not q or q in item["name"].lower() or q in item["sku"].lower() or q in item["supplier"].lower()
            match_cat = cat_filter == "All" or item["category"] == cat_filter
            status_key, _, _ = get_status(item)
            match_stock = (
                stock_filter == "All" or
                (stock_filter == "In Stock"     and status_key == "ok")  or
                (stock_filter == "Low Stock"    and status_key == "low") or
                (stock_filter == "Out of Stock" and status_key == "out")
            )
            if match_search and match_cat and match_stock:
                filtered.append(item)

        st.markdown(f'<p style="font-family:\'IBM Plex Mono\',monospace;font-size:0.65rem;color:#334155;margin:0.25rem 0 0.75rem">{len(filtered)} items</p>', unsafe_allow_html=True)

        if not filtered:
            st.markdown('<p style="text-align:center;color:#334155;padding:2rem">No items match your filters.</p>', unsafe_allow_html=True)
        else:
            table_data = []
            for item in filtered:
                status_key, color, status_label = get_status(item)
                table_data.append({
                    "Item": item["name"],
                    "SKU": item["sku"],
                    "Category": item["category"],
                    "Qty": item["qty"],
                    "Status": status_label,
                    "Price": f"${item['price']:.2f}",
                    "Supplier": item["supplier"],
                })
            df_table = pd.DataFrame(table_data)
            st.dataframe(df_table, use_container_width=True, hide_index=True)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown('<p style="font-family:\'IBM Plex Mono\',monospace;font-size:0.6rem;letter-spacing:0.15em;text-transform:uppercase;color:#334155">Quick Actions</p>', unsafe_allow_html=True)

        for item in filtered:
            _, col_name, col_minus, col_qty, col_plus, col_edit, col_del = st.columns([0.1, 2.5, 0.4, 0.5, 0.4, 0.4, 0.4])
            status_key, color, _ = get_status(item)
            with col_name:
                st.markdown(f'<span style="font-size:0.825rem;color:#94a3b8">{item["name"]}</span>', unsafe_allow_html=True)
            with col_minus:
                if st.button("−", key=f"minus_{item['id']}"):
                    item["qty"] = max(0, item["qty"] - 1)
                    save_inventory(items)
                    st.rerun()
            with col_qty:
                st.markdown(f'<span style="font-family:\'IBM Plex Mono\',monospace;color:{color};font-size:0.9rem">{item["qty"]}</span>', unsafe_allow_html=True)
            with col_plus:
                if st.button("＋", key=f"plus_{item['id']}"):
                    item["qty"] += 1
                    save_inventory(items)
                    st.rerun()
            with col_edit:
                if st.button("✎", key=f"edit_{item['id']}"):
                    st.session_state.edit_id = item["id"]
                    st.session_state.show_add = False
                    st.rerun()
            with col_del:
                if st.button("✕", key=f"del_{item['id']}"):
                    st.session_state.delete_id = item["id"]
                    st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# ANALYTICS TAB
# ════════════════════════════════════════════════════════════════════════════
with tab_analytics:
    df = pd.DataFrame(items)
    df["value"] = df["qty"] * df["price"]
    df["status"] = df.apply(lambda r: "Out of Stock" if r["qty"] == 0 else ("Low Stock" if r["qty"] <= r["threshold"] else "In Stock"), axis=1)
    df["bar_color"] = df.apply(lambda r: "#f87171" if r["qty"] == 0 else ("#fbbf24" if r["qty"] <= r["threshold"] else "#818cf8"), axis=1)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<p style="font-family:\'IBM Plex Mono\',monospace;font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:#475569">Quantity by Item</p>', unsafe_allow_html=True)
        df_sorted = df.sort_values("qty", ascending=False).head(8)
        fig1 = go.Figure(go.Bar(
            x=df_sorted["name"], y=df_sorted["qty"],
            marker_color=df_sorted["bar_color"].tolist(),
            marker_line_width=0
        ))
        fig1.update_layout(
            plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
            font=dict(color="#475569", family="IBM Plex Mono", size=10),
            xaxis=dict(gridcolor=PLOT_GRID, tickangle=-30),
            yaxis=dict(gridcolor=PLOT_GRID),
            margin=dict(l=0, r=0, t=10, b=0), height=240
        )
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.markdown('<p style="font-family:\'IBM Plex Mono\',monospace;font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:#475569">Value by Category</p>', unsafe_allow_html=True)
        cat_df = df.groupby("category")["value"].sum().reset_index()
        cat_df["color"] = cat_df["category"].map(lambda c: CATEGORY_COLORS.get(c, "#94a3b8"))
        fig2 = go.Figure(go.Bar(
            x=cat_df["category"], y=cat_df["value"],
            marker_color=cat_df["color"].tolist(),
            marker_line_width=0
        ))
        fig2.update_layout(
            plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
            font=dict(color="#475569", family="IBM Plex Mono", size=10),
            xaxis=dict(gridcolor=PLOT_GRID),
            yaxis=dict(gridcolor=PLOT_GRID, tickprefix="$"),
            margin=dict(l=0, r=0, t=10, b=0), height=240
        )
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        st.markdown('<p style="font-family:\'IBM Plex Mono\',monospace;font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:#475569">Category Distribution</p>', unsafe_allow_html=True)
        cat_count = df.groupby("category").size().reset_index(name="count")
        cat_count["color"] = cat_count["category"].map(lambda c: CATEGORY_COLORS.get(c, "#94a3b8"))
        fig3 = go.Figure(go.Pie(
            labels=cat_count["category"], values=cat_count["count"],
            hole=0.5, marker_colors=cat_count["color"].tolist(),
            textinfo="none"
        ))
        fig3.update_layout(
            plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
            font=dict(color="#94a3b8", family="IBM Plex Mono", size=10),
            legend=dict(font=dict(color="#64748b", size=10)),
            margin=dict(l=0, r=0, t=10, b=0), height=240
        )
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        st.markdown('<p style="font-family:\'IBM Plex Mono\',monospace;font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:#475569">Stock Status Overview</p>', unsafe_allow_html=True)
        total = len(items)
        in_stock_n = sum(1 for i in items if i["qty"] > i["threshold"])
        for label, count, color in [("In Stock", in_stock_n, "#4ade80"), ("Low Stock", low_stock, "#fbbf24"), ("Out of Stock", out_of_stock, "#f87171")]:
            pct = (count / total * 100) if total > 0 else 0
            st.markdown(f"""
            <div style="margin-bottom:0.75rem">
              <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem">
                <span style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:#64748b">{label}</span>
                <span style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;color:{color}">{count}</span>
              </div>
              <div style="height:5px;background:rgba(255,255,255,0.04);border-radius:3px;overflow:hidden">
                <div style="height:100%;width:{pct:.1f}%;background:{color};border-radius:3px"></div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<p style="font-family:\'IBM Plex Mono\',monospace;font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:#475569;margin-top:1rem">Top Value Items</p>', unsafe_allow_html=True)
        top4 = sorted(items, key=lambda i: i["qty"] * i["price"], reverse=True)[:4]
        for item in top4:
            val = item["qty"] * item["price"]
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;margin-bottom:0.4rem">
              <span style="font-size:0.8rem;color:#94a3b8">{item['name']}</span>
              <span style="font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#34d399">${val:,.0f}</span>
            </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# AI ASSISTANT TAB
# ════════════════════════════════════════════════════════════════════════════
with tab_ai:
    st.markdown('<p style="font-family:\'IBM Plex Mono\',monospace;font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:#475569;margin-bottom:1rem">AI Inventory Assistant</p>', unsafe_allow_html=True)

    # Show chat history
    for msg in st.session_state.ai_messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="ai-msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="ai-msg-assistant">{msg["content"]}</div>', unsafe_allow_html=True)

    # Input
    user_input = st.chat_input("Ask about your inventory…")

    if user_input:
        # Build inventory context for the AI
        inventory_summary = json.dumps(items, indent=2)
        system_prompt = f"""You are a helpful inventory management assistant for INVNTRY. 
You have access to the current inventory data below. Answer questions about stock levels, 
values, suppliers, reorder suggestions, and any other inventory-related questions. 
Be concise and helpful.

Current Inventory:
{inventory_summary}

Stats:
- Total SKUs: {total_skus}
- Total Value: ${total_value:,.2f}
- Low Stock Items: {low_stock}
- Out of Stock Items: {out_of_stock}
"""

        st.session_state.ai_messages.append({"role": "user", "content": user_input})

        with st.spinner("Thinking…"):
            try:
                client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                response = client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=1024,
                    system=system_prompt,
                    messages=st.session_state.ai_messages
                )
                reply = response.content[0].text
            except Exception as e:
                reply = f"Error contacting AI: {str(e)}. Make sure your ANTHROPIC_API_KEY is set in Streamlit secrets."

        st.session_state.ai_messages.append({"role": "assistant", "content": reply})
        st.rerun()

    if st.session_state.ai_messages:
        if st.button("🗑 Clear Chat"):
            st.session_state.ai_messages = []
            st.rerun()

# ─── Add / Edit Modal ────────────────────────────────────────────────────────
show_form = st.session_state.show_add or st.session_state.edit_id is not None
editing = next((i for i in items if i["id"] == st.session_state.edit_id), None) if st.session_state.edit_id else None

if show_form:
    st.markdown("<hr/>", unsafe_allow_html=True)
    title = "Edit Item" if editing else "Add New Item"
    st.markdown(f'<p style="font-family:\'IBM Plex Mono\',monospace;font-size:0.75rem;letter-spacing:0.12em;text-transform:uppercase;color:#818cf8">{title}</p>', unsafe_allow_html=True)

    defaults = editing or {"name": "", "sku": "", "category": "", "qty": 0, "price": 0.0, "supplier": "", "threshold": 10}

    fc1, fc2 = st.columns(2)
    with fc1:
        f_name      = st.text_input("Item Name",             value=defaults["name"])
        f_sku       = st.text_input("SKU",                   value=defaults["sku"])
        f_category  = st.text_input("Category",              value=defaults["category"])
        f_threshold = st.number_input("Low Stock Threshold", value=int(defaults["threshold"]), min_value=0)
    with fc2:
        f_qty      = st.number_input("Quantity",  value=int(defaults["qty"]),     min_value=0)
        f_price    = st.number_input("Price ($)", value=float(defaults["price"]), min_value=0.0, step=0.01, format="%.2f")
        f_supplier = st.text_input("Supplier",               value=defaults["supplier"])

    btn1, btn2, _ = st.columns([1, 1, 4])
    with btn1:
        if st.button("Save Item", type="primary"):
            if not f_name or not f_sku:
                st.error("Name and SKU are required.")
            else:
                new_item = {"name": f_name, "sku": f_sku, "category": f_category,
                            "qty": f_qty, "price": f_price, "supplier": f_supplier, "threshold": f_threshold}
                if editing:
                    for i, item in enumerate(items):
                        if item["id"] == editing["id"]:
                            items[i] = {**new_item, "id": editing["id"]}
                    st.success("✓ Item updated")
                else:
                    new_item["id"] = st.session_state.next_id
                    st.session_state.next_id += 1
                    items.append(new_item)
                    st.success("✓ Item added")
                save_inventory(items)
                st.session_state.show_add = False
                st.session_state.edit_id = None
                st.rerun()
    with btn2:
        if st.button("Cancel"):
            st.session_state.show_add = False
            st.session_state.edit_id = None
            st.rerun()

# ─── Delete Confirm ───────────────────────────────────────────────────────────
if st.session_state.delete_id is not None:
    del_item = next((i for i in items if i["id"] == st.session_state.delete_id), None)
    if del_item:
        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown(f'<p style="font-family:\'IBM Plex Mono\',monospace;font-size:0.75rem;letter-spacing:0.12em;color:#f87171">⚠ CONFIRM DELETE: {del_item["name"]}</p>', unsafe_allow_html=True)
        st.caption("This action cannot be undone.")
        db1, db2, _ = st.columns([1, 1, 4])
        with db1:
            if st.button("🗑 Delete", type="primary"):
                st.session_state.inventory = [i for i in items if i["id"] != del_item["id"]]
                save_inventory(st.session_state.inventory)
                st.session_state.delete_id = None
                st.rerun()
        with db2:
            if st.button("Cancel", key="cancel_del"):
                st.session_state.delete_id = None
                st.rerun()
