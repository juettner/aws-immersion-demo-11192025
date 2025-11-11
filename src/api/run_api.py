"""
Startup script for Concert AI Chatbot API.

This script properly configures the Python path and starts the FastAPI server.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "src.api.chatbot_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
