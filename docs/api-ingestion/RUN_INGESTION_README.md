# How to Run the Data Ingestion Pipeline

## ✅ Working Method (Recommended)

Use the demo script which properly loads environment variables:

```bash
python demo_production_flow.py
```

This script:
- ✅ Loads environment variables correctly
- ✅ Fetches real data from Spotify and Ticketmaster
- ✅ Shows where data would be persisted (S3 and Kinesis)
- ✅ Displays complete record structures

## Output Example

```
================================================================================
PRODUCTION DATA FLOW DEMONSTRATION
================================================================================

Configuration:
  Spotify Client ID: 53981a6ec0...
  Ticketmaster API Key: yKLtxfFZ7k...
  S3 Bucket: concert-data-raw
  Kinesis Stream: concert-data-stream

--------------------------------------------------------------------------------
DEMO 1: Spotify Artist Data Ingestion
--------------------------------------------------------------------------------

1. Fetching artist data from Spotify API...
   ✓ Successfully fetched 3 artists

2. Sample Artist Data:
   Name: Radiohead
   ID: spotify_4Z8W4fKeB5YxbusRsdQVPb
   Genres: alternative rock, art rock
   Popularity: 85.0

3. Data Persistence:
   → S3 Location: s3://concert-data-raw/raw/spotify/artists/year=2025/month=11/day=09/...
   → Kinesis Stream: concert-data-stream
   → Partition Key: spotify_4Z8W4fKeB5YxbusRsdQVPb

4. Downstream Processing:
   → AWS Glue would process the S3 data
   → Lambda would process Kinesis stream in real-time
   → Redshift would store for analytics
```

## Alternative: Direct API Client Usage

You can also use the API clients directly:

```python
import asyncio
import os
from src.config.environment import load_env_file
load_env_file()

from src.services.external_apis.spotify_client import SpotifyClient
from src.services.external_apis.ticketmaster_client import TicketmasterClient

async def main():
    # Spotify example
    async with SpotifyClient(
        client_id=os.getenv('API_SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('API_SPOTIFY_CLIENT_SECRET')
    ) as spotify:
        response = await spotify.search_artists("rock", limit=10)
        if response.success:
            artists = response.data.get("normalized_artists", [])
            for artist in artists:
                print(f"{artist['name']} - {artist['popularity_score']}")
    
    # Ticketmaster example
    async with TicketmasterClient(
        api_key=os.getenv('API_TICKETMASTER_API_KEY')
    ) as tm:
        response = await tm.search_venues(city="New York", size=10)
        if response.success:
            venues = response.data.get("normalized_venues", [])
            for venue in venues:
                print(f"{venue['name']} - Capacity: {venue['capacity']}")

asyncio.run(main())
```

## What Gets Fetched

### From Spotify
- Artist names
- Genres
- Popularity scores
- Follower counts
- Spotify IDs

### From Ticketmaster
- Venue names and locations
- Venue capacities
- Event dates and times
- Ticket price ranges
- Event classifications

## Data Flow

```
External APIs
     ↓
API Clients (with rate limiting & retry logic)
     ↓
Data Transformation (normalize to internal format)
     ↓
┌────────────┬────────────┐
│            │            │
S3           Kinesis      (shown in demo)
(Raw Data)   (Stream)
│            │
↓            ↓
AWS Glue     Lambda       (next steps)
│            │
└────┬───────┘
     ↓
  Redshift
```

## Troubleshooting

### Issue: "Spotify credentials not configured"

**Solution**: Make sure your `.env` file has:
```bash
API_SPOTIFY_CLIENT_ID=your_client_id
API_SPOTIFY_CLIENT_SECRET=your_client_secret
```

### Issue: "Ticketmaster API key not configured"

**Solution**: Make sure your `.env` file has:
```bash
API_TICKETMASTER_API_KEY=your_api_key
```

### Issue: Module import errors

**Solution**: Run from the project root directory:
```bash
cd /path/to/aws-immersion-demo-11192025
python demo_production_flow.py
```

## Next Steps

1. ✅ Run the demo to see data fetching in action
2. ⬜ Set up actual S3 buckets (if not already done)
3. ⬜ Verify Kinesis stream is active
4. ⬜ Set up Lambda consumers for real-time processing
5. ⬜ Configure AWS Glue for batch ETL
6. ⬜ Load processed data into Redshift

## Files

- **`demo_production_flow.py`** - Working demo script ✅
- **`src/services/external_apis/spotify_client.py`** - Spotify API client
- **`src/services/external_apis/ticketmaster_client.py`** - Ticketmaster API client
- **`src/services/external_apis/ingestion_service.py`** - Orchestration service
- **`src/services/external_apis/production_ingestion.py`** - Production pipeline (has env loading issue)

## Cost

Running the demo script is essentially free:
- API calls are within free tiers
- No AWS resources are actually written to (demo mode)
- Rate limiting prevents excessive API usage

When you enable actual S3/Kinesis writes:
- S3: ~$0.023/GB
- Kinesis: ~$11/month for 1 shard
- API calls: Free within limits

## Support

For issues:
1. Check `.env` file has correct credentials
2. Verify you're in the project root directory
3. Check API credentials are valid
4. Review `API_CONNECTORS_SUMMARY.md` for details