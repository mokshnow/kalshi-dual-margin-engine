import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.stats import norm
from datetime import datetime

# ==========================================
# User Inputs
# ==========================================
ASSET_CONFIG = {
    "BTC": {
        "spot_min": 50000.0, "spot_max": 130000.0, "spot_default": 60000.0, "step": 1000.0,
        "daily_vol_assumption": 0.03, "perp_haircut": 0.05,
        "brackets": [
            ("< $49,999.99", 0.001, 50000.0), ("$50,000 to $59,999.99", 50000.0, 60000.0),
            ("$60,000 to $69,999.99", 60000.0, 70000.0), ("$70,000 to $79,999.99", 70000.0, 80000.0),
            ("$80,000 to $89,999.99", 80000.0, 90000.0), ("$90,000 to $99,999.99", 90000.0, 100000.0),
            ("> $100,000", 100000.0, float('inf'))
        ]
    },
    "ETH": {
        "spot_min": 1000.0, "spot_max": 8000.0, "spot_default": 1500.0, "step": 50.0,
        "daily_vol_assumption": 0.04, "perp_haircut": 0.06,
        "brackets": [
            ("999.99 or below", 0.001, 1000.0), ("1,000 to 1,249.99", 1000.0, 1250.0),
            ("1,250 to 1,499.99", 1250.0, 1500.0),("1,500 to 1,749.99", 1500.0, 1750.0),
            ("1,750 to 1,999.99", 1750.0, 2000.0), ("2,000 to 2,249.99", 2000.0, 2250.0),
            ("2,250 to 2,499.99", 2250.0, 2500.0), ("2,500 to 2,749.99", 2500.0, 2750.0),
            ("2,750 to 2,999.99", 2750.0, 3000.0), ("3,000 to 3,249.99", 3000.0, 3250.0),
            ("3,250 to 3,499.99", 3250.0, 3500.0), ("3,500 to 3,749.99", 3500.0, 3750.0),
            ("3,750 to 3,999.99", 3750.0, 4000.0), ("4,000 to 4,249.99", 4000.0, 4250.0),
            ("4,250 to 4,499.99", 4250.0, 4500.0), ("4,500 to 4,749.99", 4500.0, 4750.0),
            ("4,750 to 4,999.99", 4750.0, 5000.0), ("5,000 or above", 5000.0, float('inf'))
        ]
    },
    "SOL": {
        "spot_min": 30.0, "spot_max": 400.0, "spot_default": 75.0, "step": 5.0,
        "daily_vol_assumption": 0.05, "perp_haircut": 0.08,
        "brackets": [
            ("100 or above", 100.0, float('inf')), ("150 or above", 150.0, float('inf')),
            ("200 or above", 200.0, float('inf')), ("250 or above", 250.0, float('inf')),
            ("300 or above", 300.0, float('inf')), ("350 or above", 350.0, float('inf')),
            ("400 or above", 400.0, float('inf')), ("450 or above", 450.0, float('inf'))
        ]
    },
    "HYPE": {
        "spot_min": 10.0, "spot_max": 100.0, "spot_default": 65.0, "step": 1.0,
        "daily_vol_assumption": 0.08, "perp_haircut": 0.12
       
    },
    "ZEC": {
        "spot_min": 100.0, "spot_max": 1000.0, "spot_default": 385.0, "step": 5.0,
        "daily_vol_assumption": 0.06, "perp_haircut": 0.08
    
    }
}

# historical correlations
BASE_CORRELATION_MATRIX = {
    "BTC": {"BTC": 1.0, "ETH": 0.85, "SOL": 0.70, "HYPE": 0.40, "ZEC": 0.60},
    "ETH": {"BTC": 0.85, "ETH": 1.0, "SOL": 0.75, "HYPE": 0.45, "ZEC": 0.65},
    "SOL": {"BTC": 0.70, "ETH": 0.75, "SOL": 1.0, "HYPE": 0.50, "ZEC": 0.55},
    "HYPE": {"BTC": 0.40, "ETH": 0.45, "SOL": 0.50, "HYPE": 1.0, "ZEC": 0.30},
    "ZEC": {"BTC": 0.60, "ETH": 0.65, "SOL": 0.55, "HYPE": 0.30, "ZEC": 1.0}
}

