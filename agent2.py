import os
import asyncio
import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime, timedelta
# Assuming browser_use provides these correctly
# (If using playwright directly, imports would differ)
from browser_use import (
    Agent,
    Browser,
    BrowserConfig,
    Controller,
    ActionResult, # Assuming this exists for type hinting if needed
    BrowserContextConfig
)
# Import Playwright types for hinting if available
try:
    from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
except ImportError:
    # Define dummy types if playwright isn't installed locally for type checking
    Page = object
    PlaywrightTimeoutError = Exception

from typing import Dict, List, Optional, Any, Tuple

# --- Configuration ---
load_dotenv()

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

# User Configuration (Consider loading from a file or args for more flexibility)
USER_CONFIG = {
    "flight_date": "15/07/2025",
    "initial_destination": "London",
    "final_destination": "Paris",
    "return_date": "22/07/2025"
}
DATE_FORMAT = '%d/%m/%Y'
MAX_CALENDAR_NAVIGATION_ATTEMPTS = 12
DEFAULT_TIMEOUT = 15000 # ms

# --- Data Structure ---

class TravelData:
    """Holds the collected travel information."""
    def __init__(self):
        self.flight_data: Optional[Dict[str, Any]] = None
        self.accommodation_data: Optional[Dict[str, Any]] = None
        self.activities_data: Optional[Dict[str, Any]] = None
        self.itinerary: Optional[str] = None # Itinerary might be text

    def __str__(self):
        return (
            f"TravelData(\n"
            f"  Flight: {self.flight_data}\n"
            f"  Accommodation: {self.accommodation_data}\n"
            f"  Activities: {self.activities_data}\n"
            f"  Itinerary: {'Generated' if self.itinerary else 'Not Generated'}\n"
            f")"
        )

# --- Browser and LLM Initialization ---

def initialize_llm() -> ChatGoogleGenerativeAI:
    """Initializes the Google Generative AI LLM."""
    logger.info("Initializing LLM...")
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-pro", # Using gemini-pro as 1.5 flash might have diff capabilities
            google_api_key=GEMINI_API_KEY, # Correct parameter name
            max_retries=3,
            # max_tokens=1024, # Consider if needed, depends on Gemini Pro defaults/limits
            temperature=0.5,
            # request_timeout=timedelta(seconds=60) # Add timeout if needed
        )
        # Note: _verify_llm_connection is internal, rely on first call or add explicit check
        logger.info("LLM Initialized.")
        return llm
    except Exception as e:
        logger.exception("Failed to initialize LLM.")
        raise

def initialize_browser() -> Tuple[Browser, Controller]:
    """Initializes the Browser and Controller."""
    logger.info("Initializing Browser...")
    # Note: user_agent_mode="random" might be overridden by specific user_agent below.
    # If random is desired, remove the user_agent line in BrowserContextConfig.
    config = BrowserConfig(
        headless=False, # Keep visible for debugging, set True for production
        disable_security=False,
        deterministic_rendering=False,
        user_agent_mode="random", # Set to 'none' if providing a specific user_agent
        new_context_config=BrowserContextConfig(
            viewport={'width': 1440, 'height': 900},
            device_scale_factor=1,
            is_mobile=False,
            # Specific User Agent - remove if user_agent_mode="random" is intended
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            java_script_enabled=True,
            has_touch=False,
            color_scheme='light',
            reduced_motion='no-preference',
            forced_colors='none',
        )
    )
    browser = Browser(config=config)
    controller = Controller()
    logger.info("Browser and Controller Initialized.")
    return browser, controller

# --- Custom Browser Actions ---

