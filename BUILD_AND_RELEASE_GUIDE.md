# Complete Build & Release Guide

## 📦 What We're Creating

### Package 1: SDK Wheel (league_sdk-1.0.0-py3-none-any.whl)
**Size:** ~50 KB
**Contains:** ONLY the SDK library (9 Python files)
**Use case:** Developers who want to use our SDK to build their own agents

### Package 2: Full System Archive (even-odd-league-v1.0.0.tar.gz)
**Size:** 2.2 MB
**Contains:** Complete project (778 files)
**Use case:** Anyone who wants to run or study the complete Even/Odd League system

---

## 🔨 Building the Packages

### Step 1: Build SDK Wheel

```bash
# Activate virtual environment
cd /Users/igornazarenko/PycharmProjects/LLM_Agent_Orchestration_HW7
source venv/bin/activate  # or: source .venv/bin/activate

# Install build tool
pip install build

# Build the wheel
cd SHARED/league_sdk
python -m build

# Output: dist/league_sdk-1.0.0-py3-none-any.whl
```

**What's in the wheel?**
- protocol.py (891 lines)
- logger.py
- retry.py
- config_loader.py
- config_models.py (458 lines)
- repositories.py (485 lines)
- utils.py
- cleanup.py
- queue_processor.py
- pyproject.toml (metadata)

**What's NOT in the wheel?**
- agents/ (not included)
- tests/ (not included)
- scripts/ (not included)
- docs/ (not included)

### Step 2: Full System Archive (Already Created!)

✅ **Already built:** `even-odd-league-v1.0.0.tar.gz` (2.2 MB, 778 files)

**What's in the archive?**
```
SHARED/               (SDK + configs)
agents/              (League Manager, 2 Referees, 4 Players)
tests/               (568 tests across 56 files)
doc/                 (All documentation)
scripts/             (12 automation scripts)
README.md
requirements.txt
pyproject.toml
PRD_EvenOddLeague.md
Missions_EvenOddLeague.md
PACKAGING_GUIDE.md
```

**Verify contents:**
```bash
tar -tzf even-odd-league-v1.0.0.tar.gz | head -50
tar -tzf even-odd-league-v1.0.0.tar.gz | wc -l  # Should show 778
```

---

## 📤 Uploading to GitHub Releases

### Option 1: Using GitHub Web Interface (Easiest)

1. **Go to GitHub:**
   ```
   https://github.com/YOUR-USERNAME/LLM_Agent_Orchestration_HW7/releases/new
   ```

2. **Create Release:**
   - **Tag:** `v1.0.0`
   - **Title:** `Even/Odd League v1.0.0 - Production Release`
   - **Description:** Copy from PACKAGING_GUIDE.md

3. **Upload Assets:**
   - Drag `SHARED/league_sdk/dist/league_sdk-1.0.0-py3-none-any.whl` (after building)
   - Drag `even-odd-league-v1.0.0.tar.gz` (already built)

4. **Publish!**

### Option 2: Using Git Command Line

```bash
# First, commit current changes
git add -A
git commit -m "feat: prepare v1.0.0 release with packaging improvements"
git push origin main

# Create and push tag
git tag -a v1.0.0 -m "Version 1.0.0 - Production Release"
git push origin v1.0.0

# Then upload assets via GitHub web interface
# (GitHub CLI can also upload, but web is easier)
```

### Option 3: Using GitHub CLI (if installed)

```bash
# Create release
gh release create v1.0.0 \
  --title "Even/Odd League v1.0.0 - Production Release" \
  --notes-file PACKAGING_GUIDE.md \
  SHARED/league_sdk/dist/league_sdk-1.0.0-py3-none-any.whl \
  even-odd-league-v1.0.0.tar.gz
```

---

## ✅ Testing the Packages

### Test 1: SDK Wheel

