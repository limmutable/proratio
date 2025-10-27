# Proratio Constitution

## Core Principles

### I. Modular Architecture (NON-NEGOTIABLE)

The system MUST be organized into four independent, self-contained modules:

- **Proratio Utilities**: Core infrastructure, data collection, execution engine, configuration management
- **Proratio Signals**: AI/LLM integration, ML models, signal generation, consensus mechanisms
- **Proratio QuantLab**: Backtesting, research, model training, feature engineering, analytics
- **Proratio TradeHub**: Strategy orchestration, portfolio management, risk management

**Requirements**:
- Each module MUST be independently testable with its own test suite
- Modules MUST communicate through well-defined interfaces
- Dependencies MUST flow in one direction: TradeHub → Signals → QuantLab → Utilities
- No circular dependencies allowed
- Each module MUST have clear ownership of its domain logic

**Rationale**: Modularity enables parallel development, isolated testing, and incremental improvements without system-wide regression.

### II. Test-First Development (NON-NEGOTIABLE)

All new features and bug fixes MUST follow Test-Driven Development:

1. **Write tests first** - Define expected behavior through tests
2. **Get user/stakeholder approval** - Verify tests match requirements
3. **Red phase** - Run tests and confirm they fail
4. **Green phase** - Implement minimal code to make tests pass
5. **Refactor phase** - Improve code while keeping tests green

**Testing standards**:
- Minimum 80% code coverage for new code
- All public APIs MUST have unit tests
- Integration tests MUST cover module boundaries
- Use pytest exclusively (no unittest or other frameworks)
- Mock external dependencies (APIs, exchanges, databases) in unit tests

**Rationale**: TDD catches bugs early, provides living documentation, and enables confident refactoring.

### III. Strategy Validation Framework (NON-NEGOTIABLE)

All trading strategies MUST pass the validation framework before paper trading:

**Pre-deployment validation** (5-10 minutes):
1. **Pre-flight checks** - Strategy file exists, imports work, data available
2. **Accelerated backtest** - 6 months of historical data, multiple timeframes
3. **Performance gates** - Win rate ≥45%, max drawdown <25%, Sharpe ≥0.5, profit factor ≥1.0
4. **Integration tests** - Verify strategy interfaces (populate_indicators, populate_entry_trend, etc.)
5. **Code quality** - Ruff linting passes with zero errors
6. **Documentation** - Strategy metadata complete in registry

**Paper trading** (24-48 hours minimum after validation passes):
- Real-time market data with simulated execution
- Monitor for edge cases, API failures, unexpected behavior
- Verify risk management rules enforced

**Live trading approval**:
- Validation MUST pass
- Paper trading MUST show consistent behavior
- Risk parameters MUST be reviewed and approved
- Emergency stop procedures MUST be documented

**Rationale**: Validation framework provides 60-120x faster feedback than paper trading alone, preventing deployment of broken strategies.

### IV. Configuration as Code

All system configuration MUST follow these principles:

**Single source of truth**:
- Secrets and environment-specific settings in `.env` only (NEVER commit)
- JSON configuration files are templates (safe to commit)
- Runtime hydration injects secrets from `.env` into config templates
- Validation ensures required settings are present before execution

**Configuration structure**:
- Centralized configuration in `proratio_utilities/config/`
- Strategy-specific config in `strategies/<strategy_id>/config.json`
- Freqtrade configs in `proratio_utilities/config/freqtrade/`
- Trading parameters in `proratio_utilities/config/trading_config.json`

**Security requirements**:
- API keys, tokens, passwords MUST only exist in `.env`
- Secrets MUST NOT be logged or written to disk
- Git pre-commit hooks MUST scan for exposed secrets
- Configuration hydration MUST be auditable (logged)

**Rationale**: Separation of secrets from templates enables safe version control, environment isolation, and secure deployments.

### V. Risk Management First

Financial safety MUST be built into every layer:

**Six layers of risk control** (all MUST be enforced):
1. **Position sizing** - Max 2% risk per trade, Kelly Criterion or AI-weighted
2. **Stop loss** - Every position MUST have a stop loss (2-3.5% typical)
3. **Take profit** - Risk/reward ratio minimum 2:1
4. **Portfolio limits** - Max 2-3 concurrent trades, 10% max drawdown halt, 5% daily loss limit
5. **Market condition filters** - Volatility, volume, spread checks before entry
6. **AI confidence threshold** - Minimum 65% confidence, 70% ML-LLM agreement

