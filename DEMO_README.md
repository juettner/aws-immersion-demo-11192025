# Demo Materials - Quick Reference

This document provides quick access to all demo-related materials for the Concert Data Platform.

## 📋 Demo Documentation

### Main Guides
- **[Demo Execution Guide](docs/guides/DEMO_EXECUTION_GUIDE.md)** - Complete step-by-step instructions for running demos
- **[Demo Scenarios](docs/guides/DEMO_SCENARIOS.md)** - 13 comprehensive demo scenarios with scripts and expected outputs
- **[Demo Pipeline Guide](docs/guides/DEMO_PIPELINE_GUIDE.md)** - Guide for running the complete data pipeline

### Implementation Summaries
- **[Task 8.2 Completion](docs/features/TASK_8.2_COMPLETION.md)** - Demo pipeline implementation summary
- **[Task 8.3 Completion](docs/features/TASK_8.3_COMPLETION.md)** - Demo scenarios and validation summary

## 🛠️ Demo Scripts

### Validation Scripts
```bash
# Quick system health check (no services required)
python quick_system_validation.py

# Full end-to-end validation (requires services running)
python validate_end_to_end_system.py

# Demo pipeline validation
python validate_demo_pipeline.py
```

### Demo Execution Scripts
```bash
# Interactive demo query runner
python demo_test_queries.py

# Generate synthetic demo data
python generate_synthetic_data.py --num-artists 1000 --num-venues 500 --num-concerts 10000

# Run complete demo pipeline
./run_complete_demo.sh

# Train ML models with demo data
python train_demo_models.py
```

## 🎬 Quick Demo Flow

### 1. Prepare Environment
```bash
# Verify system readiness
python quick_system_validation.py

# Generate demo data
python generate_synthetic_data.py --num-artists 1000 --num-venues 500 --num-concerts 10000 --upload-to-s3

# Run data pipeline
./run_complete_demo.sh

# Train ML models
python train_demo_models.py
```

### 2. Start Services
```bash
# Start chatbot API
python src/api/chatbot_api.py &

# Start web interface
cd web && npm run dev &
```

### 3. Run Demo Scenarios
```bash
# Interactive demo runner
python demo_test_queries.py

# Or follow manual scenarios in:
# docs/guides/DEMO_SCENARIOS.md
```

### 4. Validate System
```bash
# Run end-to-end validation
python validate_end_to_end_system.py

# View validation report
cat validation_report_*.json
```

## 📊 Demo Scenarios Overview

### Chatbot Scenarios (6 scenarios)
1. Artist Lookup and Information
2. Venue Search and Recommendations
3. Concert Recommendations
4. Data Analysis and Visualization
5. External Data Enrichment
6. Conversation Memory

### Dashboard Scenarios (3 scenarios)
7. Venue Popularity Dashboard
8. Ticket Sales Predictions Dashboard
9. Artist Popularity Trends

### ML Model Scenarios (3 scenarios)
10. Venue Popularity Prediction
11. Ticket Sales Prediction
12. Concert Recommendations

### Data Pipeline Scenarios (2 scenarios)
13. Real-Time Data Ingestion
14. ETL Pipeline Execution

## 🎯 Demo Timing Options

### Quick Demo (30 minutes)
- Data generation and pipeline (10 min)
- ML model predictions (5 min)
- Chatbot demonstration (10 min)
- Dashboard walkthrough (5 min)

### Standard Demo (65 minutes)
- All phases from Demo Execution Guide
- Includes infrastructure and monitoring
- Q&A time included

### Technical Deep Dive (90 minutes)
- Complete demo with code walkthrough
- Architecture discussion
- Deployment demonstration
- Extended Q&A

## 📝 Pre-Demo Checklist

- [ ] Run `python quick_system_validation.py`
- [ ] Generate synthetic data
- [ ] Execute data pipeline
- [ ] Train ML models
- [ ] Start chatbot service
- [ ] Start web interface
- [ ] Test key scenarios
- [ ] Prepare backup screenshots

## 🔧 Troubleshooting

### Chatbot not responding
```bash
# Check service status
curl http://localhost:8000/health

# Restart service
pkill -f chatbot_api.py
python src/api/chatbot_api.py &
```

### No data in Redshift
```bash
# Verify Redshift connectivity
python validate_redshift_implementation.py

# Re-run pipeline
./run_complete_demo.sh
```

### ML predictions failing
```bash
# Verify models are trained
ls -la models/

# Retrain models
python train_demo_models.py
```

### Web interface not loading
```bash
# Check if port is in use
lsof -i :5173

# Rebuild and restart
cd web
npm run build
npm run dev
```

## 📚 Additional Resources

- **[Main README](README.md)** - Project overview and architecture
- **[Quick Start Guide](QUICKSTART.md)** - Get started in 15 minutes
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment
- **[Documentation Index](docs/DOCUMENTATION_INDEX.md)** - Complete documentation catalog

## 🎓 Demo Best Practices

1. **Always run validation before demos** - Use `quick_system_validation.py`
2. **Have backup data ready** - Pre-generate data in case of issues
3. **Test all scenarios beforehand** - Run through at least once
4. **Prepare for questions** - Review architecture and design docs
5. **Have AWS console open** - Show infrastructure in real-time
6. **Keep timing flexible** - Adjust based on audience interest
7. **Focus on business value** - Technical details as needed

---

**For detailed instructions, see [Demo Execution Guide](docs/guides/DEMO_EXECUTION_GUIDE.md)**
