"""
Streamlit web UI for the Binance Futures Testnet Trading Bot.
Styled with a Binance-inspired dark + yellow theme.
Reuses the same validation and order placement pipeline as the CLI.
"""

import streamlit as st
from pydantic import ValidationError

from bot.orders import OrderExecutionError, place_order
from bot.validators import OrderRequest

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Futures Trading Bot | Testnet",
    page_icon="📈",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Binance-style dark + yellow theme (custom CSS)
# ---------------------------------------------------------------------------
BINANCE_YELLOW = "#F0B90B"
BINANCE_BG = "#0B0E11"
BINANCE_CARD = "#181A20"
BINANCE_GREEN = "#0ECB81"
BINANCE_RED = "#F6465D"
BINANCE_TEXT_MUTED = "#848E9C"

st.markdown(
    f"""
    <style>
        /* ---------- Base app ---------- */
        html, body {{
            background-color: {BINANCE_BG} !important;
        }}

        .stApp {{
            background-color: {BINANCE_BG};
            color: #EAECEF;
        }}

        /* Top toolbar (hamburger menu / deploy bar) — separate layer, defaults to white */
        header[data-testid="stHeader"] {{
            background-color: {BINANCE_BG} !important;
        }}

        header[data-testid="stHeader"] * {{
            color: #EAECEF !important;
        }}

        div[data-testid="stToolbar"] {{
            background-color: {BINANCE_BG} !important;
        }}

        div[data-testid="stDecoration"] {{
            background-image: none !important;
            background-color: {BINANCE_BG} !important;
        }}

        section[data-testid="stSidebar"] {{
            background-color: {BINANCE_CARD};
            border-right: 1px solid #2B3139;
        }}

        section[data-testid="stSidebar"] * {{
            color: #EAECEF;
        }}

        h1, h2, h3 {{
            color: {BINANCE_YELLOW} !important;
            font-weight: 700 !important;
        }}

        p, label, span, .stMarkdown {{
            color: #EAECEF;
        }}

        /* ---------- Buttons ---------- */
        .stButton > button {{
            background-color: {BINANCE_YELLOW};
            color: #0B0E11;
            font-weight: 700;
            border: none;
            border-radius: 6px;
            padding: 0.6rem 1rem;
            width: 100%;
            cursor: pointer;
            transition: background-color 0.15s ease;
        }}

        .stButton > button:hover {{
            background-color: #d9a509;
            color: #0B0E11;
            cursor: pointer;
        }}

        .stButton > button:active,
        .stButton > button:focus {{
            background-color: #d9a509 !important;
            color: #0B0E11 !important;
            box-shadow: none !important;
        }}

        /* ---------- Text / number inputs ---------- */
        div[data-baseweb="input"],
        div[data-baseweb="input"] > div {{
            background-color: #0B0E11 !important;
            border: 1px solid #2B3139 !important;
            border-radius: 6px !important;
        }}

        input {{
            background-color: transparent !important;
            color: #EAECEF !important;
            cursor: text;
        }}

        /* Number input +/- stepper buttons */
        button[data-testid="stNumberInputStepUp"],
        button[data-testid="stNumberInputStepDown"] {{
            background-color: #0B0E11 !important;
            border: 1px solid #2B3139 !important;
            color: {BINANCE_YELLOW} !important;
            cursor: pointer;
        }}

        button[data-testid="stNumberInputStepUp"]:hover,
        button[data-testid="stNumberInputStepDown"]:hover {{
            background-color: #2B3139 !important;
        }}

        /* ---------- Selectbox (closed state) ---------- */
        div[data-baseweb="select"] > div {{
            background-color: #0B0E11 !important;
            border: 1px solid #2B3139 !important;
            border-radius: 6px !important;
            color: #EAECEF !important;
            cursor: pointer;
        }}

        div[data-baseweb="select"] * {{
            color: #EAECEF !important;
            cursor: pointer;
        }}

        div[data-baseweb="select"]:hover > div {{
            border-color: {BINANCE_YELLOW} !important;
        }}

        /* ---------- Selectbox dropdown (open popover, rendered outside sidebar) ---------- */
        div[data-baseweb="popover"] ul {{
            background-color: {BINANCE_CARD} !important;
            border: 1px solid #2B3139 !important;
        }}

        div[data-baseweb="popover"] li {{
            background-color: {BINANCE_CARD} !important;
            color: #EAECEF !important;
            cursor: pointer;
        }}

        div[data-baseweb="popover"] li:hover {{
            background-color: #2B3139 !important;
            color: {BINANCE_YELLOW} !important;
        }}

        /* ---------- Alerts ---------- */
        .stAlert {{
            border-radius: 6px;
        }}

        /* ---------- Metrics ---------- */
        [data-testid="stMetricValue"] {{
            color: {BINANCE_YELLOW};
        }}

        [data-testid="stMetricLabel"] {{
            color: {BINANCE_TEXT_MUTED};
        }}

        [data-testid="stMetric"] {{
            background-color: {BINANCE_CARD};
            border: 1px solid #2B3139;
            border-radius: 8px;
            padding: 0.75rem;
        }}

        /* ---------- Order preview card ---------- */
        .order-card {{
            background-color: {BINANCE_CARD};
            border: 1px solid #2B3139;
            border-radius: 10px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
            color: #EAECEF;
        }}

        .badge-buy {{
            background-color: rgba(14, 203, 129, 0.15);
            color: {BINANCE_GREEN};
            padding: 2px 10px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 0.85rem;
        }}

        .badge-sell {{
            background-color: rgba(246, 70, 93, 0.15);
            color: {BINANCE_RED};
            padding: 2px 10px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 0.85rem;
        }}

        /* ---------- Expander ---------- */
        details {{
            background-color: {BINANCE_CARD} !important;
            border: 1px solid #2B3139 !important;
            border-radius: 8px !important;
        }}

        summary {{
            color: #EAECEF !important;
            cursor: pointer;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("📈 Futures Trading Bot")
st.caption("Binance Futures Testnet (USDT-M) · Simulated order execution")

# ---------------------------------------------------------------------------
# Sidebar — order configuration
# ---------------------------------------------------------------------------
st.sidebar.markdown("### 🔧 Order Configuration")

symbol = st.sidebar.text_input("Symbol", value="BTCUSDT").upper().strip()

side = st.sidebar.selectbox("Side", options=["BUY", "SELL"])

order_type = st.sidebar.selectbox(
    "Order Type", options=["MARKET", "LIMIT", "STOP_LIMIT"]
)

quantity = st.sidebar.number_input(
    "Quantity", min_value=0.0, value=0.01, step=0.001, format="%.4f"
)

price = None
if order_type in ("LIMIT", "STOP_LIMIT"):
    price = st.sidebar.number_input(
        "Price", min_value=0.0, value=65000.0, step=0.5
    )

stop_price = None
if order_type == "STOP_LIMIT":
    stop_price = st.sidebar.number_input(
        "Stop Price (trigger)", min_value=0.0, value=64500.0, step=0.5
    )

submit = st.sidebar.button("Place Order", type="primary")

# ---------------------------------------------------------------------------
# Order preview card
# ---------------------------------------------------------------------------
side_badge = (
    f'<span class="badge-buy">BUY</span>'
    if side == "BUY"
    else f'<span class="badge-sell">SELL</span>'
)

preview_rows = f"""
    <b>{symbol}</b> &nbsp;·&nbsp; {side_badge} &nbsp;·&nbsp; {order_type} &nbsp;·&nbsp; Qty: {quantity}
"""
if price is not None:
    preview_rows += f" &nbsp;·&nbsp; Price: {price}"
if stop_price is not None:
    preview_rows += f" &nbsp;·&nbsp; Stop: {stop_price}"

st.markdown(f'<div class="order-card">{preview_rows}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Order submission
# ---------------------------------------------------------------------------
if submit:
    payload = {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "price": price,
        "stop_price": stop_price,
    }

    with st.spinner("Validating and sending order to Binance Testnet..."):
        try:
            validated_order = OrderRequest(
                **{k: v for k, v in payload.items() if v is not None}
            )
            response = place_order(validated_order)

            st.success("Order placed successfully")

            # Handle both standard orders (orderId/status) and
            # algo/conditional orders (algoId/algoStatus)
            order_id = response.get("orderId", response.get("algoId"))
            status = response.get("status", response.get("algoStatus"))
            executed_qty = response.get("executedQty", "N/A")
            avg_price = response.get("avgPrice")

            cols = st.columns(4) if avg_price else st.columns(3)
            cols[0].metric("Order ID", order_id)
            cols[1].metric("Status", status)
            cols[2].metric("Executed Qty", executed_qty)
            if avg_price:
                cols[3].metric("Avg Price", avg_price)

            with st.expander("View raw API response"):
                st.json(response)

        except ValidationError as validation_error:
            st.error("Input validation failed")
            for error in validation_error.errors():
                st.warning(error["msg"])

        except OrderExecutionError as exchange_error:
            st.error("Order execution failed")
            st.info(str(exchange_error))

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(
    "⚠️ Connected to Binance Futures **Testnet** — no real funds are involved."
)