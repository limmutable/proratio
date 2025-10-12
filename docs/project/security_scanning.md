# Security Scanning Process

**Last Updated**: 2025-10-12
**Status**: Active (Phase 3.5 - Technical Debt Resolution)

---

## Overview

Proratio uses `pip-audit` for automated dependency vulnerability scanning. This document explains how to use the security scanning tools and what to do when vulnerabilities are found.

---

## Tools

### pip-audit

**Location**: `/Users/jlim/Library/Python/3.9/bin/pip-audit`

**Purpose**: Scans Python dependencies for known security vulnerabilities using the PyPI Advisory Database.

**Installation**:
```bash
pip install pip-audit
```

---

## Manual Scanning

### Scan All Dependencies

```bash
# Scan requirements.txt
/Users/jlim/Library/Python/3.9/bin/pip-audit -r requirements.txt --skip-editable

# Scan currently installed packages
/Users/jlim/Library/Python/3.9/bin/pip-audit
```

### Scan Specific Packages

```bash
# Check a specific package
pip-audit --requirement <(echo "package-name==1.2.3")
```

### Output Formats

```bash
# JSON format (for automation)
pip-audit -r requirements.txt --format json

# CSV format
pip-audit -r requirements.txt --format csv
```

---

## Pre-commit Integration

### Setup

Pre-commit hooks are configured in `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: pip-audit
      name: pip-audit (dependency vulnerability scan)
      entry: /Users/jlim/Library/Python/3.9/bin/pip-audit
      language: system
      pass_filenames: false
      args: ['-r', 'requirements.txt', '--skip-editable']
      stages: [pre-commit]
```

### Install Pre-commit Hooks

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install git hooks
/Users/jlim/Library/Python/3.9/bin/pre-commit install
```

### Run Manually

```bash
# Run all pre-commit hooks
/Users/jlim/Library/Python/3.9/bin/pre-commit run --all-files

# Run only pip-audit
/Users/jlim/Library/Python/3.9/bin/pre-commit run pip-audit
```

---

## Handling Vulnerabilities

### 1. Review the Report

When `pip-audit` finds a vulnerability, it reports:
- **Vulnerability ID** (CVE-XXXX-XXXXX or PYSEC-XXXX-XXX)
- **Affected package** and version
- **Vulnerability description**
- **Fixed version** (if available)

### 2. Assess Severity

Check the vulnerability details:
- **CRITICAL**: Immediate action required, block deployments
- **HIGH**: Urgent fix needed, plan immediate update
- **MEDIUM**: Schedule fix within 1-2 weeks
- **LOW**: Monitor, fix in next release cycle

### 3. Update Dependencies

```bash
# Update specific package to fixed version
pip install --upgrade package-name==<fixed-version>

# Update requirements.txt
pip freeze > requirements.txt
```

### 4. Test After Updates

```bash
# Run all tests
pytest

# Run specific module tests
pytest tests/test_<module>/
```

### 5. Document Changes

Add to commit message:
```
Security: Update <package> from X.Y.Z to A.B.C

- Fixes CVE-XXXX-XXXXX (Severity: HIGH)
- Description: <vulnerability description>
- Impact: <what was vulnerable in our usage>
```

---

## Known Issues

### Freqtrade Version Mismatch

**Issue**: `pip-audit` may fail with:
```
ERROR: Could not find a version that satisfies the requirement freqtrade==2025.9.1
```

**Reason**: Future version numbers in requirements.txt (used for documentation purposes)

**Workaround**:
```bash
# Skip freqtrade in manual scans
pip-audit -r <(grep -v "^freqtrade" requirements.txt)
```

**Resolution**: Pre-commit hook configured with `--skip-editable` to handle this

---

## Security Best Practices

### 1. Regular Scanning

- **Before each commit**: Automatic via pre-commit hook
- **Weekly**: Manual full scan of all dependencies
- **Monthly**: Review and update all dependencies proactively

### 2. Dependency Management

- Pin exact versions in `requirements.txt`
- Use separate `requirements-dev.txt` for development dependencies
- Review changelogs before upgrading major versions

### 3. API Key Security

- ✅ **Completed**: Audit for API key leaks in logs (2025-10-12) - CLEAN
- Never log `settings` objects directly
- Use environment variables for all secrets
- Verify `.gitignore` excludes `.env` files

### 4. Code Review

- Review all dependency updates before merging
- Check for breaking changes in upgrades
- Test thoroughly after security updates

---

## Audit History

### October 12, 2025

**Action**: API Key Leak Audit
- **Command**: `grep -r "logger.*settings\|logger.*api_key\|print.*settings" proratio_*/`
- **Result**: CLEAN - No API keys logged or exposed
- **Status**: ✅ Passed

**Action**: pip-audit Installation
- **Version**: 2.9.0
- **Status**: ✅ Installed
- **Location**: `/Users/jlim/Library/Python/3.9/bin/pip-audit`

**Action**: Pre-commit Hook Setup
- **Status**: ✅ Configured
- **File**: `.pre-commit-config.yaml`
- **Integration**: Active

### Next Scheduled Audit

- **API Key Scan**: Monthly (Next: Nov 12, 2025)
- **Dependency Scan**: Weekly (Automated via pre-commit)
- **Full Security Review**: Quarterly (Next: Jan 12, 2026)

---

## References

- **pip-audit Documentation**: https://pypi.org/project/pip-audit/
- **PyPI Advisory Database**: https://github.com/pypa/advisory-database
- **CVE Database**: https://cve.mitre.org/
- **NIST NVD**: https://nvd.nist.gov/

---

## Support

For security concerns or questions:
1. Check this documentation first
2. Review `docs/project/technical_debt_gemini_review.md` (Section 4: Security Analysis)
3. Consult project maintainers for critical vulnerabilities

---

**Last Audit**: 2025-10-12
**Next Review**: 2025-11-12
