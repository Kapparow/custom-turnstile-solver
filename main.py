from api_solver import create_app
import asyncio
import logging
import time
import sys


class CustomLogger(logging.Logger):
    COLORS = {
        'DEBUG': '\033[35m',    # Magenta
        'INFO': '\033[34m',     # Blue
        'SUCCESS': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
    }
    RESET = '\033[0m'  # Reset color

    def format_message(self, level, message):
        timestamp = time.strftime('%H:%M:%S')
        return f"[{timestamp}] [{self.COLORS.get(level, '')}{level}{self.RESET}] -> {message}"

    def debug(self, message, *args, **kwargs):
        super().debug(self.format_message('DEBUG', message), *args, **kwargs)

    def info(self, message, *args, **kwargs):
        super().info(self.format_message('INFO', message), *args, **kwargs)

    def success(self, message, *args, **kwargs):
        super().info(self.format_message('SUCCESS', message), *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        super().warning(self.format_message('WARNING', message), *args, **kwargs)

    def error(self, message, *args, **kwargs):
        super().error(self.format_message('ERROR', message), *args, **kwargs)


logging.setLoggerClass(CustomLogger)
logger = logging.getLogger("TurnstileTester")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


async def main():
    """Run the API server with logging."""
    logger.info("Starting API server on http://localhost:3003")
    logger.info("API documentation available at http://localhost:3003/")

    try:
        app = create_app(debug=False, headless=True,
                         useragent=None, browser_type="chromium", thread=4, proxy_support=True, api_key="your-secure-api-key-here")
        import hypercorn.asyncio
        config = hypercorn.Config()
        config.bind = ["0.0.0.0:3003"]
        await hypercorn.asyncio.serve(app, config)
    except Exception as e:
        logger.error(f"API server failed to start: {str(e)}")
        raise e


if __name__ == "__main__":
    asyncio.run(main())
