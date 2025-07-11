import uvicorn
import os
import signal
import sys

if __name__ == "__main__":
    # Get port from environment variable (Google Cloud Run requirement)
    port = int(os.environ.get("PORT", 8080))

    def handle_sigint(sig, frame):
        print("\nReceived Ctrl+C, shutting down gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    # Bind to 0.0.0.0 for production deployment
    uvicorn.run(
        # "app.main:app",
        "app.main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=False  # Disable reload in production
    ) 