@controller.action('Select date in calendar')
async def select_date_in_calendar(data: Dict[str, str], browser: Browser, page: Optional[Page] = None) -> Dict[str, str]:
    """
    Selects a date in a generic calendar widget.

    Requires the following keys in the `data` dictionary:
    - 'date': The date to select (format DD/MM/YYYY).
    - 'calendar_selector': CSS selector for the main calendar container.
    - 'date_button_selector': CSS selector for the button that initially opens the date picker (if applicable).
    - 'next_month_selector': CSS selector for the 'next month' button.
    - 'done_button_selector': Optional CSS selector for a 'Done' or 'Confirm' button after selection.
    - 'date_aria_label_format': Optional strftime format for the aria-label (defaults to "%A, %d %B %Y").
    - 'month_year_format': Optional strftime format for matching the target month/year (defaults to "%B %Y").
    """
    close_page_on_exit = False
    current_page = page

    try:
        target_date_str = data['date']
        calendar_selector = data['calendar_selector']
        date_button_selector = data['date_button_selector']
        next_month_selector = data['next_month_selector']
        done_button_selector = data.get('done_button_selector')
        date_aria_label_format = data.get('date_aria_label_format', "%A, %d %B %Y")
        month_year_format = data.get('month_year_format', "%B %Y")

        if current_page is None:
            logger.info("No page provided, creating a new one for date selection.")
            current_page = await browser.new_page()
            if current_page is None: # Ensure page creation worked
                 raise RuntimeError("Failed to create a new browser page.")
            close_page_on_exit = True

        logger.info(f"Attempting to select date: {target_date_str}")

        # 1. Open the calendar if it's not already visible
        try:
             is_calendar_visible = await current_page.is_visible(calendar_selector, timeout=5000)
        except PlaywrightTimeoutError:
             is_calendar_visible = False

        if not is_calendar_visible:
            logger.info(f"Calendar '{calendar_selector}' not visible, clicking button '{date_button_selector}'")
            await current_page.click(date_button_selector, timeout=DEFAULT_TIMEOUT)
            await current_page.wait_for_selector(calendar_selector, state="visible", timeout=DEFAULT_TIMEOUT)
            logger.info("Calendar opened.")
        else:
            logger.info("Calendar already visible.")

        # 2. Navigate to the correct month
        target_date_obj = datetime.strptime(target_date_str, DATE_FORMAT)
        target_month_year_str = target_date_obj.strftime(month_year_format)
        target_date_label = target_date_obj.strftime(date_aria_label_format)
        date_selector = f'[aria-label="{target_date_label}"]' # Common pattern, adjust if needed

        logger.info(f"Target month/year: {target_month_year_str}, Target date label: {target_date_label}")

        for attempt in range(MAX_CALENDAR_NAVIGATION_ATTEMPTS):
            try:
                # Using JS evaluation might be more robust for complex text content
                # current_calendar_text = await current_page.inner_text(calendar_selector, timeout=5000)
                # Need to wait for potential async updates after clicking next
                await current_page.wait_for_timeout(500) # Small wait for render
                current_calendar_text = await current_page.locator(calendar_selector).text_content(timeout=5000)

                logger.debug(f"Calendar text (Attempt {attempt+1}): {current_calendar_text[:100]}...") # Log snippet

                if target_month_year_str in current_calendar_text:
                    logger.info(f"Correct month '{target_month_year_str}' found.")
                    # 3. Select the date
                    date_element = current_page.locator(date_selector)
                    if await date_element.is_visible(timeout=5000):
                        # Scroll into view might be necessary
                        await date_element.scroll_into_view_if_needed()
                        await date_element.click(timeout=DEFAULT_TIMEOUT)
                        logger.info(f"Clicked date element: {date_selector}")

                        # 4. Click Done button if specified
                        if done_button_selector:
                            await current_page.click(done_button_selector, timeout=DEFAULT_TIMEOUT)
                            logger.info(f"Clicked done button: {done_button_selector}")

                        return {"status": "success", "message": f"Date {target_date_str} selected successfully."}
                    else:
                        logger.warning(f"Date selector '{date_selector}' not found or visible in the correct month.")
                        # Check if it exists but is disabled (could be an issue)
                        is_disabled = await current_page.locator(date_selector).is_disabled(timeout=1000)
                        if is_disabled:
                             raise Exception(f"Date {target_date_label} found but is disabled.")
                        else:
                             raise Exception(f"Date {target_date_label} not found or not visible in the correct month.")

            except PlaywrightTimeoutError:
                logger.warning(f"Timeout waiting for calendar text or date element on attempt {attempt+1}.")
                # Optional: Add a small delay before retrying navigation
                await asyncio.sleep(0.5)
            except Exception as e:
                 # Catch potential errors during text check or element interaction
                 logger.error(f"Error checking month or finding date element: {e}")
                 # Decide if we should continue navigation or raise immediately
                 # For now, we continue to navigate month

            # 5. Navigate to the next month if not found
            logger.debug(f"Target month not found, clicking next month button: {next_month_selector}")
            try:
                next_button = current_page.locator(next_month_selector)
                if await next_button.is_enabled(timeout=DEFAULT_TIMEOUT):
                    await next_button.click()
                    # Wait for the calendar content to potentially update
                    await current_page.wait_for_timeout(1000) # Adjust timing as needed
                else:
                     raise Exception("Next month button is not enabled or found.")
            except PlaywrightTimeoutError:
                raise Exception(f"Timeout finding or clicking the next month button ('{next_month_selector}').") from None
            except Exception as nav_exc:
                 raise Exception(f"Could not navigate to the next month: {nav_exc}") from nav_exc


        # If loop finishes without success
        raise Exception(f"Could not find month {target_month_year_str} or date {target_date_label} after {MAX_CALENDAR_NAVIGATION_ATTEMPTS} attempts.")

    except PlaywrightTimeoutError as e:
        logger.error(f"Timeout error during date selection: {e}")
        return {"status": "error", "message": f"Timeout: {e}"}
    except ValueError as e:
        logger.error(f"Invalid date format provided: {data.get('date')} - {e}")
        return {"status": "error", "message": f"Invalid date format: {e}"}
    except KeyError as e:
        logger.error(f"Missing required key in data for date selection: {e}")
        return {"status": "error", "message": f"Missing required parameter: {e}"}
    except Exception as e:
        logger.exception("An unexpected error occurred during date selection.")
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
    finally:
        if close_page_on_exit and current_page:
            logger.info("Closing temporary page used for date selection.")
            await current_page.close()

