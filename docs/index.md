# Proratio Documentation Index

**Last Updated**: 2025-10-11

This is the main documentation index for the Proratio project. For the project overview, see [../README.md](../README.md).

> **Quick Links**: [Project Roadmap](roadmap.md) | [Project Progress](project_progress.md) | [Quickstart](quickstart.md)

---

## 📚 Quick Start

Start here if you're new to Proratio:

### [quickstart.md](quickstart.md)
**Getting started with Proratio in 15 minutes**
- Initial setup and installation
- Environment configuration
- First dry-run test
- Basic commands

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


### Project Management

#### [roadmap.md](roadmap.md)
**Complete development roadmap**
- 4-week MVP timeline
- Phase 2-5 roadmap
- Feature specifications
- Success metrics

#### [project_progress.md](project_progress.md)
**Current project status and progress**
- Completed milestones
- Current tasks
- Metrics and statistics
- Task backlog

### Configuration & Setup

#### [trading_config_guide.md](trading_config_guide.md)
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

## 📦 Obsolete Documentation

Deprecated or outdated documentation (kept for reference in `/docs/obsolete/`):

- [3hour_test_guide_obsolete.md](obsolete/3hour_test_guide_obsolete.md) - Time-specific test guide → See [paper_trading_guide.md](paper_trading_guide.md)
- [week4_quickstart_obsolete.md](obsolete/week4_quickstart_obsolete.md) - Week-specific guide → See [quickstart.md](quickstart.md)
- [phase2_summary_obsolete.md](obsolete/phase2_summary_obsolete.md) - Phase 2 snapshot → See [roadmap.md](roadmap.md)
- [phase2_guide_obsolete.md](obsolete/phase2_guide_obsolete.md) - Phase 2 guide → Merged into [strategy_development_guide.md](strategy_development_guide.md) and [backtesting_guide.md](backtesting_guide.md)
- [streamlit_dashboard_summary.md](obsolete/streamlit_dashboard_summary.md) - Old dashboard docs → See [dashboard_guide.md](dashboard_guide.md)
- [GEMINI.md](obsolete/GEMINI.md) - Old project overview → See main [README.md](../README.md) and [CLAUDE.md](../CLAUDE.md)
- [PLANREVIEW.md](obsolete/PLANREVIEW.md) - Initial plan review → See [roadmap.md](roadmap.md)
- [CLEANUP_SUMMARY_20251009.md](obsolete/CLEANUP_SUMMARY_20251009.md) - Historical cleanup notes

---

## 📖 Document Hierarchy

```
Quick Start
    └── quickstart.md (15-min setup)

Project Management
    ├── roadmap.md (development plan)
    └── project_progress.md (current status)

Trading Workflow
    ├── paper_trading_guide.md (full workflow)
    └── strategy_development_guide.md (strategy dev)

Configuration
    └── trading_config_guide.md (all settings)

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
1. Start with [quickstart.md](quickstart.md)
2. Read [paper_trading_guide.md](paper_trading_guide.md)
3. Review [trading_config_guide.md](trading_config_guide.md)
4. Explore [dashboard_guide.md](dashboard_guide.md)

### Intermediate
1. Study [strategy_development_guide.md](strategy_development_guide.md)
2. Practice with [paper_trading_guide.md](paper_trading_guide.md)
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
