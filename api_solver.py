import os
import sys
import time
import uuid
import json
import random
import logging
import asyncio
import argparse
from functools import wraps
from quart import Quart, request, jsonify
# from camoufox.async_api import AsyncCamoufox
from patchright.async_api import async_playwright
from urllib.parse import urlparse

COLORS = {
    'MAGENTA': '\033[35m',
    'BLUE': '\033[34m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'RED': '\033[31m',
    'RESET': '\033[0m',
}


class CustomLogger(logging.Logger):
    @staticmethod
    def format_message(level, color, message):
        timestamp = time.strftime('%H:%M:%S')
        return f"[{timestamp}] [{COLORS.get(color)}{level}{COLORS.get('RESET')}] -> {message}"

    def debug(self, message, *args, **kwargs):
        super().debug(self.format_message('DEBUG', 'MAGENTA', message), *args, **kwargs)

    def info(self, message, *args, **kwargs):
        super().info(self.format_message('INFO', 'BLUE', message), *args, **kwargs)

    def success(self, message, *args, **kwargs):
        super().info(self.format_message('SUCCESS', 'GREEN', message), *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        super().warning(self.format_message('WARNING', 'YELLOW', message), *args, **kwargs)

    def error(self, message, *args, **kwargs):
        super().error(self.format_message('ERROR', 'RED', message), *args, **kwargs)


logging.setLoggerClass(CustomLogger)
logger = logging.getLogger("TurnstileAPIServer")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


class TurnstileAPIServer:
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Turnstile Solver</title>
        <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async></script>
        <script>
            async function fetchIP() {
                try {
                    const response = await fetch('https://api64.ipify.org?format=json');
                    const data = await response.json();
                    document.getElementById('ip-display').innerText = `Your IP: ${data.ip}`;
                } catch (error) {
                    console.error('Error fetching IP:', error);
                    document.getElementById(
                        'ip-display').innerText = 'Failed to fetch IP';
                }
            }
            window.onload = fetchIP;
        </script>
    </head>
    <body>
        <!-- cf turnstile -->
        <p id="ip-display">Fetching your IP...</p>
    </body>
    </html>
    """

    def __init__(self, headless: bool, useragent: str, debug: bool, browser_type: str, thread: int, proxy_support: bool, api_key: str = None):
        self.app = Quart(__name__)
        self.debug = debug
        self.results = self._load_results()
        self.browser_type = browser_type
        self.headless = headless
        self.useragent = useragent
        self.thread_count = thread
        self.proxy_support = proxy_support
        self.api_key = api_key
        self.browser_pool = asyncio.Queue()
        self.browser_args = []
        if useragent:
            self.browser_args.append(f"--user-agent={useragent}")

        self._setup_routes()

    def require_api_key(self, f):
        """Decorator to require API key authentication."""
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            if not self.api_key:
                # If no API key is configured, allow all requests
                return await f(*args, **kwargs)

            api_key = request.headers.get('x-api-key')

            if not api_key:
                logger.warning("Request blocked: Missing x-api-key header")
                return jsonify({
                    "status": "error",
                    "error": "Missing x-api-key header"
                }), 401

            if api_key != self.api_key:
                logger.warning(
                    f"Request blocked: Invalid API key provided: {api_key[:10]}...")
                return jsonify({
                    "status": "error",
                    "error": "Invalid API key"
                }), 401

            logger.debug("API key validation successful")
            return await f(*args, **kwargs)
        return decorated_function

    @staticmethod
    def _load_results():
        """Load previous results from results.json."""
        try:
            if os.path.exists("results.json"):
                with open("results.json", "r") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(
                f"Error loading results: {str(e)}. Starting with an empty results dictionary.")
        return {}

    def _save_results(self):
        """Save results to results.json."""
        try:
            with open("results.json", "w") as result_file:
                json.dump(self.results, result_file, indent=4)
        except IOError as e:
            logger.error(f"Error saving results to file: {str(e)}")

    def _setup_routes(self) -> None:
        """Set up the application routes."""
        self.app.before_serving(self._startup)
        self.app.route(
            '/turnstile', methods=['GET'])(self.require_api_key(self.process_turnstile))
        self.app.route('/result', methods=['GET']
                       )(self.require_api_key(self.get_result))
        self.app.route('/')(self.index)

    async def _startup(self) -> None:
        """Initialize the browser and page pool on startup."""
        logger.info("Starting browser initialization")
        try:
            await self._initialize_browser()
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise

    async def _initialize_browser(self) -> None:
        """Initialize the browser and create the page pool."""

        if self.browser_type in ['chromium', 'chrome', 'msedge']:
            playwright = await async_playwright().start()
        # elif self.browser_type == "camoufox":
        #     camoufox = AsyncCamoufox(headless=self.headless)

        for _ in range(self.thread_count):
            if self.browser_type in ['chromium', 'chrome', 'msedge']:
                browser = await playwright.chromium.launch(
                    channel=self.browser_type,
                    headless=self.headless,
                    args=self.browser_args,
                )

            # elif self.browser_type == "camoufox":
            #     browser = await camoufox.start()

            await self.browser_pool.put((_+1, browser))

            if self.debug:
                logger.success(f"Browser {_ + 1} initialized successfully")

        logger.success(
            f"Browser pool initialized with {self.browser_pool.qsize()} browsers")

    async def _solve_turnstile(self, task_id: str, url: str, sitekey: str, action: str = None, cdata: str = None, proxy: str = None):
        """Solve the Turnstile challenge."""

        index, browser = await self.browser_pool.get()

        parsed = urlparse(proxy)

        logger.debug(f"Proxy: {proxy}")
        logger.debug(f"Parsed: {parsed}")
        logger.debug(f"url: {url}")
        logger.debug(f"sitekey: {sitekey}")

        username = parsed.username
        password = parsed.password
        ip = parsed.hostname
        port = parsed.port

        parsed_proxy = {
            "server": f"{ip}:{port}",
            "username": username,
            "password": password
        }

        context = await browser.new_context(proxy=parsed_proxy)

        page = await context.new_page()

        start_time = time.time()

        try:
            if self.debug:
                logger.debug(
                    f"Browser {index}: Starting Turnstile solve for URL: {url} with Sitekey: {sitekey} | Proxy: {proxy}")
                logger.debug(
                    f"Browser {index}: Setting up page data and route")

            url_with_slash = url + "/" if not url.endswith("/") else url
            turnstile_div = f'<div class="cf-turnstile" style="background: white;" data-sitekey="{sitekey}"' + (
                f' data-action="{action}"' if action else '') + (f' data-cdata="{cdata}"' if cdata else '') + '></div>'
            page_data = self.HTML_TEMPLATE.replace(
                "<!-- cf turnstile -->", turnstile_div)

            await page.route(url_with_slash, lambda route: route.fulfill(body=page_data, status=200))
            await page.goto(url_with_slash)

            if self.debug:
                logger.debug(
                    f"Browser {index}: Setting up Turnstile widget dimensions")

            await page.eval_on_selector("//div[@class='cf-turnstile']", "el => el.style.width = '70px'")

            if self.debug:
                logger.debug(
                    f"Browser {index}: Starting Turnstile response retrieval loop")

            for _ in range(40):
                try:
                    turnstile_check = await page.input_value("[name=cf-turnstile-response]", timeout=2000)
                    # Get cookies from the page context
                    cookies = await page.context.cookies()

                    if turnstile_check == "":
                        if self.debug:
                            logger.debug(
                                f"Browser {index}: Attempt {_} - No Turnstile response yet")

                        await page.locator("//div[@class='cf-turnstile']").click(timeout=1000)
                        await asyncio.sleep(0.5)
                    else:
                        elapsed_time = round(time.time() - start_time, 3)

                        logger.success(
                            f"Browser {index}: Successfully solved captcha - {COLORS.get('MAGENTA')}{turnstile_check[:10]}{COLORS.get('RESET')} in {COLORS.get('GREEN')}{elapsed_time}{COLORS.get('RESET')} Seconds")

                        user_agent = await page.evaluate("navigator.userAgent")

                        self.results[task_id] = {
                            "value": turnstile_check, "elapsed_time": elapsed_time, "cookies": cookies, "user_agent": user_agent}
                        self._save_results()
                        break
                except:
                    pass

            if self.results.get(task_id) == "CAPTCHA_NOT_READY":
                elapsed_time = round(time.time() - start_time, 3)
                self.results[task_id] = {
                    "value": "CAPTCHA_FAIL", "elapsed_time": elapsed_time}
                if self.debug:
                    logger.error(
                        f"Browser {index}: Error solving Turnstile in {COLORS.get('RED')}{elapsed_time}{COLORS.get('RESET')} Seconds")
        except Exception as e:
            elapsed_time = round(time.time() - start_time, 3)
            self.results[task_id] = {
                "value": "CAPTCHA_FAIL", "elapsed_time": elapsed_time}
            if self.debug:
                logger.error(
                    f"Browser {index}: Error solving Turnstile: {str(e)}")
        finally:
            if self.debug:
                logger.debug(f"Browser {index}: Clearing page state")

            await context.close()
            await self.browser_pool.put((index, browser))

    async def process_turnstile(self):
        """Handle the /turnstile endpoint requests."""
        url = request.args.get('url')
        sitekey = request.args.get('sitekey')
        action = request.args.get('action')
        cdata = request.args.get('cdata')
        proxy = request.args.get('proxy')

        if not url or not sitekey:
            return jsonify({
                "status": "error",
                "error": "Both 'url' and 'sitekey' are required"
            }), 400

        task_id = str(uuid.uuid4())
        self.results[task_id] = "CAPTCHA_NOT_READY"

        try:
            asyncio.create_task(self._solve_turnstile(
                task_id=task_id, url=url, sitekey=sitekey, action=action, cdata=cdata, proxy=proxy))

            if self.debug:
                logger.debug(f"Request completed with taskid {task_id}.")
            return jsonify({"task_id": task_id}), 202
        except Exception as e:
            logger.error(f"Unexpected error processing request: {str(e)}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    async def get_result(self):
        """Return solved data"""
        task_id = request.args.get('id')

        if not task_id or task_id not in self.results:
            return jsonify({"status": "error", "error": "Invalid task ID/Request parameter"}), 400

        result = self.results[task_id]
        status_code = 200

        if "CAPTCHA_FAIL" in result:
            status_code = 422

        return result, status_code

    @staticmethod
    async def index():
        """Serve the API documentation page."""
        return """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Turnstile Solver API</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-900 text-gray-200 min-h-screen flex items-center justify-center">
                <div class="text-center">
                <h1 class="text-3xl font-bold mb-6 text-center text-red-500">KRALLAR ICIN</h1>
                </div>
            </body>
            </html>
        """


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Turnstile API Server")

    parser.add_argument('--headless', type=bool, default=False,
                        help='Run the browser in headless mode, without opening a graphical interface. This option requires the --useragent argument to be set (default: False)')
    parser.add_argument('--useragent', type=str, default=None,
                        help='Specify a custom User-Agent string for the browser. If not provided, the default User-Agent is used')
    parser.add_argument('--debug', type=bool, default=False,
                        help='Enable or disable debug mode for additional logging and troubleshooting information (default: False)')
    parser.add_argument('--browser_type', type=str, default='chromium',
                        help='Specify the browser type for the solver. Supported options: chromium, chrome, msedge, camoufox (default: chromium)')
    parser.add_argument('--thread', type=int, default=1,
                        help='Set the number of browser threads to use for multi-threaded mode. Increasing this will speed up execution but requires more resources (default: 1)')
    parser.add_argument('--proxy', type=bool, default=False,
                        help='Enable proxy support for the solver (Default: False)')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Specify the IP address where the API solver runs. Use 0.0.0.0 for public access (Default: 0.0.0.0)')
    parser.add_argument('--port', type=str, default='5000',
                        help='Set the port for the API solver to listen on. (Default: 5000)')
    parser.add_argument('--api-key', type=str, default=None,
                        help='Set an API key for authentication. If not provided, API key validation is disabled (Default: None)')
    return parser.parse_args()


def create_app(headless: bool, useragent: str, debug: bool, browser_type: str, thread: int, proxy_support: bool, api_key: str = None) -> Quart:
    server = TurnstileAPIServer(headless=headless, useragent=useragent, debug=debug,
                                browser_type=browser_type, thread=thread, proxy_support=proxy_support, api_key=api_key)
    return server.app


if __name__ == '__main__':
    args = parse_args()
    browser_types = [
        'chromium',
        'chrome',
        'msedge',
        # 'camoufox',
    ]
    if args.browser_type not in browser_types:
        logger.error(
            f"Unknown browser type: {COLORS.get('RED')}{args.browser_type}{COLORS.get('RESET')} Available browser types: {browser_types}")
    # elif args.headless is True and args.useragent is None and "camoufox" not in args.browser_type:
    #     logger.error(f"You must specify a {COLORS.get('YELLOW')}User-Agent{COLORS.get('RESET')} for Turnstile Solver or use {COLORS.get('GREEN')}camoufox{COLORS.get('RESET')} without useragent")
    else:
        # Access the api_key attribute (argparse converts --api-key to api_key)
        api_key = getattr(args, 'api_key', None)
        if api_key:
            logger.info(
                f"API key authentication {COLORS.get('GREEN')}enabled{COLORS.get('RESET')}")
        else:
            logger.warning(
                f"API key authentication {COLORS.get('YELLOW')}disabled{COLORS.get('RESET')} - all requests will be allowed")

        app = create_app(headless=args.headless, debug=args.debug, useragent=args.useragent,
                         browser_type=args.browser_type, thread=args.thread, proxy_support=args.proxy,
                         api_key=api_key)
        app.run(host=args.host, port=int(args.port))