**Emergency controls**:
- Manual emergency stop button (close all positions immediately)
- Automatic trading halt on max drawdown or daily loss limit
- Kill switch for individual strategies
- Dry-run mode MUST work identically to live mode (except execution)

**Monitoring requirements**:
- Real-time position tracking
- Risk metric dashboard
- Alert system for threshold breaches
- Trade logs with full context (signals, confidence, market conditions)

**Rationale**: Trading systems MUST protect capital first, optimize returns second. Multiple independent risk layers prevent catastrophic losses.

### VI. AI/ML Consensus and Transparency

AI and machine learning predictions MUST be:

**Consensus-based decision making**:
- Multi-LLM analysis (ChatGPT, Claude, Gemini) with weighted voting
- ML ensemble (LSTM, LightGBM, XGBoost) with stacking or blending
- Hybrid ML+LLM signals require agreement between both systems
- Conflict resolution: ALWAYS skip trades when ML and LLM disagree

**Explainability requirements**:
- Every signal MUST include reasoning/explanation
- Confidence scores MUST be calibrated and interpretable
- Feature importance MUST be tracked for ML models
- Trade decisions MUST be auditable (logs capture full context)

**Model governance**:
- Models MUST be versioned (semantic versioning)
- Training data MUST be tracked (lineage, date ranges, sources)
- Performance metrics MUST be monitored in production
- Model drift detection MUST trigger retraining alerts
- A/B testing framework for comparing models/strategies

**Rationale**: AI systems are only as good as their transparency and accountability. Consensus reduces false signals; explainability builds trust.

### VII. Observability and Debugging

System behavior MUST be observable at all times:

**Structured logging**:
- Use Python `logging` module exclusively (no print statements)
- Log levels: DEBUG (development), INFO (production operations), WARNING (degraded state), ERROR (failures)
- Contextual logging: Include trade IDs, strategy names, timestamps, relevant data
- Centralized log aggregation for analysis

**Monitoring and alerts**:
- System health checks (API connectivity, database status, disk space)
- Trading metrics (win rate, drawdown, Sharpe ratio, daily P&L)
- Model performance (prediction accuracy, confidence calibration)
- Alert channels: Logs, Telegram (optional), dashboard

**Debuggability**:
- Reproducible environments (Docker, requirements.txt pinned versions)
- Debug mode for step-by-step strategy execution
- Data snapshots for issue investigation
- Backtest replay for production issues

**Performance tracking**:
- Strategy performance reports (daily, weekly, monthly)
- Comparison against baselines and benchmarks
- Attribution analysis (which signals drove performance)

**Rationale**: Trading systems operate in production 24/7; observability enables rapid issue detection and resolution.

### VIII. Code Quality and Style

All code MUST meet these standards:

**Python style** (enforced by Ruff):
- Black-compatible formatting (88 char line length)
- Import order: 1. standard library, 2. third-party, 3. application-specific
- Type hints for all function signatures (`Optional` for nullable types)
- Naming: `snake_case` for functions/variables, `PascalCase` for classes
- Google-style docstrings for all public modules, classes, and functions

**Error handling**:
- Use specific custom exceptions (defined in each module)
- Never use bare `except:` clauses
- Always clean up resources (context managers, try/finally)
- Graceful degradation (log and continue when possible, fail fast when critical)

**Code organization**:
- Functions ≤50 lines (prefer smaller)
- Classes with single responsibility
- Pure functions where possible (no side effects)
- Avoid premature optimization (readability first, then optimize)

**Documentation**:
- README for each module
- Inline comments for complex logic
- Architecture Decision Records (ADRs) for major design choices
- API documentation auto-generated from docstrings

**Rationale**: Consistent code style reduces cognitive load, improves collaboration, and minimizes bugs.

## Security Requirements

### API Key Management

