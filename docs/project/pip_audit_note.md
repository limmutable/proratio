# pip-audit Pre-commit Hook Note

**Status**: Temporarily disabled in `.pre-commit-config.yaml`

## Issue

The `freqtrade==2025.9.1` dependency in `requirements.txt` causes pip-audit to fail during pre-commit:

```
ERROR: Could not find a version that satisfies the requirement freqtrade==2025.9.1
```

**Reason**: This version doesn't exist yet (future version placeholder for documentation).

## Solution Options

### Option 1: Manual Scanning (Current)
Run pip-audit manually, excluding problematic dependencies:

```bash
# Scan all except freqtrade
pip-audit -r <(grep -v "^freqtrade" requirements.txt)

# Or scan installed packages only
pip-audit
```

### Option 2: Update requirements.txt
Change to an actual available version:

```bash
# Check available versions
pip index versions freqtrade

# Update to latest actual version (e.g., 2024.9)
sed -i 's/freqtrade==2025.9.1/freqtrade==2024.9/' requirements.txt
```

### Option 3: Create requirements-audit.txt
Separate file for pip-audit with real versions:

```bash
# Create audit-friendly requirements
grep -v "^freqtrade" requirements.txt > requirements-audit.txt
echo "freqtrade==2024.9" >> requirements-audit.txt

# Update pre-commit hook to use requirements-audit.txt
```

## Recommendation

**For now**: Keep pip-audit commented out in pre-commit, run manually when needed.

**Long-term**: Update to Option 3 (separate requirements-audit.txt) once actual freqtrade version is determined.

## Manual Audit Schedule

- **Before each release**: Run manual pip-audit
- **Weekly**: Check for new vulnerabilities
- **After dependency updates**: Always audit

---

**Last Updated**: 2025-10-12
**Next Review**: When freqtrade version is finalized