```bash
# Create fresh test environment
mkdir /tmp/test-sdk
cd /tmp/test-sdk
python3 -m venv venv
source venv/bin/activate

# Install SDK wheel
pip install /path/to/league_sdk-1.0.0-py3-none-any.whl

# Test import
python3 -c "
from league_sdk import protocol, logger, retry, config_loader
print('✅ SDK imports successfully')
print(f'Protocol module: {protocol.__file__}')
"

# Expected output:
# ✅ SDK imports successfully
# Protocol module: /tmp/test-sdk/venv/lib/python3.10/site-packages/league_sdk/protocol.py
```

**What you CAN do:**
```python
from league_sdk.protocol import MessageEnvelope, GAME_INVITATION
from league_sdk.logger import JsonLogger
from league_sdk.retry import call_with_retry

# Build your own custom agents using the SDK
```

**What you CANNOT do:**
```bash
./scripts/start_league.sh  # ❌ No scripts
pytest                      # ❌ No tests
```

---

### Test 2: Full System Archive

```bash
# Create fresh test environment
mkdir /tmp/test-full-system
cd /tmp/test-full-system

# Extract archive
tar -xzf /path/to/even-odd-league-v1.0.0.tar.gz

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e SHARED/league_sdk

# Run tests
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/unit/test_sdk/ -v

# Start system
./scripts/start_league.sh
./scripts/check_health.sh
```

**Expected output:**
```
✅ League Manager running on http://localhost:8000
✅ Referee REF01 running on http://localhost:8001
✅ Referee REF02 running on http://localhost:8002
✅ Player P01 running on http://localhost:8101
✅ Player P02 running on http://localhost:8102
✅ Player P03 running on http://localhost:8103
✅ Player P04 running on http://localhost:8104
```

---

## 📋 README Installation Methods Explained

### Method 1: Development Setup (Clone Repo)

```bash
git clone https://github.com/YOUR-USERNAME/LLM_Agent_Orchestration_HW7.git
cd LLM_Agent_Orchestration_HW7
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e SHARED/league_sdk  # Editable mode - changes take effect immediately
```

**You get:** Full source code, can modify anything, run all scripts

---

### Method 2A: Package Installation - SDK Only

```bash
pip install https://github.com/YOUR-USERNAME/LLM_Agent_Orchestration_HW7/releases/download/v1.0.0/league_sdk-1.0.0-py3-none-any.whl
```

**You get:** Just the SDK library installed in site-packages
**You can:** Build your own agents using our SDK
**You cannot:** Run our Even/Odd League system

---

### Method 2B: Package Installation - Full System

```bash
wget https://github.com/YOUR-USERNAME/LLM_Agent_Orchestration_HW7/releases/download/v1.0.0/even-odd-league-v1.0.0.tar.gz
tar -xzf even-odd-league-v1.0.0.tar.gz
cd even-odd-league-v1.0.0
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e SHARED/league_sdk
./scripts/start_league.sh
```

**You get:** Complete system, ready to run
**You can:** Run everything, modify code, deploy to production
**Difference from Method 1:** Same end result, just distributed as archive instead of git clone

---

## 🎯 Summary: What Each User Gets

| User Type | Recommended Method | What They Get |
|-----------|-------------------|---------------|
| **Library User** | SDK Wheel | SDK library only, build custom agents |
| **End User** | Full System Archive | Complete working system |
| **Developer/Contributor** | Git Clone | Full source + git history |

---

## ✅ Current Status

**Created:**
- ✅ `even-odd-league-v1.0.0.tar.gz` (2.2 MB, 778 files)

**To Create:**
- ⏳ `league_sdk-1.0.0-py3-none-any.whl` (run commands above)

**To Upload:**
- Both files to GitHub Releases

---

## 📝 Next Steps

1. **Build SDK wheel:**
   ```bash
   cd SHARED/league_sdk
   python -m build
   ```

2. **Verify both packages exist:**
   ```bash
   ls -lh SHARED/league_sdk/dist/league_sdk-1.0.0-py3-none-any.whl
   ls -lh even-odd-league-v1.0.0.tar.gz
   ```

3. **Create GitHub Release** (web interface or CLI)

4. **Upload both files as release assets**

5. **Test both installation methods** to verify they work

Done! 🎉