# --- Agent Creation Functions ---

async def create_initial_navigation_agent(llm: ChatGoogleGenerativeAI, browser: Browser, controller: Controller, target_url: str):
    """Creates an agent to handle initial navigation and basic checks."""
    agent = Agent(
        task=(
            f"1. **Navigate & Load:** Navigate to `{target_url}`. Wait up to {DEFAULT_TIMEOUT / 1000} seconds for the page to load meaningfully."
            f"2. **Dismiss Popups:** Actively look for and try to dismiss common cookie/consent banners or initial popups that might block interaction."
            f"3. **Verify Core Elements:** Check if essential elements for the site's main function (e.g., flight search form fields like 'From', 'To', date inputs, search button for Skyscanner) are visible and seem interactive."
            f"4. **Handle Failure:** If navigation fails, the page doesn't load correctly, core elements are missing, or you detect an obvious CAPTCHA/block page (look for keywords like 'verify', 'human', 'security', 'CAPTCHA', 'Access Denied', 'Blocked'):"
            f"   - Report the specific issue encountered (e.g., 'Navigation timeout', 'CAPTCHA detected', 'Missing search form', 'Consent banner blocked interaction')."
            f"   - STOP execution and return a failure status."
            f"5. **Success:** If the core elements are present and the page seems ready for interaction, return a success status."
        ),
        llm=llm,
        browser=browser,
        controller=controller,
        # Output validation might be tricky here, focus on status reporting
        validate_output=False,
        enable_memory=False # Keep stateless for initial check
    )
    # await agent._verify_llm_connection() # Internal method, avoid if possible
    return agent