- API keys MUST be stored in `.env` only (never in code or JSON)
- Git pre-commit hooks MUST scan for exposed secrets (using pip-audit)
- Production keys MUST be different from testing/development keys
- Key rotation procedures MUST be documented

### Dependency Security

- Run `pip-audit` on every dependency update
- Pin all dependencies with exact versions in `requirements.txt`
- Security vulnerabilities MUST be addressed within 7 days
- No dependencies with known critical CVEs

### Data Privacy

- Personal trading data MUST NOT be shared or logged to external services
- Database backups MUST be encrypted
- No sensitive data in error messages or logs
- Audit trail for configuration changes

## Development Workflow

### Feature Development Process

1. **Specification** - Create spec.md in `specs/<feature-id>/` using SpecKit
2. **Planning** - Create plan.md with architecture, phases, and tasks using SpecKit
3. **Task breakdown** - Create tasks.md with implementation checklist using SpecKit
4. **Analysis** - Run `/speckit.analyze` to validate consistency across artifacts
5. **Branch creation** - Create feature branch `<feature-id>-<feature-name>`
6. **TDD implementation** - Write tests first, implement, refactor
7. **Validation** - Run tests, linting, validation framework
8. **Documentation** - Update relevant docs, add completion report
9. **Pull request** - Review, approve, merge to main

### Strategy Development Process

1. **Research** - Backtest concept in Jupyter notebook
2. **Registration** - Add strategy to `strategies/registry.json`
3. **Implementation** - Create strategy file in `strategies/active/<id>_<name>/`
4. **Testing** - Write unit tests, integration tests
5. **Validation** - Run validation framework (`./start.sh strategy validate`)
6. **Paper trading** - Monitor 24-48 hours in dry-run mode
7. **Review** - Performance review, risk parameter approval
8. **Deployment** - Enable in production with monitoring

### Code Review Standards

All pull requests MUST have:
- Tests with >80% coverage
- Ruff linting passes (zero errors)
- Documentation updated
- At least one approval
- All CI/CD checks passing

## Quality Gates

### Pre-Commit (Local)

- Ruff formatting and linting MUST pass
- Type checking MUST pass (mypy where configured)
- Pre-commit hooks MUST pass (secret scanning)

### Pre-Merge (CI/CD)

- All tests MUST pass (186+ tests)
- Code coverage MUST be ≥80% for new code
- Strategy validation MUST pass (if strategy changed)
- Security scan MUST pass (pip-audit)
- Documentation build MUST succeed

### Pre-Production

- Paper trading MUST show expected behavior (24-48 hours)
- Risk parameters MUST be reviewed and approved
- Rollback plan MUST be documented
- Monitoring/alerting MUST be configured

## Governance

### Constitution Authority

This constitution is the **highest authority** for all development decisions:

- All features, changes, and decisions MUST align with these principles
- Conflicts between this constitution and other documentation/practices are resolved in favor of the constitution
- Team members MUST raise concerns when they observe violations
- "Move fast and break things" is explicitly rejected in favor of "move deliberately and protect capital"

### Amendment Process

Constitution amendments require:

1. **Proposal** - Document proposed change with rationale
2. **Impact analysis** - Identify affected systems, code, and workflows
3. **Discussion** - Review with stakeholders, gather feedback
4. **Approval** - Explicit approval required
5. **Migration plan** - Document how to transition from old to new principle
6. **Version bump** - Increment version using semantic versioning:
   - **MAJOR**: Backward-incompatible principle removal or redefinition
   - **MINOR**: New principle added or materially expanded guidance
   - **PATCH**: Clarifications, wording, typo fixes, non-semantic refinements
7. **Communication** - Announce change, update dependent documentation

### Compliance Verification

- All pull requests MUST verify constitutional compliance
- Code reviews MUST check for principle violations
- Quarterly constitution review to ensure it remains relevant
- Automated checks where possible (linting, testing, validation)

### Runtime Development Guidance

For day-to-day development practices, refer to:
- **[AGENTS.md](../../AGENTS.md)** - AI agent development guidelines
- **[README.md](../../README.md)** - Project overview and quick start
- **[docs/](../../docs/)** - Detailed guides and reference materials

**Version**: 1.0.0 | **Ratified**: 2025-10-27 | **Last Amended**: 2025-10-27
