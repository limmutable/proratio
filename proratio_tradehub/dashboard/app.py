"""
Proratio Trading Dashboard

Real-time monitoring and control interface for the AI-driven trading system.
Provides live status, AI consensus visualization, risk monitoring, and emergency controls.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from proratio_utilities.config.trading_config import TradingConfig
from proratio_tradehub.risk.risk_manager import RiskManager
from proratio_signals.orchestrator import SignalOrchestrator
from proratio_tradehub.dashboard.system_status import SystemStatusChecker

# Page configuration
st.set_page_config(
    page_title="Proratio Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .risk-normal { color: #28a745; }
    .risk-warning { color: #ffc107; }
    .risk-critical { color: #dc3545; }
    .risk-halt { color: #6c757d; background-color: #f8d7da; }
    .ai-consensus {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .consensus-bullish { background-color: #d4edda; color: #155724; }
    .consensus-bearish { background-color: #f8d7da; color: #721c24; }
    .consensus-neutral { background-color: #fff3cd; color: #856404; }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'trading_enabled' not in st.session_state:
    st.session_state.trading_enabled = False
if 'emergency_stop' not in st.session_state:
    st.session_state.emergency_stop = False
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()


def load_trading_config() -> TradingConfig:
    """Load current trading configuration"""
    config_path = project_root / "proratio_utilities" / "config" / "trading_config.json"
    return TradingConfig.load_from_file(str(config_path))


def get_mock_trading_data() -> Dict:
    """
    Get current trading data from Freqtrade API

    TODO: Replace with actual Freqtrade API integration
    For now, returns mock data for dashboard development
    """
    return {
        "total_pnl": 1234.56,
        "pnl_pct": 12.34,
        "win_rate": 61.6,
        "total_trades": 73,
        "open_positions": 2,
        "max_positions": 3,
        "current_drawdown": 3.2,
        "max_drawdown": 10.0,
        "total_profit_trades": 45,
        "total_loss_trades": 28,
        "avg_profit": 2.3,
        "avg_loss": -1.8,
        "profit_factor": 1.42,
        "sharpe_ratio": 1.89,
        "active_trades": [
            {
                "pair": "BTC/USDT",
                "entry_price": 62500.00,
                "current_price": 63200.00,
                "pnl_pct": 1.12,
                "pnl_usd": 112.00,
                "duration": "2h 35m",
            },
            {
                "pair": "ETH/USDT",
                "entry_price": 3100.00,
                "current_price": 3085.00,
                "pnl_pct": -0.48,
                "pnl_usd": -48.00,
                "duration": "45m",
            }
        ]
    }


def get_ai_signals() -> Dict:
    """
    Get current AI signals from orchestrator

    TODO: Integrate with live SignalOrchestrator
    For now, returns mock data for dashboard development
    """
    return {
        "btc_usdt": {
            "direction": "long",
            "confidence": 0.72,
            "providers": {
                "chatgpt": {"signal": "long", "confidence": 0.68, "status": "unavailable"},
                "claude": {"signal": "long", "confidence": 0.78, "status": "active"},
                "gemini": {"signal": "long", "confidence": 0.70, "status": "active"}
            },
            "reasoning": "Strong uptrend confirmed by multiple indicators. RSI showing momentum, price above EMA crossover."
        },
        "eth_usdt": {
            "direction": "neutral",
            "confidence": 0.45,
            "providers": {
                "chatgpt": {"signal": "neutral", "confidence": 0.50, "status": "unavailable"},
                "claude": {"signal": "short", "confidence": 0.40, "status": "active"},
                "gemini": {"signal": "neutral", "confidence": 0.45, "status": "active"}
            },
            "reasoning": "Mixed signals. Consolidation pattern forming, awaiting breakout direction."
        }
    }


def render_sidebar():
    """Render sidebar with controls and settings"""
    with st.sidebar:
        st.title("🎛️ Control Panel")

        st.markdown("---")

        # Emergency Controls
        st.subheader("🚨 Emergency Controls")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("STOP ALL", type="secondary", width="stretch"):
                st.session_state.emergency_stop = True
                st.error("⚠️ Emergency stop activated!")

        with col2:
            if st.button("RESET", type="secondary", width="stretch"):
                st.session_state.emergency_stop = False
                st.success("✅ System reset")

        st.markdown("---")

        # Trading Controls
        st.subheader("⚙️ Trading Controls")

        st.session_state.trading_enabled = st.toggle(
            "Enable Trading",
            value=st.session_state.trading_enabled,
            help="Enable/disable automated trading"
        )

        auto_refresh = st.checkbox("Auto-refresh (10s)", value=True)

        st.markdown("---")

        # Quick Stats
        st.subheader("📊 Quick Stats")
        config = load_trading_config()

        st.metric("Risk Level", f"{config.risk.max_loss_per_trade_pct:.1f}%",
                 help="Maximum loss per trade")
        st.metric("Position Size", f"{config.position_sizing.base_risk_pct:.1f}%",
                 help="Base risk percentage")
        st.metric("Max Positions", config.risk.max_concurrent_positions,
                 help="Maximum concurrent positions")

        st.markdown("---")

        # System Status
        st.subheader("🔧 System Status")

        # Get real-time system status
        status_checker = SystemStatusChecker()
        all_status = status_checker.get_all_status()
        summary = status_checker.get_summary()

        # Display overall health
        health_pct = summary['health_pct']
        if health_pct >= 85:
            health_color = "🟢"
            health_text = "Healthy"
        elif health_pct >= 60:
            health_color = "🟡"
            health_text = "Degraded"
        else:
            health_color = "🔴"
            health_text = "Critical"

        st.caption(f"{health_color} System Health: **{health_text}** ({health_pct:.0f}%)")
        st.caption(f"✅ {summary['available']} | ⚠️ {summary['warnings']} | ❌ {summary['unavailable']}")

        # Display individual service status
        for service_key, status in all_status.items():
            if status.is_available:
                if "⚠️" in status.icon:
                    st.warning(f"{status.icon} {status.name}: {status.message}")
                else:
                    st.success(f"{status.icon} {status.name}: {status.message}")
            else:
                st.error(f"{status.icon} {status.name}: {status.message}")

        st.markdown("---")

        # Last Update
        st.caption(f"Last update: {st.session_state.last_update.strftime('%H:%M:%S')}")

        if auto_refresh:
            st.session_state.last_update = datetime.now()


def render_performance_overview():
    """Render main performance metrics"""
    st.header("📈 Performance Overview")

    data = get_mock_trading_data()

    # Top metrics row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Total P&L",
            value=f"${data['total_pnl']:.2f}",
            delta=f"{data['pnl_pct']:.2f}%"
        )

    with col2:
        st.metric(
            label="Win Rate",
            value=f"{data['win_rate']:.1f}%",
            delta=f"{data['total_profit_trades']}/{data['total_trades']} wins"
        )

    with col3:
        st.metric(
            label="Open Positions",
            value=f"{data['open_positions']}/{data['max_positions']}",
        )

    with col4:
        drawdown_delta = f"{data['current_drawdown']:.1f}% / {data['max_drawdown']:.1f}% max"
        st.metric(
            label="Drawdown",
            value=f"{data['current_drawdown']:.1f}%",
            delta=drawdown_delta,
            delta_color="inverse"
        )

    with col5:
        st.metric(
            label="Sharpe Ratio",
            value=f"{data['sharpe_ratio']:.2f}",
            delta="Good" if data['sharpe_ratio'] > 1.5 else "Fair"
        )

    # Additional metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Profit Factor", f"{data['profit_factor']:.2f}")

    with col2:
        st.metric("Avg Profit", f"{data['avg_profit']:.2f}%")

    with col3:
        st.metric("Avg Loss", f"{data['avg_loss']:.2f}%")

    with col4:
        st.metric("Total Trades", data['total_trades'])


def render_active_positions():
    """Render active trading positions"""
    st.subheader("💼 Active Positions")

    data = get_mock_trading_data()

    if not data['active_trades']:
        st.info("No active positions")
        return

    # Create DataFrame for positions
    df = pd.DataFrame(data['active_trades'])

    # Format columns
    df['Entry Price'] = df['entry_price'].apply(lambda x: f"${x:,.2f}")
    df['Current Price'] = df['current_price'].apply(lambda x: f"${x:,.2f}")
    df['P&L %'] = df['pnl_pct'].apply(lambda x: f"{x:+.2f}%")
    df['P&L USD'] = df['pnl_usd'].apply(lambda x: f"${x:+.2f}")
    df['Pair'] = df['pair']
    df['Duration'] = df['duration']

    # Display table
    st.dataframe(
        df[['Pair', 'Entry Price', 'Current Price', 'P&L %', 'P&L USD', 'Duration']],
        width="stretch",
        hide_index=True
    )


def render_ai_consensus():
    """Render AI consensus signals"""
    st.header("🤖 AI Signal Consensus")

    signals = get_ai_signals()

    for pair, signal_data in signals.items():
        st.subheader(f"{pair.replace('_', '/').upper()}")

        # Overall consensus
        direction = signal_data['direction']
        confidence = signal_data['confidence']

        consensus_class = {
            'long': 'consensus-bullish',
            'short': 'consensus-bearish',
            'neutral': 'consensus-neutral'
        }[direction]

        col1, col2, col3 = st.columns([2, 1, 3])

        with col1:
            st.markdown(
                f"<div class='ai-consensus {consensus_class}'>"
                f"<strong>Signal:</strong> {direction.upper()} | "
                f"<strong>Confidence:</strong> {confidence:.0%}"
                f"</div>",
                unsafe_allow_html=True
            )

        with col2:
            # Confidence gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=confidence * 100,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 40], 'color': "lightgray"},
                        {'range': [40, 60], 'color': "yellow"},
                        {'range': [60, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 60
                    }
                }
            ))
            fig.update_layout(height=150, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col3:
            st.caption("**Reasoning:**")
            st.write(signal_data['reasoning'])

        # Individual provider signals
        st.markdown("**Provider Breakdown:**")

        provider_cols = st.columns(3)

        for idx, (provider, provider_data) in enumerate(signal_data['providers'].items()):
            with provider_cols[idx]:
                status = provider_data['status']
                status_icon = "✅" if status == "active" else "❌"

                st.markdown(
                    f"**{provider.title()}** {status_icon}<br>"
                    f"Signal: {provider_data['signal'].upper()}<br>"
                    f"Confidence: {provider_data['confidence']:.0%}",
                    unsafe_allow_html=True
                )

        st.markdown("---")


def render_risk_dashboard():
    """Render risk management dashboard"""
    st.header("⚠️ Risk Management")

    config = load_trading_config()
    data = get_mock_trading_data()

    # Risk status indicator
    current_drawdown = data['current_drawdown']
    max_drawdown_limit = config.risk.max_total_drawdown_pct

    if current_drawdown >= max_drawdown_limit:
        risk_level = "HALT"
        risk_class = "risk-halt"
    elif current_drawdown >= max_drawdown_limit * 0.8:
        risk_level = "CRITICAL"
        risk_class = "risk-critical"
    elif current_drawdown >= max_drawdown_limit * 0.6:
        risk_level = "WARNING"
        risk_class = "risk-warning"
    else:
        risk_level = "NORMAL"
        risk_class = "risk-normal"

    st.markdown(
        f"<h2 class='{risk_class}'>Risk Level: {risk_level}</h2>",
        unsafe_allow_html=True
    )

    # Risk metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Current Drawdown",
            f"{current_drawdown:.2f}%",
            delta=f"{max_drawdown_limit:.1f}% limit",
            delta_color="inverse"
        )

    with col2:
        position_usage = (data['open_positions'] / data['max_positions']) * 100
        st.metric(
            "Position Usage",
            f"{position_usage:.0f}%",
            delta=f"{data['open_positions']}/{data['max_positions']} used"
        )

    with col3:
        max_loss_per_trade = config.risk.max_loss_per_trade_pct * 100
        st.metric(
            "Max Loss/Trade",
            f"{max_loss_per_trade:.1f}%",
            delta="Per position limit"
        )

    with col4:
        max_leverage = config.risk.max_leverage
        st.metric(
            "Max Leverage",
            f"{max_leverage:.1f}x",
            delta="Spot only" if max_leverage == 1.0 else "Futures enabled"
        )

    # Drawdown progress bar
    st.subheader("Drawdown vs. Limit")
    drawdown_pct = (current_drawdown / max_drawdown_limit) * 100
    st.progress(min(drawdown_pct / 100, 1.0))
    st.caption(f"{current_drawdown:.2f}% / {max_drawdown_limit:.1f}% maximum ({drawdown_pct:.0f}% of limit)")

    # Risk limits table
    st.subheader("Risk Limits Configuration")

    limits_data = {
        "Risk Parameter": [
            "Max Loss Per Trade",
            "Warning Drawdown",
            "Max Total Drawdown",
            "Max Concurrent Positions",
            "Max Position Size",
        ],
        "Current Limit": [
            f"{config.risk.max_loss_per_trade_pct:.1f}%",
            f"{config.risk.warning_drawdown_pct:.1f}%",
            f"{config.risk.max_total_drawdown_pct:.1f}%",
            str(config.risk.max_concurrent_positions),
            f"{config.risk.max_position_size_pct:.1f}%",
        ],
        "Current Value": [
            f"{data['avg_loss']:.2f}%",
            f"{current_drawdown:.2f}%",
            f"{current_drawdown:.2f}%",
            f"{data['open_positions']}/{data['max_positions']}",
            f"{config.position_sizing.base_risk_pct:.1f}%",
        ],
        "Status": [
            "✅ OK" if abs(data['avg_loss']) < config.risk.max_loss_per_trade_pct else "⚠️ WARNING",
            "✅ OK",
            "✅ OK" if current_drawdown < max_drawdown_limit else "🚨 CRITICAL",
            "✅ OK",
            "✅ OK",
        ]
    }

    st.dataframe(
        pd.DataFrame(limits_data),
        width="stretch",
        hide_index=True
    )


def render_configuration_viewer():
    """Render configuration viewer"""
    st.header("⚙️ Trading Configuration")

    config = load_trading_config()

    tabs = st.tabs(["Risk", "Position Sizing", "Strategy", "AI", "Execution"])

    with tabs[0]:  # Risk
        st.subheader("Risk Management Settings")
        risk_data = {
            "Parameter": [
                "Max Loss Per Trade",
                "Max Position Size",
                "Min Position Size",
                "Warning Drawdown",
                "Max Total Drawdown",
                "Max Concurrent Positions",
                "Max Positions Per Pair",
                "Max Leverage",
            ],
            "Value": [
                f"{config.risk.max_loss_per_trade_pct:.2f}%",
                f"{config.risk.max_position_size_pct:.2f}%",
                f"{config.risk.min_position_size_pct:.2f}%",
                f"{config.risk.warning_drawdown_pct:.2f}%",
                f"{config.risk.max_total_drawdown_pct:.2f}%",
                str(config.risk.max_concurrent_positions),
                str(config.risk.max_positions_per_pair),
                f"{config.risk.max_leverage:.1f}x",
            ]
        }
        st.dataframe(pd.DataFrame(risk_data), width="stretch", hide_index=True)

    with tabs[1]:  # Position Sizing
        st.subheader("Position Sizing Settings")
        pos_data = {
            "Parameter": [
                "Method",
                "Base Risk %",
                "AI Confidence Min",
                "AI Multiplier Min",
                "AI Multiplier Max",
            ],
            "Value": [
                config.position_sizing.method,
                f"{config.position_sizing.base_risk_pct:.2f}%",
                f"{config.position_sizing.ai_confidence_min:.0%}",
                f"{config.position_sizing.ai_confidence_multiplier_min:.2f}x",
                f"{config.position_sizing.ai_confidence_multiplier_max:.2f}x",
            ]
        }
        st.dataframe(pd.DataFrame(pos_data), width="stretch", hide_index=True)

    with tabs[2]:  # Strategy
        st.subheader("Strategy Settings")
        strat_data = {
            "Parameter": [
                "Strategy Name",
                "Timeframe",
                "Trading Pairs",
                "EMA Fast Period",
                "EMA Slow Period",
                "RSI Period",
            ],
            "Value": [
                config.strategy.strategy_name,
                config.strategy.timeframe,
                ", ".join(config.strategy.pairs),
                str(config.strategy.ema_fast_period),
                str(config.strategy.ema_slow_period),
                str(config.strategy.rsi_period),
            ]
        }
        st.dataframe(pd.DataFrame(strat_data), width="stretch", hide_index=True)

    with tabs[3]:  # AI
        st.subheader("AI Settings")
        ai_data = {
            "Parameter": [
                "Min Consensus Score",
                "Min Confidence",
                "ChatGPT Weight",
                "Claude Weight",
                "Gemini Weight",
                "Signal Timeout",
            ],
            "Value": [
                f"{config.ai.min_consensus_score:.0%}",
                f"{config.ai.min_confidence:.0%}",
                f"{config.ai.chatgpt_weight:.0%}",
                f"{config.ai.claude_weight:.0%}",
                f"{config.ai.gemini_weight:.0%}",
                f"{config.ai.signal_timeout_seconds}s" if hasattr(config.ai, 'signal_timeout_seconds') else "N/A",
            ]
        }
        st.dataframe(pd.DataFrame(ai_data), width="stretch", hide_index=True)

    with tabs[4]:  # Execution
        st.subheader("Execution Settings")
        exec_data = {
            "Parameter": [
                "Exchange",
                "Trading Mode",
                "Entry Order Type",
                "Exit Order Type",
                "Stoploss Order Type",
                "Stoploss on Exchange",
            ],
            "Value": [
                config.execution.exchange,
                config.execution.trading_mode,
                config.execution.entry_order_type,
                config.execution.exit_order_type,
                config.execution.stoploss_order_type,
                "✅ Yes" if config.execution.stoploss_on_exchange else "❌ No",
            ]
        }
        st.dataframe(pd.DataFrame(exec_data), width="stretch", hide_index=True)


def main():
    """Main dashboard application"""

    # Render sidebar
    render_sidebar()

    # Main title
    st.title("📊 Proratio Trading Dashboard")
    st.caption("AI-Driven Cryptocurrency Trading System")

    # Emergency stop banner
    if st.session_state.emergency_stop:
        st.error("🚨 **EMERGENCY STOP ACTIVATED** - All trading halted. Reset in sidebar to resume.")

    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Live Trading",
        "🤖 AI Signals",
        "⚠️ Risk Management",
        "⚙️ Configuration"
    ])

    with tab1:
        render_performance_overview()
        st.markdown("---")
        render_active_positions()

    with tab2:
        render_ai_consensus()

    with tab3:
        render_risk_dashboard()

    with tab4:
        render_configuration_viewer()

    # Footer
    st.markdown("---")
    st.caption("Proratio v0.3.0 | Dashboard v1.0 | Week 4 MVP")


if __name__ == "__main__":
    main()