async def create_flight_agent(llm: ChatGoogleGenerativeAI, browser: Browser, controller: Controller, config: Dict):
    """Creates an agent to find flight details on Skyscanner."""
    # Define selectors here for clarity or pass them if they change often
    skyscanner_selectors = {
        "from_field": "input[aria-label='Departure airport']", # Example, verify actual selector
        "to_field": "input[aria-label='Destination airport']", # Example, verify actual selector
        "depart_date_button": "[data-testid='depart-fsc-datepicker-button']",
        "return_date_button": "[data-testid='return-fsc-datepicker-button']",
        "calendar": "[data-testid='datepicker-calendar']",
        "next_month": "[aria-label='Next month']", # Verify selector
        "done_button": "[data-testid='date-picker-done-button']",
        "search_button": "[data-testid='search-button']", # Example, verify actual selector
    }

    task = (
        f"You are on the Skyscanner flight search page. Perform the following actions precisely:"
        f"1. Ensure the 'Flights' tab is selected (click if necessary)."
        f"2. Locate the 'From' input field ('{skyscanner_selectors['from_field']}') and type '{config['initial_destination']}'. Wait briefly for the dropdown and select the first matching option precisely."
        f"3. Locate the 'To' input field ('{skyscanner_selectors['to_field']}') and type '{config['final_destination']}'. Wait briefly for the dropdown and select the first matching option precisely."
        f"4. Use the 'Select date in calendar' action with the following parameters to select the departure date '{config['flight_date']}':"
        f"   {{'date': '{config['flight_date']}', 'calendar_selector': '{skyscanner_selectors['calendar']}', 'date_button_selector': '{skyscanner_selectors['depart_date_button']}', 'next_month_selector': '{skyscanner_selectors['next_month']}', 'done_button_selector': '{skyscanner_selectors['done_button']}'}}"
        f"5. Use the 'Select date in calendar' action with the following parameters to select the return date '{config['return_date']}':"
        f"   {{'date': '{config['return_date']}', 'calendar_selector': '{skyscanner_selectors['calendar']}', 'date_button_selector': '{skyscanner_selectors['return_date_button']}', 'next_month_selector': '{skyscanner_selectors['next_month']}', 'done_button_selector': '{skyscanner_selectors['done_button']}'}}"
        f"6. Click the main flight search button ('{skyscanner_selectors['search_button']}')."
        f"7. Wait for the search results page to load completely."
        f"8. Analyze the results and identify the *cheapest* available round-trip flight option shown on the first page of results."
        f"9. Extract the following details for the cheapest option. If a detail isn't clearly visible, use 'N/A':"
        f"   - Price (e.g., '£150', include currency symbol if shown)"
        f"   - Airline(s) (list all if multiple)"
        f"   - Outbound Departure Time (e.g., '08:30')"
        f"   - Outbound Arrival Time (e.g., '10:00')"
        f"   - Return Departure Time (e.g., '18:00')"
        f"   - Return Arrival Time (e.g., '19:30')"
        f"10. Return the extracted information ONLY in the following JSON format:\n"
        f"```json\n"
        f"{{\n"
        f"    \"price\": \"<extracted_price>\",\n"
        f"    \"airline\": [\"<airline1>\", \"<airline2>\"],\n"
        f"    \"departure_time\": \"<outbound_departure>\",\n"
        f"    \"arrival_time\": \"<outbound_arrival>\",\n"
        f"    \"return_departure_time\": \"<return_departure>\",\n"
        f"    \"return_arrival_time\": \"<return_arrival>\",\n"
        f"    \"search_url\": \"<current_page_url>\"\n" # Capture URL after search
        f"}}\n"
        f"```"
    )

    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        controller=controller,
        validate_output=True, # Expecting JSON
        enable_memory=False # Usually better to keep flight search stateless
    )
    return agent

async def create_accommodation_agent(llm: ChatGoogleGenerativeAI, browser: Browser, controller: Controller, config: Dict, flight_data: Dict):
    """Creates an agent to find accommodation on Booking.com."""
    # Define selectors for Booking.com
    booking_selectors = {
        "destination_field": "input[name='ss']", # Example, verify selector
        "checkin_button": "[data-testid='date-display-field-start']",
        "checkout_button": "[data-testid='date-display-field-end']", # Often same as checkin
        "calendar": "[data-testid='datepicker-calendar']", # Verify selector
        "next_month": "[data-testid='datepicker-next-month']", # Verify selector
        # No 'done' button usually needed on Booking.com calendar
        "search_button": "button[type='submit']", # Example, verify selector
    }
    checkin_date = config['flight_date']
    checkout_date = config['return_date']
    destination = config['final_destination']

    task = (
        f"Navigate to `https://www.booking.com`. Perform the following actions:"
        f"1. Find the destination input field ('{booking_selectors['destination_field']}') and enter '{destination}'. Select the primary match if suggestions appear."
        f"2. Use the 'Select date in calendar' action to select the check-in date '{checkin_date}':"
        f"   {{'date': '{checkin_date}', 'calendar_selector': '{booking_selectors['calendar']}', 'date_button_selector': '{booking_selectors['checkin_button']}', 'next_month_selector': '{booking_selectors['next_month']}'}}"
        # Booking.com often closes calendar after first date, might need to click check-out button if separate
        f"3. Use the 'Select date in calendar' action to select the check-out date '{checkout_date}':"
        f"   {{'date': '{checkout_date}', 'calendar_selector': '{booking_selectors['calendar']}', 'date_button_selector': '{booking_selectors['checkout_button']}', 'next_month_selector': '{booking_selectors['next_month']}'}}"
        f"4. Configure number of adults/rooms if necessary (assume defaults for now unless specified)."
        f"5. Click the search button ('{booking_selectors['search_button']}')."
        f"6. Wait for the search results page to load."
        f"7. Analyze the first page of results. Find the accommodation that represents the best *value* (a balance of good price for the stay duration, positive guest rating (e.g., 8+), and reasonable location if apparent)."
        f"8. Extract the following details for the selected accommodation. Use 'N/A' if not found:"
        f"   - Name"
        f"   - Total price for the stay (if shown directly, otherwise calculate or state price per night)"
        f"   - Guest Rating (e.g., '8.5 / 10')"
        f"   - Location description (e.g., address snippet or neighborhood)"
        f"9. Return the extracted information ONLY in the following JSON format:\n"
        f"```json\n"
        f"{{\n"
        f"    \"name\": \"<accommodation_name>\",\n"
        f"    \"total_price\": \"<total_price_or_price_per_night>\",\n"
        f"    \"rating\": \"<guest_rating>\",\n"
        f"    \"location\": \"<location_description>\",\n"
        f"    \"search_url\": \"<current_page_url>\"\n" # Capture URL of results/property
        f"}}\n"
        f"```"
    )
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        controller=controller,
        validate_output=True,
        enable_memory=False
    )
    return agent

