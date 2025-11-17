# Python Path Fix Summary

## Issue

When running Python scripts from the `src/` directory, you encountered:
```
ModuleNotFoundError: No module named 'src'
```

This happens because Python couldn't find the `src` module in its path.

## Root Cause

The scripts use absolute imports like `from src.services.chatbot_service import ...`, which requires the project root to be in Python's module search path (PYTHONPATH).

## Solutions Implemented

### 1. Helper Scripts (Recommended)

Created two helper scripts that automatically set the PYTHONPATH:

**`run_chatbot.sh`**:
```bash
#!/bin/bash
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"
python src/api/chatbot_api.py
```

**`run_ml_api.sh`**:
```bash
#!/bin/bash
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"
python src/api/ml_api.py
```

**Usage**:
```bash
# Start chatbot API
./run_chatbot.sh

# Start ML API
./run_ml_api.sh
```

### 2. Manual PYTHONPATH Setting

You can also set PYTHONPATH manually:

```bash
# One-time for a single command
PYTHONPATH=. python src/api/chatbot_api.py

# Export for the entire session
export PYTHONPATH="${PWD}:${PYTHONPATH}"
python src/api/chatbot_api.py
```

### 3. Python Module Flag

Use Python's `-m` flag to run as a module:

```bash
python -m src.api.chatbot_api
```

### 4. Permanent Fix (Optional)

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export PYTHONPATH="/Users/juettner/Projects/aws-immersion-demo-11192025:${PYTHONPATH}"
```

## Updated Documentation

### Files Created
1. **`run_chatbot.sh`** - Helper script to start chatbot API
2. **`run_ml_api.sh`** - Helper script to start ML API
3. **`TROUBLESHOOTING.md`** - Comprehensive troubleshooting guide
4. **`PYTHON_PATH_FIX_SUMMARY.md`** - This file

### Files Updated
1. **`DEMO_README.md`** - Updated service start commands
2. **`docs/guides/DEMO_EXECUTION_GUIDE.md`** - Updated chatbot start instructions
3. **`README.md`** - Added link to troubleshooting guide

## How to Use

### Starting Services

**Before (caused error)**:
```bash
python src/api/chatbot_api.py  # ❌ ModuleNotFoundError
```

**After (works correctly)**:
```bash
./run_chatbot.sh              # ✅ Works!
# OR
PYTHONPATH=. python src/api/chatbot_api.py  # ✅ Works!
```

### Running Demo Scripts

Most demo scripts at the root level should work fine:
```bash
python demo_test_queries.py           # ✅ Works
python quick_system_validation.py     # ✅ Works
python validate_end_to_end_system.py  # ✅ Works
```

But if you encounter import errors, use:
```bash
PYTHONPATH=. python script_name.py
```

## Verification

Test that imports work:
```bash
# Test import
PYTHONPATH=. python -c "from src.config.settings import Settings; print('Success!')"

# Should output: Success!
```

## Quick Reference

### Start Chatbot API
```bash
./run_chatbot.sh
```

### Start ML API
```bash
./run_ml_api.sh
```

### Run Any Script with Proper Path
```bash
PYTHONPATH=. python path/to/script.py
```

### Check if Service is Running
```bash
curl http://localhost:8000/health
```

## Additional Resources

- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Complete troubleshooting guide
- **[DEMO_README.md](DEMO_README.md)** - Demo execution guide
- **[docs/guides/DEMO_EXECUTION_GUIDE.md](docs/guides/DEMO_EXECUTION_GUIDE.md)** - Detailed demo instructions

---

**Issue Resolved**: ✅  
**Date**: November 13, 2025
