# API Ingestion Documentation

Documentation for external API integration and data ingestion from Spotify and Ticketmaster.

## 📄 Documents

### Quick Start
- **[Production Ingestion Fixed](PRODUCTION_INGESTION_FIXED.md)** ⭐ **START HERE**
  - Working implementation guide
  - Test results and verification
  - How to run the pipeline
  - Troubleshooting tips

- **[Run Ingestion README](RUN_INGESTION_README.md)**
  - Quick start guide
  - Alternative methods
  - Common issues

### Comprehensive Guides
- **[Production Ingestion Guide](PRODUCTION_INGESTION_GUIDE.md)**
  - Complete production setup
  - AWS integration details
  - Lambda deployment
  - Monitoring and logging

- **[API Connectors Summary](API_CONNECTORS_SUMMARY.md)**
  - Implementation overview
  - Architecture details
  - API client features
  - Cost estimates

## 🚀 Quick Start

```bash
# Run the production ingestion pipeline
python -m src.services.external_apis.production_ingestion
```

**Expected Results:**
- ✅ Fetches data from Spotify and Ticketmaster
- ✅ Saves to S3: `s3://concert-data-raw/`
- ✅ Streams to Kinesis: `concert-data-stream`
- ✅ Logs comprehensive metrics

## 📊 What Gets Ingested

### From Spotify
- Artist names and IDs
- Genres and popularity scores
- Follower counts
- Related artists

### From Ticketmaster
- Venue information (name, location, capacity)
- Event details (date, time, prices)
- Ticket price ranges
- Event classifications

## 🔗 Related Documentation

- [Kinesis Setup](../kinesis/KINESIS_QUICKSTART.md) - Configure streaming
- [Main Documentation](../README.md) - Full documentation index
- [Infrastructure](../../infrastructure/) - Setup scripts

## 💡 Key Features

- **Rate Limiting**: Prevents API abuse
- **Retry Logic**: Handles transient failures
- **Data Transformation**: Normalizes to internal format
- **Dual Persistence**: S3 (batch) + Kinesis (streaming)
- **Error Handling**: Comprehensive logging
- **Production Ready**: Tested and verified

## 📈 Success Metrics

Latest test run:
- ✅ 150 artists from Spotify
- ✅ 194 venues from Ticketmaster
- ✅ 125 events from Ticketmaster
- ✅ 469 total records persisted
- ✅ 0 errors

---

[← Back to Main Documentation](../README.md)