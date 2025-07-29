import os
import secrets
import asyncio
import logging
import sys
from dotenv import load_dotenv
from api_solver import create_app

# Load environment variables from .env file
load_dotenv()

# Generate secure API key if not provided


def generate_api_key():
    return secrets.token_urlsafe(32)

# Production configuration


class ProductionConfig:
    def __init__(self):
        self.api_key = os.getenv('TURNSTILE_API_KEY') or generate_api_key()
        self.host = os.getenv('HOST', '0.0.0.0')
        self.port = int(os.getenv('PORT', 8000))
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        self.headless = os.getenv('HEADLESS', 'true').lower() == 'true'
        self.browser_type = os.getenv('BROWSER_TYPE', 'chromium')
        self.threads = int(os.getenv('THREADS', 2))
        self.useragent = os.getenv('USER_AGENT')

        # Security settings
        self.workers = int(os.getenv('WORKERS', 1))
        self.max_connections = int(os.getenv('MAX_CONNECTIONS', 100))

        # Log the API key on first run for manual setup
        if not os.getenv('TURNSTILE_API_KEY'):
            print(f"🔑 Generated API Key: {self.api_key}")
            print(
                "⚠️  Save this key! Set TURNSTILE_API_KEY environment variable for future runs.")


async def run_production_server():
    """Run the production server with optimized settings."""
    config = ProductionConfig()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO if not config.debug else logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("TurnstileProduction")

    logger.info(f"🚀 Starting Turnstile API in production mode")
    logger.info(
        f"🌐 Server will be available at http://{config.host}:{config.port}")
    logger.info(
        f"🔒 API Authentication: {'Enabled' if config.api_key else 'Disabled'}")
    logger.info(f"🧠 Browser threads: {config.threads}")
    logger.info(f"👻 Headless mode: {config.headless}")

    try:
        app = create_app(
            debug=config.debug,
            headless=config.headless,
            useragent=config.useragent,
            browser_type=config.browser_type,
            thread=config.threads,
            proxy_support=True,
            api_key=config.api_key
        )

        # Use Hypercorn for production ASGI serving
        import hypercorn.asyncio
        from hypercorn import Config

        server_config = Config()
        server_config.bind = [f"{config.host}:{config.port}"]
        server_config.workers = config.workers
        server_config.max_incomplete_streams = config.max_connections

        # Note: Security headers can be added at reverse proxy level (nginx)

        await hypercorn.asyncio.serve(app, server_config)

    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_production_server())
