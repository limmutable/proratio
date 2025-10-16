# Project Documentation

**Last Organized**: October 16, 2025

This directory contains project management and planning documentation for the Proratio trading system.

---

## 📁 Directory Structure

```
docs/project/
├── README.md                              # This file
│
├── 📋 Core Documentation (Active)
│   ├── roadmap.md                        # Development roadmap (Phase 1-10)
│   ├── project_structure.md              # Module architecture and code stats
│   ├── advanced_ai_strategies.md         # Phase 5-10 AI strategies guide
│   ├── file_naming_standards.md          # Project naming conventions
│   ├── phase46_llm_integration_test_20251016.md    # Phase 4.6 validation
│   └── strategy_registry_complete_20251016.md      # Strategy Registry docs
│
├── 🔒 security/                           # Security & technical debt
│   ├── security_scanning.md              # pip-audit setup guide
│   ├── pip_audit_note.md                 # pip-audit notes
│   └── technical_debt_gemini_review.md   # Code review from Gemini
│
└── 📦 phase4_archive/                     # Phase 4 historical docs
    ├── phase_4_implementation_summary.md
    ├── phase_4_test_summary.md
    ├── phase4_integration_status_20251015.md
    ├── ml_paper_trading_analysis_20251015.md
    ├── ensemble_model_training_summary_20251015.md
    ├── ensemble_model_training_guide.md
    ├── strategy_management_system_proposal.md
    └── strategy_registry_implementation_20251016.md
```

---

## 📖 Key Documents

### Start Here
1. **[roadmap.md](roadmap.md)** - Main development roadmap with phase breakdown
2. **[project_structure.md](project_structure.md)** - Module architecture overview

### Phase 4 Complete (Oct 16, 2025)
- **[phase46_llm_integration_test_20251016.md](phase46_llm_integration_test_20251016.md)** - Latest Phase 4.6 validation (LLM integration fix)
- **[strategy_registry_complete_20251016.md](strategy_registry_complete_20251016.md)** - Strategy Registry System docs

### Advanced Features (Phase 5-10)
- **[advanced_ai_strategies.md](advanced_ai_strategies.md)** - Detailed implementation guides for future phases

### Security & Quality
- **[security/security_scanning.md](security/security_scanning.md)** - Vulnerability scanning setup
- **[security/technical_debt_gemini_review.md](security/technical_debt_gemini_review.md)** - Code review and recommendations

---

## 🎯 Current Status

**Phase Progress**: Phase 1-4.6 Complete (92%)

**Completed**:
- ✅ Phase 1.0-1.4: MVP Foundation, Strategy Validation
- ✅ Phase 2.0: Advanced Strategies
- ✅ Phase 3.1-3.3: ML (FreqAI, LSTM, Ensemble)
- ✅ Phase 3.5: Technical Debt Resolution
- ✅ Phase 4.0: Hybrid ML+LLM Integration
- ✅ Phase 4.5: ML Paper Trading Validation
- ✅ Phase 4.6: LLM Integration Fix
- ✅ Strategy Registry System

**Next**: Phase 4.7 - Confidence Calibration

---

## 📂 Archive Organization

### phase4_archive/
Contains historical Phase 4 documentation. These docs were superseded by:
- **phase46_llm_integration_test_20251016.md** (replaces all Phase 4.0-4.5 docs)
- **strategy_registry_complete_20251016.md** (replaces proposal and implementation docs)

**Why archived**: Phase 4 went through multiple iterations (4.0 → 4.5 → 4.6). The latest docs contain all relevant information.

### ../obsolete/
Contains deprecated guides and summaries from earlier phases (Phase 1-3). See [../obsolete/README.md](../obsolete/README.md) if it exists.

---

## 🔍 Finding Information

### Development Planning
- Current phase: [roadmap.md](roadmap.md) → Current Status section
- Module details: [project_structure.md](project_structure.md)
- Future features: [advanced_ai_strategies.md](advanced_ai_strategies.md)

### Phase 4 Implementation
- Latest status: [phase46_llm_integration_test_20251016.md](phase46_llm_integration_test_20251016.md)
- Historical: [phase4_archive/](phase4_archive/)

### Strategy Management
- Registry system: [strategy_registry_complete_20251016.md](strategy_registry_complete_20251016.md)
- Registry file: [../../strategies/registry.json](../../strategies/registry.json)

### Security & Quality
- Security setup: [security/security_scanning.md](security/security_scanning.md)
- Code review: [security/technical_debt_gemini_review.md](security/technical_debt_gemini_review.md)
- Naming standards: [file_naming_standards.md](file_naming_standards.md)

---

## 📝 Document Naming Convention

Active docs follow this pattern:
- **Living docs** (continuously updated): `roadmap.md`, `project_structure.md`
- **Point-in-time snapshots**: `phase46_llm_integration_test_20251016.md` (YYYYMMDD format)
- **Completion docs**: `strategy_registry_complete_20251016.md`

See [file_naming_standards.md](file_naming_standards.md) for complete guidelines.

---

## 🔄 Maintenance

This directory was last organized on **October 16, 2025**.

**Maintenance tasks**:
- Move superseded docs to `phase4_archive/` or `../obsolete/`
- Keep only latest phase completion docs in root
- Update this README when adding new subdirectories
- Review quarterly and archive old snapshots

**Next review**: After Phase 4.7 completion

---

**For more documentation**: See [../README.md](../README.md) or [../index.md](../index.md)