# ==========================================
# Formulas
# ==========================================
class RiskMath:
    @staticmethod
    def calculate_binary_price(S, K, T, sigma, r=0.0325):
        if K == float('inf') or K <= 0: return 0.0
        T = max(T, 0.0001)
        d2 = (np.log(S / K) + (r - 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return np.exp(-r * T) * norm.cdf(d2)

    @staticmethod
    def calculate_range_price(S, K_lower, K_upper, T, sigma, r=0.0325):
        return max(0.0, RiskMath.calculate_binary_price(S, K_lower, T, sigma, r) - RiskMath.calculate_binary_price(S, K_upper, T, sigma, r))

    @staticmethod
    def calculate_binary_call_greeks(S, K, T, sigma, r=0.0325):
        if K == float('inf') or K <= 0: return 0.0, 0.0
        T = max(T, 0.0001)
        d2 = (np.log(S / K) + (r - 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        delta = (np.exp(-r * T) * norm.pdf(d2)) / (sigma * S * np.sqrt(T))
        gamma = -delta * ((d2 + sigma * np.sqrt(T)) / (sigma * S * np.sqrt(T)) + 1 / S)
        return delta, gamma

    @staticmethod
    def calculate_range_greeks(S, K_lower, K_upper, T, sigma, r=0.0325):
        d_lower, g_lower = RiskMath.calculate_binary_call_greeks(S, K_lower, T, sigma, r)
        d_upper, g_upper = RiskMath.calculate_binary_call_greeks(S, K_upper, T, sigma, r)
        return d_lower - d_upper, g_lower - g_upper

    @staticmethod
    def calculate_cross_asset_rho(S_perp, S_pred, K_lower, K_upper, T_current, sigma, vol_perp, vol_pred, base_corr, days_history=90):
        np.random.seed(42)
        
        # cholesky decomp
        Z1 = np.random.normal(0, 1, days_history)
        Z2 = base_corr * Z1 + np.sqrt(1 - base_corr**2) * np.random.normal(0, 1, days_history)
        
        r_perp = Z1 * vol_perp
        r_pred = Z2 * vol_pred
        
        spot_path_perp = [S_perp]
        spot_path_pred = [S_pred]
        
        for rp, rq in zip(reversed(r_perp), reversed(r_pred)):
            spot_path_perp.insert(0, spot_path_perp[0] / np.exp(rp))
            spot_path_pred.insert(0, spot_path_pred[0] / np.exp(rq))
            
        spot_path_perp = np.array(spot_path_perp)
        spot_path_pred = np.array(spot_path_pred)
        
        event_prices = []
        for i, S in enumerate(spot_path_pred):
            T_historical = T_current + ((days_history - i) / 365.0)
            p = RiskMath.calculate_range_price(S, K_lower, K_upper, T_historical, sigma)
            event_prices.append(p)
            
        event_prices = np.array(event_prices) + 1e-6
        
        spot_returns_perp = np.diff(np.log(spot_path_perp))
        event_returns = np.diff(np.log(event_prices))
        
        rho = np.corrcoef(spot_returns_perp, event_returns)[0, 1]
        return 0.0 if np.isnan(rho) else float(rho)

    @staticmethod
    def calc_isolated_var(exposure, vol, z_score):
        return abs(exposure * vol * z_score)

    @staticmethod
    def calc_unified_margin(var_perp, var_event, rho, is_offsetting, gamma, S_pred, contracts, shock_pct=0.05):
        surcharge = 0.5 * abs(gamma) * ((S_pred * shock_pct) ** 2) * abs(contracts)
        
        effective_rho = -abs(rho) if is_offsetting else abs(rho)
        unified_var_sq = (var_perp**2) + (var_event**2) + (2 * effective_rho * var_perp * var_event)
        base_unified = np.sqrt(max(0, unified_var_sq))
        
        total_unified = base_unified + surcharge
        isolated_total = var_perp + var_event + surcharge
        return isolated_total, total_unified, surcharge

# ==========================================
# Dashboard
# ==========================================
st.set_page_config(page_title="Kalshi Dual Margin Engine", layout="wide")
st.title("Kalshi Dual Margin Engine")
st.markdown("Margin Efficiency for Kalshi Perps and Predictions.")

perp_assets_list = ["BTC", "ETH", "SOL", "HYPE", "ZEC"]
pred_assets_list = ["BTC", "ETH", "SOL"]

colA, colB = st.sidebar.columns(2)
with colA:
    perp_asset = st.selectbox("Perp", perp_assets_list, index=0)
with colB:
    pred_asset = st.selectbox("Prediction", pred_assets_list, index=1)

perp_cfg = ASSET_CONFIG[perp_asset]
pred_cfg = ASSET_CONFIG[pred_asset]

st.sidebar.markdown("---")

# perp
st.sidebar.header(f"{perp_asset} Perpetual")
perp_spot = st.sidebar.slider(
    f"{perp_asset} Spot Price ($)", 
    min_value=perp_cfg["spot_min"], max_value=perp_cfg["spot_max"], 
    value=perp_cfg["spot_default"], step=perp_cfg["step"], key="perp_spot"
)
perp_dir = st.sidebar.radio("Position", ["LONG", "SHORT"], horizontal=True)
perp_cost = st.sidebar.number_input("Cost ($)", value=100000.0, step=1000.0)
perp_leverage = st.sidebar.slider("Leverage", min_value=1.0, max_value=6.0, value=3.0, step=0.1)

total_perp_size = perp_cost * perp_leverage
st.sidebar.caption(f"**Total Size ({perp_leverage}x):** ${total_perp_size:,.2f}")

st.sidebar.markdown("---")

# prediction
st.sidebar.header(f"{pred_asset} Price at the End of 2026")
pred_spot = st.sidebar.slider(
    f"{pred_asset} Spot Price ($)", 
    min_value=pred_cfg["spot_min"], max_value=pred_cfg["spot_max"], 
    value=pred_cfg["spot_default"], step=pred_cfg["step"], key="pred_spot"
)

bracket_labels = [b[0] for b in pred_cfg["brackets"]]
selected_bracket_label = st.sidebar.selectbox("Target Price", bracket_labels)
k_lower, k_upper = next((b[1], b[2]) for b in pred_cfg["brackets"] if b[0] == selected_bracket_label)

vol = st.sidebar.slider("Event IV", min_value=0.1, max_value=1.5, value=0.5, step=0.1)
event_dir = st.sidebar.radio("Shares", ["Yes (Long)", "No (Short)"], horizontal=True)
contracts = st.sidebar.number_input("Total Contracts", value=100000, step=1000)

# ==========================================
# Calculations
# ==========================================

expiration_date = datetime(2026, 12, 31, 23, 59, 59)
time_remaining = expiration_date - datetime.now()
T_years = max(time_remaining.total_seconds() / (365.0 * 24 * 3600), 0.0001)

z_score = 2.576     

base_corr = BASE_CORRELATION_MATRIX[perp_asset][pred_asset]

calculated_rho = RiskMath.calculate_cross_asset_rho(
    perp_spot, pred_spot, k_lower, k_upper, T_years, vol, 
    perp_cfg["daily_vol_assumption"], pred_cfg["daily_vol_assumption"], base_corr
)

st.sidebar.markdown("---")
st.sidebar.success(f"Correlation: {calculated_rho:.4f}")

raw_delta, gamma = RiskMath.calculate_range_greeks(pred_spot, k_lower, k_upper, T_years, vol)

active_delta = raw_delta if event_dir == "Yes (Long)" else -raw_delta

event_exposure = contracts * active_delta * pred_spot
perp_multiplier = 1 if perp_dir == "LONG" else -1
perp_exposure = total_perp_size * perp_multiplier  

is_offsetting = np.sign(event_exposure) != np.sign(perp_exposure)

var_perp = RiskMath.calc_isolated_var(perp_exposure, perp_cfg["perp_haircut"], z_score)
var_event = RiskMath.calc_isolated_var(event_exposure, 0.12, z_score) 

isolated, unified, surcharge = RiskMath.calc_unified_margin(
    var_perp, var_event, calculated_rho, is_offsetting, gamma, pred_spot, contracts
)

capital_unlocked = isolated - unified
efficiency_gain = (capital_unlocked / isolated) * 100 if isolated > 0 else 0

# ==========================================
# Visualizations
# ==========================================
if is_offsetting and abs(calculated_rho) > 0.1:
    st.success(f"Portfolio is Hedged.")
elif is_offsetting and abs(calculated_rho) <= 0.1:
    st.warning("Portfolio is NOT Correlated.")
else:
    st.error("Portfolio is Directional.")

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
col1.metric(label=f"Prediction Delta", value=f"{active_delta:.5f}")
col2.metric(label="Gamma Surcharge", value=f"${surcharge:,.2f}")
col3.metric(label="Capital Unlocked", value=f"${capital_unlocked:,.2f}", delta=f"+{efficiency_gain:.1f}% Efficiency")
col4.metric(label="Unified Margin", value=f"${unified:,.2f}")

st.markdown("---")

fig = go.Figure(data=[
    go.Bar(
        name='Isolated Margin', 
        x=['Collateral'], y=[isolated], 
        marker_color='#3f3f46', hovertemplate='$%{y:,.2f}<extra></extra>' 
    ),
    go.Bar(
        name='Unified Margin', 
        x=['Collateral'], y=[unified], 
        marker_color='#10b981' if is_offsetting else '#ef4444', hovertemplate='$%{y:,.2f}<extra></extra>' 
    )
])

fig.update_layout(
    title=f"Dual Margin: {perp_asset} Perp vs. {pred_asset} ({selected_bracket_label})",
    yaxis_title='Capital ($)',
    barmode='group',
    template='plotly_white',
    height=500
)

st.plotly_chart(fig, use_container_width=True)
