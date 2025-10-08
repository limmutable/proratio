# Proratio Documentation Index

**Last Updated**: 2025-10-09

Welcome to the Proratio documentation! This guide will help you navigate all available documentation.

---

## 📚 Quick Start Guides

Start here if you're new to Proratio:

### [QUICKSTART.md](QUICKSTART.md)
**Getting started with Proratio in 15 minutes**
- Initial setup and installation
- Environment configuration
- First dry-run test
- Basic commands

### [week4_quickstart.md](week4_quickstart.md)
**Week 4: Paper Trading Validation**
- Paper trading setup
- Monitoring dashboard
- Performance validation
- Transition to live trading

---

## 🎯 Core Guides

### Trading & Strategy

#### [paper_trading_guide.md](paper_trading_guide.md)
**Complete paper trading workflow**
- Dry-run configuration
- Risk parameters
- Monitoring and logging
- Performance analysis

#### [strategy_development_guide.md](strategy_development_guide.md)
**Develop and test trading strategies**
- Strategy architecture
- Indicator implementation
- Entry/exit logic
- AI signal integration

#### [3hour_test_guide.md](3hour_test_guide.md)
**Quick 3-hour validation test**
- Mean reversion strategy test
- Automated test scripts
- Real-time monitoring
- Results analysis

### Configuration & Setup

#### [TRADING_CONFIG_GUIDE.md](TRADING_CONFIG_GUIDE.md)
**Centralized configuration system**
- TradingConfig dataclasses
- Risk management settings
- Position sizing parameters
- AI provider configuration
- Execution settings

### Data & Backtesting

#### [data_management_workflow.md](data_management_workflow.md)
**Market data collection and management**
- Historical data download
- Data validation
- Storage optimization
- Update workflows

#### [backtesting_guide.md](backtesting_guide.md)
**Strategy backtesting and optimization**
- Backtesting workflow
- Hyperparameter optimization
- Performance metrics
- Result interpretation

### Monitoring & Control

#### [dashboard_guide.md](dashboard_guide.md)
**Streamlit dashboard for monitoring**
- Real-time trading status
- AI signal visualization
- Risk management monitoring
- Emergency controls
- System health status

---

## 🛠️ Reference Documentation

### [troubleshooting.md](troubleshooting.md)
**Common issues and solutions**
- Environment setup issues
- Freqtrade errors
- API connection problems
- Database issues
- Performance debugging

---

## 📦 Archive

Deprecated or outdated documentation (kept for reference):

- [archive/streamlit_dashboard_summary.md](archive/streamlit_dashboard_summary.md) - Replaced by dashboard_guide.md
- [archive/GEMINI.md](archive/GEMINI.md) - Old project overview (see README.md and CLAUDE.md)
- [archive/PLANREVIEW.md](archive/PLANREVIEW.md) - Initial plan review (see PLAN.md)

---

## 📖 Document Hierarchy

```
Quick Start
    ├── QUICKSTART.md (15-min setup)
    └── week4_quickstart.md (paper trading)

Trading Workflow
    ├── paper_trading_guide.md (full workflow)
    ├── strategy_development_guide.md (strategy dev)
    └── 3hour_test_guide.md (quick test)

Configuration
    └── TRADING_CONFIG_GUIDE.md (all settings)

Data & Analysis
    ├── data_management_workflow.md (data ops)
    └── backtesting_guide.md (testing)

Monitoring
    └── dashboard_guide.md (Streamlit UI)

Support
    └── troubleshooting.md (issues)
```

---

## 🎓 Learning Path

### Beginner
1. Start with [QUICKSTART.md](QUICKSTART.md)
2. Read [paper_trading_guide.md](paper_trading_guide.md)
3. Review [TRADING_CONFIG_GUIDE.md](TRADING_CONFIG_GUIDE.md)
4. Explore [dashboard_guide.md](dashboard_guide.md)

### Intermediate
1. Study [strategy_development_guide.md](strategy_development_guide.md)
2. Practice with [3hour_test_guide.md](3hour_test_guide.md)
3. Learn [data_management_workflow.md](data_management_workflow.md)
4. Master [backtesting_guide.md](backtesting_guide.md)

### Advanced
1. Develop custom strategies
2. Optimize hyperparameters
3. Integrate ML models
4. Deploy to live trading

---

## 🔗 External Resources

- **Freqtrade Docs**: https://www.freqtrade.io/
- **CCXT Docs**: https://docs.ccxt.com/
- **Binance API**: https://binance-docs.github.io/apidocs/spot/en/
- **Streamlit Docs**: https://docs.streamlit.io/

---

## 📝 Documentation Standards

All documentation follows these standards:
- **Markdown format** (.md files)
- **Clear section headers** with emojis for visual scanning
- **Code examples** with syntax highlighting
- **Command-line examples** ready to copy-paste
- **Updated timestamps** for version tracking

---

## 🤝 Contributing

When adding new documentation:
1. Follow the naming convention: `lowercase_with_underscores.md`
2. Add entry to this README.md index
3. Include "Last Updated" timestamp
4. Use clear section headers
5. Provide working code examples
6. Update CLAUDE.md if workflow changes

---

**Questions?** Check [troubleshooting.md](troubleshooting.md) or review the main [README.md](../README.md)