async def create_activities_agent(llm: ChatGoogleGenerativeAI, browser: Browser, controller: Controller, config: Dict, accommodation_data: Dict):
    """Creates an agent to find activities on TripAdvisor."""
    # Define selectors for TripAdvisor
    tripadvisor_selectors = {
        "search_box": "[aria-label='Search']", # Example, verify selector
        "things_to_do_tab": "a[href*='/Attractions']", # Example
        "date_picker_trigger": "[data-testid='date-picker']", # Example
        "calendar": "[data-testid='date-picker-calendar']", # Example
        "next_month": "[data-testid='date-picker-next-month']", # Example
        # TripAdvisor calendar might need separate start/end date selections
    }
    destination = config['final_destination']
    start_date = config['flight_date']
    end_date = config['return_date']

    try:
        start_dt = datetime.strptime(start_date, DATE_FORMAT)
        end_dt = datetime.strptime(end_date, DATE_FORMAT)
        num_days = max(1, (end_dt - start_dt).days) # Ensure at least 1 day
    except ValueError:
        logger.warning("Could not parse dates for activity duration calculation, defaulting to 3 activities.")
        num_days = 3

    task = (
        f"Navigate to `https://www.tripadvisor.com`. Perform the following actions:"
        f"1. Use the main search box ('{tripadvisor_selectors['search_box']}') to search for 'Things to Do in {destination}'."
        f"2. On the results page, ensure you are viewing attractions/activities."
        # Date selection on TripAdvisor can be complex, LLM might need to adapt
        f"3. If a date filter is prominent, try to set the date range from {start_date} to {end_date}. Use the 'Select date in calendar' action if a standard calendar appears, providing appropriate selectors. If date filtering isn't straightforward, proceed without it initially."
        # Example Calendar Interaction (Adapt based on actual TA interface):
        # f"   - Click the date trigger: '{tripadvisor_selectors['date_picker_trigger']}'"
        # f"   - Select start date '{start_date}': {{'date': '{start_date}', 'calendar_selector': '{tripadvisor_selectors['calendar']}', ...}}"
        # f"   - Select end date '{end_date}': {{'date': '{end_date}', 'calendar_selector': '{tripadvisor_selectors['calendar']}', ...}}"
        f"4. Browse the list of activities/attractions."
        f"5. Identify {num_days} distinct, highly-rated (aim for 4+ stars or equivalent) activities. Prioritize a variety of types (e.g., landmark, museum, outdoor, tour)."
        # Optional: f"Consider proximity to {accommodation_data.get('location', destination)} if location data is available."
        f"6. For each selected activity, extract:"
        f"   - Name"
        f"   - Type (e.g., 'Museum', 'Landmark', 'Tour')"
        f"   - Price indication (e.g., 'Free', '$$', 'From $50', 'N/A')"
        f"   - Rating (e.g., '4.5 / 5', number of reviews if available)"
        f"7. Return the extracted information ONLY in the following JSON format:\n"
        f"```json\n"
        f"{{\n"
        f"    \"activities\": [\n"
        f"        {{\n"
        f"            \"name\": \"<activity1_name>\",\n"
        f"            \"type\": \"<activity1_type>\",\n"
        f"            \"price_indication\": \"<activity1_price>\",\n"
        f"            \"rating\": \"<activity1_rating>\"\n"
        # Optional: f"            \"url\": \"<activity1_url>\"\n"
        f"        }},\n"
        # ... repeat for num_days activities
        f"        {{\n"
        f"            \"name\": \"<activityN_name>\",\n"
        f"            \"type\": \"<activityN_type>\",\n"
        f"            \"price_indication\": \"<activityN_price>\",\n"
        f"            \"rating\": \"<activityN_rating>\"\n"
        f"        }}\n"
        f"    ],\n"
        f"    \"search_url\": \"<current_page_url>\"\n"
        f"}}\n"
        f"```"
    )
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        controller=controller,
        validate_output=True,
        enable_memory=False
    )
    return agent

