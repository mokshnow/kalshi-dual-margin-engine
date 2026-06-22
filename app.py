import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.stats import norm

# ==========================================
# MATH
# ==========================================
class RiskMath:
    @staticmethod
    def calculate_binary_price(S, K, T, sigma, r=0.0325):
        if K == float('inf') or K <= 0:
            return 0.0
        T = max(T, 0.0001)
        d2 = (np.log(S / K) + (r - 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return np.exp(-r * T) * norm.cdf(d2)

    @staticmethod
    def calculate_range_price(S, K_lower, K_upper, T, sigma, r=0.0325):
        price_lower = RiskMath.calculate_binary_price(S, K_lower, T, sigma, r)
        price_upper = RiskMath.calculate_binary_price(S, K_upper, T, sigma, r)
        return max(0.0, price_lower - price_upper)

    @staticmethod
    def calculate_binary_call_greeks(S, K, T, sigma, r=0.0325):
        if K == float('inf') or K <= 0:
            return 0.0, 0.0
        T = max(T, 0.0001)
        d2 = (np.log(S / K) + (r - 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        delta = (np.exp(-r * T) * norm.pdf(d2)) / (sigma * S * np.sqrt(T))
        gamma = -delta * ((d2 + sigma * np.sqrt(T)) / (sigma * S * np.sqrt(T)) + 1 / S)
        return delta, gamma

    @staticmethod
    def calculate_range_greeks(S, K_lower, K_upper, T, sigma, r=0.0325):
        delta_lower, gamma_lower = RiskMath.calculate_binary_call_greeks(S, K_lower, T, sigma, r)
        delta_upper, gamma_upper = RiskMath.calculate_binary_call_greeks(S, K_upper, T, sigma, r)
        return delta_lower - delta_upper, gamma_lower - gamma_upper

    @staticmethod
    def calculate_dynamic_rho(S_current, K_lower, K_upper, T_current, sigma, days_history=90):
        np.random.seed(42)
        returns = np.random.normal(0, 0.03, days_history)
        
        spot_path = [S_current]
        for r in reversed(returns):
            spot_path.insert(0, spot_path[0] / np.exp(r))
        spot_path = np.array(spot_path)
        
        event_prices = []
        for i, S in enumerate(spot_path):
            T_historical = T_current + ((days_history - i) / 365.0)
            p = RiskMath.calculate_range_price(S, K_lower, K_upper, T_historical, sigma)
            event_prices.append(p)
            
        event_prices = np.array(event_prices) + 1e-6
        
        spot_returns = np.diff(np.log(spot_path))
        event_returns = np.diff(np.log(event_prices))
        
        rho = np.corrcoef(spot_returns, event_returns)[0, 1]
        
        return 0.0 if np.isnan(rho) else float(rho)

    @staticmethod
    def calc_isolated_var(exposure, vol, z_score):
        return abs(exposure * vol * z_score)

    @staticmethod
    def calc_unified_margin(var_perp, var_event, rho, is_offsetting, gamma, S, contracts, shock_pct=0.05):
        surcharge = 0.5 * abs(gamma) * ((S * shock_pct) ** 2) * abs(contracts)
        
        effective_rho = -abs(rho) if is_offsetting else abs(rho)
        unified_var_sq = (var_perp**2) + (var_event**2) + (2 * effective_rho * var_perp * var_event)
        base_unified = np.sqrt(max(0, unified_var_sq))
        
        total_unified = base_unified + surcharge
        isolated_total = var_perp + var_event + surcharge
        return isolated_total, total_unified, surcharge

# ==========================================
# DASHBOARD
# ==========================================
st.set_page_config(page_title=" Kalshi Dual Margin Engine", layout="wide")
st.title("Dual Margin Engine for Perps & Predictions")
st.markdown("Margin Efficiency for Coorelated BTC Perps and Predictions.")

# sidebar
st.sidebar.header("Market Parameters (BTC)")
spot_price = st.sidebar.slider("BTC Spot Price ($)", min_value=50000.0, max_value=100000.0, value=65000.0, step=1000.0)
vol = st.sidebar.slider("Event Implied Volatility", min_value=0.1, max_value=1.5, value=0.5, step=0.1)

st.sidebar.markdown("---")
st.sidebar.header("BTC Perp")
perp_dir = st.sidebar.radio("Position", ["LONG", "SHORT"], horizontal=True)
perp_cost = st.sidebar.number_input("Cost ($)", value=100000.0, step=1000.0)
perp_leverage = st.sidebar.slider("Leverage", min_value=1.0, max_value=6.0, value=3.0, step=0.1)

total_perp_size = perp_cost * perp_leverage
st.sidebar.caption(f"**Total Size ({perp_leverage}x):** ${total_perp_size:,.2f}")

st.sidebar.markdown("---")
st.sidebar.header("Bitcoin price at the end of 2026")
bracket = st.sidebar.selectbox("Select Price Bracket", [
    "< $49,999.99",
    "$50,000 to $54,999.99",
    "$55,000 to $59,999.99",
    "$60,000 to $64,999.99",
    "$65,000 to $69,999.99",
    "$70,000 to $74,999.99",
    "$75,000 to $79,999.99",
    "$80,000 to $84,999.99",
    "$85,000 to $89,999.99",
    "> $90,000"
])

# choices for prediction market
if bracket == "< $49,999.99":
    k_lower, k_upper = 0.001, 50000.0
elif bracket == "$50,000 to $54,999.99":
    k_lower, k_upper = 50000.0, 55000.0
elif bracket == "$55,000 to $59,999.99":
    k_lower, k_upper = 55000.0, 60000.0
elif bracket == "$60,000 to $64,999.99":
    k_lower, k_upper = 60000.0, 65000.0
elif bracket == "$65,000 to $69,999.99":
    k_lower, k_upper = 65000.0, 70000.0
elif bracket == "$70,000 to $74,999.99":
    k_lower, k_upper = 70000.0, 75000.0
elif bracket == "$75,000 to $79,999.99":
    k_lower, k_upper = 75000.0, 80000.0
elif bracket == "$80,000 to $84,999.99":
    k_lower, k_upper = 80000.0, 85000.0
elif bracket == "$85,000 to $89,999.99":
    k_lower, k_upper = 85000.0, 90000.0
else:
    k_lower, k_upper = 90000.0, float('inf')

event_dir = st.sidebar.radio("Shares", ["Yes Shares (Long)", "No Shares (Short)"], horizontal=True)
contracts = st.sidebar.number_input("Total Size (Shares)", value=100000, step=1000)

# ==========================================
# CALCULATIONS
# ==========================================
T_years = 193 / 365.0 
z_score = 2.326       

# --- DYNAMIC CORRELATION ENGINE ---
calculated_rho = RiskMath.calculate_dynamic_rho(spot_price, k_lower, k_upper, T_years, vol)

st.sidebar.markdown("---")
st.sidebar.success(f"**Correlation (rho):** {calculated_rho:.4f}")

# greeks
raw_delta, gamma = RiskMath.calculate_range_greeks(spot_price, k_lower, k_upper, T_years, vol)
active_delta = raw_delta if event_dir == "Yes Shares (Long)" else -raw_delta

# exposure
event_exposure = contracts * active_delta * spot_price
perp_multiplier = 1 if perp_dir == "LONG" else -1
perp_exposure = total_perp_size * perp_multiplier  

is_offsetting = np.sign(event_exposure) != np.sign(perp_exposure)

var_perp = RiskMath.calc_isolated_var(perp_exposure, 0.05, z_score)
var_event = RiskMath.calc_isolated_var(event_exposure, 0.12, z_score)

# optimizier
isolated, unified, surcharge = RiskMath.calc_unified_margin(
    var_perp, var_event, calculated_rho, is_offsetting, gamma, spot_price, contracts
)

capital_unlocked = isolated - unified
efficiency_gain = (capital_unlocked / isolated) * 100 if isolated > 0 else 0

# ==========================================
# DATA VISUALIZATION
# ==========================================
if is_offsetting and abs(calculated_rho) > 0.1:
    st.success(f"Portfolio is HEDGED (Offsetting Risk). Applying a {abs(calculated_rho)*100:.1f}% discount.")
elif is_offsetting and abs(calculated_rho) <= 0.1:
    st.warning("Portfolio is UNCORRELATED** — No significant margin discount.")
else:
    st.error("Portfolio is DIRECTIONAL (Compounding Risk)")

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Delta (Δ)", value=f"{active_delta:.5f}")
col2.metric(label="Gamma Surcharge", value=f"${surcharge:,.2f}")
col3.metric(label="Capital Unlocked", value=f"${capital_unlocked:,.2f}", delta=f"+{efficiency_gain:.1f}% Efficiency")
col4.metric(label="Unified Margin Req", value=f"${unified:,.2f}")

st.markdown("---")

fig = go.Figure(data=[
    go.Bar(
        name='Isolated Margin', 
        x=['Required Collateral'], 
        y=[isolated], 
        marker_color='#3f3f46',
        hovertemplate='$%{y:,.2f}<extra></extra>' # Forces clean dollar formatting
    ),
    go.Bar(
        name='Unified Margin', 
        x=['Required Collateral'], 
        y=[unified], 
        marker_color='#10b981' if is_offsetting else '#ef4444',
        hovertemplate='$%{y:,.2f}<extra></extra>' # Forces clean dollar formatting
    )
])

fig.update_layout(
    title=f"Dynamic Correlation Margin Profile: {bracket}",
    yaxis_title='Capital ($)',
    barmode='group',
    template='plotly_white',
    height=500
)

st.plotly_chart(fig, use_container_width=True)