async def create_itinerary_planner_agent(llm: ChatGoogleGenerativeAI, config: Dict, travel_data: TravelData):
    """Creates an agent to generate a text-based itinerary."""
    # This agent doesn't interact with the browser directly for planning
    task = (
        f"Based ONLY on the provided travel data, create a suggested day-by-day itinerary for a trip from {config['initial_destination']} to {config['final_destination']} from {config['flight_date']} to {config['return_date']}."
        f"\n**Provided Data:**\n"
        f"- Flight Details: {travel_data.flight_data}\n"
        f"- Accommodation Details: {travel_data.accommodation_data}\n"
        f"- Selected Activities: {travel_data.activities_data}\n"
        f"\n**Instructions:**\n"
        f"1. Structure the itinerary clearly day by day (e.g., Day 1: {config['flight_date']}, Day 2:, ... Day N: {config['return_date']})."
        f"2. Incorporate the flight arrival and departure times."
        f"3. Schedule the selected activities, allocating one or potentially two per day depending on type and duration (use common sense)."
        f"4. Suggest logical timings (morning/afternoon) for activities."
        f"5. Include placeholders for meals (e.g., 'Lunch near [Activity]', 'Dinner')."
        f"6. Briefly mention potential transport between locations if logical (e.g., 'Metro to Museum', 'Walk to Eiffel Tower'). Assume standard city transport is available."
        f"7. Keep the tone practical and informative."
        f"8. Output the itinerary as well-formatted text."
    )

    # Using a standard LangChain call might be simpler here if no browser needed
    # agent = Agent(...) # If browser context is somehow still useful
    # For now, assume a direct LLM call pattern would work:
    # response = await llm.ainvoke(task)
    # return response.content

    # Or, if sticking to Agent structure but without browser interaction:
    agent = Agent(
        task=task,
        llm=llm,
        browser=None, # Explicitly state no browser needed for this agent
        controller=None,
        validate_output=False, # Output is text
        enable_memory=False
    )
    return agent


# --- Main Execution Logic ---

async def run_agent_task(agent_name: str, agent_creator, *args) -> Optional[Dict[str, Any]]:
    """Helper function to create, run, and handle errors for an agent task."""
    logger.info(f"--- Starting Task: {agent_name} ---")
    result = None
    try:
        agent = await agent_creator(*args)
        # The result format depends on the Agent's implementation
        # Assuming it returns the extracted data or raises an error
        action_result = await agent.run()

        # Check if action_result is structured (dict) and indicates success
        # This depends heavily on how browser_use.Agent returns results
        # Assuming a dict is returned on success based on original code prompts
        if isinstance(action_result, dict):
             result = action_result
             logger.info(f"{agent_name} Result: {result}")
             logger.info(f"--- Task Successful: {agent_name} ---")
        elif isinstance(action_result, str) and agent_name == "Itinerary Planning":
             result = {"itinerary_text": action_result} # Wrap text result
             logger.info(f"{agent_name} Result:\n{action_result}")
             logger.info(f"--- Task Successful: {agent_name} ---")
        else:
             # Handle unexpected result format
             logger.error(f"{agent_name} returned unexpected result format: {type(action_result)}")
             logger.error(f"--- Task Failed: {agent_name} ---")
             result = None # Explicitly mark as failure

    except Exception as e:
        logger.exception(f"An error occurred during {agent_name}: {e}")
        logger.error(f"--- Task Failed: {agent_name} ---")
        result = None # Ensure failure is marked

    # Optional: Add a small delay between major tasks if needed for stability
    # await asyncio.sleep(5)
    return result


async def main():
    """Main function to orchestrate the travel planning process."""
    browser = None
    playwright_instance = None # Keep track to close it properly
    try:
        llm = initialize_llm()
        browser, controller = initialize_browser()

        # Get the underlying Playwright browser instance to manage its lifecycle
        # This depends on how browser_use exposes it. Assuming get_playwright_browser()
        try:
             playwright_instance = await browser.get_playwright_browser()
             if playwright_instance is None:
                  raise RuntimeError("Failed to get Playwright browser instance.")
             logger.info("Successfully obtained Playwright browser instance.")
        except Exception as e:
             logger.exception("Could not get underlying Playwright browser instance.")
             return # Cannot proceed without the browser instance


        travel_data = TravelData()

        # === Step 1: Initial Navigation & Check ===
        initial_nav_result = await run_agent_task(
            "Initial Navigation to Skyscanner",
            create_initial_navigation_agent,
            llm, browser, controller, "https://www.skyscanner.net"
        )
        if not initial_nav_result: # Check if navigation failed
             logger.error("Initial navigation/check failed. Aborting.")
             return # Stop if we can't even load the first page properly

        # === Step 2: Find Flights ===
        flight_result = await run_agent_task(
             "Flight Search",
             create_flight_agent,
             llm, browser, controller, USER_CONFIG
        )
        if flight_result:
            travel_data.flight_data = flight_result
        else:
            logger.error("Flight search failed. Aborting dependent tasks.")
            return # Stop if flights are essential

        # === Step 3: Find Accommodation ===
        if travel_data.flight_data: # Proceed only if flight data is available
             accommodation_result = await run_agent_task(
                 "Accommodation Search",
                 create_accommodation_agent,
                 llm, browser, controller, USER_CONFIG, travel_data.flight_data
             )
             if accommodation_result:
                 travel_data.accommodation_data = accommodation_result
             else:
                 logger.warning("Accommodation search failed. Itinerary will be incomplete.")
                 # Decide whether to continue without accommodation or stop

        # === Step 4: Find Activities ===
        if travel_data.accommodation_data: # Best effort, proceed even if accom failed but maybe less useful
             activities_result = await run_agent_task(
                 "Activities Search",
                 create_activities_agent,
                 llm, browser, controller, USER_CONFIG, travel_data.accommodation_data
             )
             if activities_result:
                 travel_data.activities_data = activities_result
             else:
                 logger.warning("Activities search failed. Itinerary will be incomplete.")

        # === Step 5: Create Itinerary ===
        # Proceed if we have at least flight data
        if travel_data.flight_data:
             # Itinerary planning might not need the browser, pass None if applicable to creator
             itinerary_result = await run_agent_task(
                 "Itinerary Planning",
                 create_itinerary_planner_agent,
                 llm, USER_CONFIG, travel_data # Pass data collected so far
             )
             if itinerary_result and "itinerary_text" in itinerary_result:
                 travel_data.itinerary = itinerary_result["itinerary_text"]
                 logger.info("\n--- Generated Itinerary ---")
                 print(travel_data.itinerary) # Print final output cleanly
                 logger.info("--- End of Itinerary ---")
             else:
                 logger.error("Itinerary generation failed.")
        else:
             logger.warning("Skipping itinerary generation as flight data is missing.")


        logger.info("\n--- Final Collected Data ---")
        logger.info(travel_data)
        logger.info("--- Travel Planning Process Completed ---")

    except Exception as e:
        logger.exception(f"An unexpected error occurred in the main loop: {e}")
    finally:
        # Clean up browser resources
        if playwright_instance:
            logger.info("Closing browser...")
            try:
                await playwright_instance.close()
                logger.info("Browser closed successfully.")
            except Exception as e:
                logger.exception(f"Error closing browser: {e}")
        else:
            logger.warning("Playwright instance was not available for closing.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nScript interrupted by user.")
    except Exception as e:
        logger.exception(f"A fatal error occurred: {e}")
    finally:
        # Ensure event loop cleanup if necessary (often handled by asyncio.run)
        logger.info("Script finished.")