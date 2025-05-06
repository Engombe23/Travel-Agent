import os
import asyncio
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime, timedelta
from browser_use import Agent, Browser, BrowserConfig, Controller, ActionResult, BrowserContextConfig
from typing import Dict, List, Optional, Any

load_dotenv()

# API key
api_key = os.environ.get("GEMINI_API_KEY")

class TravelData:
    def __init__(self):
        self.flight_data = None
        self.accommodation_data = None
        self.activities_data = None
        self.itinerary = None

def flight_date_info(date):
  date_format = '%d/%m/%Y'
  flight_date_obj = datetime.strptime(date, date_format)
  return flight_date_obj.strftime(date_format)

# For now, hardcoded user input
user_input = {
    "flight_date": "15/07/2025",
    "initial_destination": "London",
    "final_destination": "Paris",
    "return_date": "22/07/2025"
}

# Initialize travel data
travel_data = TravelData()

# Browser Configuration
config = BrowserConfig(
    headless=False,  # Disable headless mode to avoid detection
    disable_security=False,
    deterministic_rendering=False,
    user_agent_mode="random",
    new_context_config=BrowserContextConfig(
        viewport={'width': 1440, 'height': 900},
        device_scale_factor=1,
        is_mobile=False,
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

# Initialize LLM with rate limiting
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=api_key,
    max_retries=3,  # Add retries for rate limiting
    max_tokens=1024,
    temperature=0.5
)

async def initialize_browser():
    playwright_browser = await browser.get_playwright_browser()
    return playwright_browser

async def create_captcha_agent():
    agent = Agent(
        task=(
          " 1. **Navigate & Load:**"
          " * Attempt to navigate to `https://www.skyscanner.net`."
          " * Wait up to **[e.g., 20-25]** seconds for the page to attempt loading."
          " * During loading and after, actively look for and attempt to dismiss standard cookie/consent banners if they appear and might obstruct content checks. If a banner cannot be dismissed and blocks checks, note this as a potential issue."
"2.  **Verify Success State:**"
"* After the wait time, check if the page successfully displays key flight search elements (e.g., clearly visible input fields for From/To, date selectors, Search flights button)."
"* If these key elements are present and interactive: Consider the page successfully loaded. Proceed with the next planned task on Skyscanner."
"3.  **Handle Failure/Non-Success State:**"    
"* If the key flight search elements are NOT reliably detected after the timeout, OR if navigation failed earlier:"
"        a.  Analyze Current Page: Examine the current page's URL and visible content thoroughly."
"        b.  Check for Explicit Site Errors: Look for common error indicators like Access Denied, Blocked, Forbidden, Error 403, Error 503, Site Maintenance or similar messages indicating the site itself is unavailable or blocking access."
"            * If found: STOP execution for Skyscanner and report: ERROR: Skyscanner access failed (Reason: [Detected Error Message])."        
"        c.  Check for CAPTCHA Indicators: Search broadly for keywords (e.g., CAPTCHA, verify, human, security check, prove you're not a robot, hCaptcha, reCAPTCHA, Cloudflare, Turnstile, challenge) AND visual elements:"
"            i.  Press and Hold Button: If this specific interaction is detected."
"                * Action: STOP and report: ACTION REQUIRED: Manual intervention needed (Press and Hold CAPTCHA) on Skyscanner."
"            ii. Checkbox CAPTCHA: (e.g., a box next to I'm not a robot)."
"                * Action: STOP and report: ACTION REQUIRED: Manual intervention needed (Checkbox CAPTCHA - e.g., reCAPTCHA) on Skyscanner."
"            iii. Image Selection / Puzzle / Grid CAPTCHA: (e.g., instructions like select all squares with..., slide the puzzle piece)."
"                * Action: STOP and report: ACTION REQUIRED: Manual intervention needed (Image/Puzzle CAPTCHA) on Skyscanner."
"            iv. Other/Unclear CAPTCHA: If indicators strongly suggest a security challenge/CAPTCHA but it doesn't fit the specific types above."
"                * Action: STOP and report: ACTION REQUIRED: Manual intervention needed (CAPTCHA detected - type unclear) on Skyscanner."
"        d.  Handle Ambiguous Failures: If no explicit site error (step 3b) or clear CAPTCHA (step 3c) is identified, but the page is incorrect (e.g., partially loaded, wrong language redirect, blank page, blocked by undismissed banner)."
"            * Action: STOP and report: ERROR: Failed to load Skyscanner search page correctly or encountered unexpected state. Manual check recommended."
 ),
        llm=llm,
  browser=browser,
  controller=controller
)
    await agent._verify_llm_connection()
    return agent

@controller.action('Select date in calendar')
async def select_date(data: Dict[str, str], browser: Browser, page: Optional[Any] = None) -> Dict[str, str]:
    try:
        if page is None:
            page = await browser.new_page()
            close_page = True
        else:
            close_page = False
            
        # Wait for calendar to load
        await page.wait_for_selector('[data-testid="depart-fsc-datepicker-button"]', timeout=10000)
        
        # Determine if this is a departure or return date
        is_departure = 'depart' in data.get('type', '').lower()
        date_button_selector = '[data-testid="depart-fsc-datepicker-button"]' if is_departure else '[data-testid="return-fsc-datepicker-button"]'
        
        # Click the correct date picker button if not already open
        if not await page.is_visible('[data-testid="datepicker-calendar"]'):
            await page.click(date_button_selector)
            await page.wait_for_selector('[data-testid="datepicker-calendar"]', timeout=10000)
            
        # Format the date for the aria-label
        date_obj = datetime.strptime(data['date'], '%d/%m/%Y')
        date_label = date_obj.strftime("%A, %d %B %Y")
        date_selector = f'[aria-label="{date_label}"]'
        
        # Get current month and year from the calendar
        current_month_text = await page.evaluate('() => document.querySelector("[data-testid=datepicker-calendar]").textContent')
        print(f"Current month in calendar: {current_month_text}")
        
        # Extract month and year from the target date
        target_month = date_obj.strftime("%B %Y")
        print(f"Looking for month: {target_month}")
        
        # Try up to 12 months ahead
        for attempt in range(12):
            # Check if we're in the correct month
            if target_month in current_month_text:
                print(f"Found correct month: {target_month}")
                # Try to find and click the date
                if await page.query_selector(date_selector):
                    await page.eval_on_selector(date_selector, 'el => el.scrollIntoView()')
                    await page.click(date_selector)
                    break
                else:
                    raise Exception(f"Date {date_label} not found in the correct month")
            
            # If not in the correct month, click next month
            next_btn = await page.query_selector('[aria-label="Next month"]')
            if next_btn:
                await next_btn.click()
                await page.wait_for_timeout(1000)
                # Update current month
                current_month_text = await page.evaluate('() => document.querySelector("[data-testid=datepicker-calendar]").textContent')
                print(f"Navigated to month: {current_month_text}")
            else:
                raise Exception("Next month button not found")
        else:
            raise Exception(f"Could not find month {target_month} after 12 attempts")
            
        # Click done button
        await page.click('[data-testid="date-picker-done-button"]')
        return {"status": "success", "message": "Date selected successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if close_page and page:
            await page.close()

@controller.action('Select date in Booking.com calendar')
async def select_booking_date(data: Dict[str, str], browser: Browser, page: Optional[Any] = None) -> Dict[str, str]:
    try:
        if page is None:
            page = await browser.new_page()
            close_page = True
        else:
            close_page = False
            
        # Wait for calendar to load
        await page.wait_for_selector('[data-testid="date-display-field-start"]', timeout=10000)
        
        # Click the date picker button if not already open
        if not await page.is_visible('[data-testid="datepicker-calendar"]'):
            await page.click('[data-testid="date-display-field-start"]')
            await page.wait_for_selector('[data-testid="datepicker-calendar"]', timeout=10000)
            
        # Format the date for the aria-label
        date_obj = datetime.strptime(data['date'], '%d/%m/%Y')
        date_label = date_obj.strftime("%A, %d %B %Y")
        date_selector = f'[aria-label="{date_label}"]'
        
        # Get current month and year from the calendar
        current_month_text = await page.evaluate('() => document.querySelector("[data-testid=datepicker-calendar]").textContent')
        print(f"Current month in Booking.com calendar: {current_month_text}")
        
        # Extract month and year from the target date
        target_month = date_obj.strftime("%B %Y")
        print(f"Looking for month: {target_month}")
        
        # Try up to 12 months ahead
        for attempt in range(12):
            # Check if we're in the correct month
            if target_month in current_month_text:
                print(f"Found correct month: {target_month}")
                # Try to find and click the date
                if await page.query_selector(date_selector):
                    await page.eval_on_selector(date_selector, 'el => el.scrollIntoView()')
                    await page.click(date_selector)
                    break
                else:
                    raise Exception(f"Date {date_label} not found in the correct month")
            
            # If not in the correct month, click next month
            next_btn = await page.query_selector('[data-testid="datepicker-next-month"]')
            if next_btn:
                await next_btn.click()
                await page.wait_for_timeout(1000)
                # Update current month
                current_month_text = await page.evaluate('() => document.querySelector("[data-testid=datepicker-calendar]").textContent')
                print(f"Navigated to month: {current_month_text}")
            else:
                raise Exception("Next month button not found")
        else:
            raise Exception(f"Could not find month {target_month} after 12 attempts")
            
        return {"status": "success", "message": "Date selected successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if close_page and page:
            await page.close()

@controller.action('Select date in TripAdvisor calendar')
async def select_tripadvisor_date(data: Dict[str, str], browser: Browser, page: Optional[Any] = None) -> Dict[str, str]:
    try:
        if page is None:
            page = await browser.new_page()
            close_page = True
        else:
            close_page = False
            
        # Wait for calendar to load
        await page.wait_for_selector('[data-testid="date-picker"]', timeout=10000)
        
        # Click the date picker button if not already open
        if not await page.is_visible('[data-testid="date-picker-calendar"]'):
            await page.click('[data-testid="date-picker"]')
            await page.wait_for_selector('[data-testid="date-picker-calendar"]', timeout=10000)
            
        # Format the date for the aria-label
        date_obj = datetime.strptime(data['date'], '%d/%m/%Y')
        date_label = date_obj.strftime("%A, %d %B %Y")
        date_selector = f'[aria-label="{date_label}"]'
        
        # Get current month and year from the calendar
        current_month_text = await page.evaluate('() => document.querySelector("[data-testid=date-picker-calendar]").textContent')
        print(f"Current month in TripAdvisor calendar: {current_month_text}")
        
        # Extract month and year from the target date
        target_month = date_obj.strftime("%B %Y")
        print(f"Looking for month: {target_month}")
        
        # Try up to 12 months ahead
        for attempt in range(12):
            # Check if we're in the correct month
            if target_month in current_month_text:
                print(f"Found correct month: {target_month}")
                # Try to find and click the date
                if await page.query_selector(date_selector):
                    await page.eval_on_selector(date_selector, 'el => el.scrollIntoView()')
                    await page.click(date_selector)
                    break
                else:
                    raise Exception(f"Date {date_label} not found in the correct month")
            
            # If not in the correct month, click next month
            next_btn = await page.query_selector('[data-testid="date-picker-next-month"]')
            if next_btn:
                await next_btn.click()
                await page.wait_for_timeout(1000)
                # Update current month
                current_month_text = await page.evaluate('() => document.querySelector("[data-testid=date-picker-calendar]").textContent')
                print(f"Navigated to month: {current_month_text}")
            else:
                raise Exception("Next month button not found")
        else:
            raise Exception(f"Could not find month {target_month} after 12 attempts")
            
        return {"status": "success", "message": "Date selected successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if close_page and page:
            await page.close()

async def check_for_captcha(browser: Browser) -> bool:
    try:
        playwright_browser = await browser.get_playwright_browser()
        page = await playwright_browser.new_page()
        await page.goto("https://www.skyscanner.net")
        await page.wait_for_selector('body')
        current_url = page.url
        
        # If we hit a CAPTCHA, immediately close the page and return True
        if "captcha-v2" in current_url:
            print("CAPTCHA detected, redirecting to Google search...")
            await page.close()
            return True
            
        await page.close()
        return False
    except Exception as e:
        print(f"Error checking for CAPTCHA: {str(e)}")
        return False

async def navigate_to_skyscanner(browser: Browser):
    print("Navigating to Skyscanner through Google...")
    playwright_browser = await browser.get_playwright_browser()
    page = await playwright_browser.new_page()
    
    try:
        # Go to Google
        await page.goto("https://www.google.com")
        
        # Search for Skyscanner
        await page.type('textarea[name="q"]', "skyscanner")
        await page.keyboard.press('Enter')
        
        # Wait for search results to load
        await page.wait_for_selector('#search')
        
        # Try to find and click the Skyscanner link
        try:
            # First try the main search result
            await page.click('a[href*="skyscanner.net"]:has-text("Skyscanner")')
        except:
            # If that fails, try any Skyscanner link
            await page.click('a[href*="skyscanner.net"]')
            
        # Verify we're on Skyscanner
        await page.wait_for_selector('body')
        if "skyscanner.net" not in page.url:
            raise Exception("Failed to navigate to Skyscanner")
            
    except Exception as e:
        print(f"Error during navigation: {str(e)}")
        # Try direct navigation as fallback
        await page.goto("https://www.skyscanner.net")
    finally:
        await page.close()


async def create_flight_agent():
    agent = Agent(
        task=(
            f"On the current Skyscanner page, "
            f"click the flight tab if not already selected. "
            f"Wait for the search form to load. "
            f"Click the 'From' field and type '{user_input['initial_destination']}' exactly. "
            f"Wait for the dropdown to appear and click the first option that matches '{user_input['initial_destination']}'. "
            f"Click the 'To' field and type '{user_input['final_destination']}' exactly. "
            f"Wait for the dropdown to appear and click the first option that matches '{user_input['final_destination']}'. "
            f"Click the 'Depart' date field. "
            f"Wait for the calendar to load. "
            f"Use the 'Select date in calendar' action to select the date {user_input['flight_date']} with type 'depart'. "
            f"Click the 'Return' date field. "
            f"Wait for the calendar to load. "
            f"Use the 'Select date in calendar' action to select the date {user_input['return_date']} with type 'return'. "
            f"Click the 'Search' button. "
            f"Wait for the search results to load. "
            f"Find the cheapest round-trip flight in the results. "
            f"Click on the flight to view details. "
            f"Extract and return the following information in JSON format: "
            f"{{"
            f"    'price': price of the flight,"
            f"    'airline': name of the airline,"
            f"    'departure_time': departure time,"
            f"    'arrival_time': arrival time,"
            f"    'return_departure_time': return flight departure time,"
            f"    'return_arrival_time': return flight arrival time,"
            f"    'url': current URL of the selected flight"
            f"}}"
        ),
        llm=llm,
        browser=browser,
        controller=controller,
        validate_output=False,
        enable_memory=False
    )
    await agent._verify_llm_connection()
    return agent

async def create_accommodation_agent(flight_data: Dict):
    agent = Agent(
        task=(
            f"Go to https://www.booking.com. "
            f"Search for accommodation in {user_input['final_destination']} for the dates {user_input['flight_date']} to {user_input['return_date']}. "
            f"Click the check-in date field. "
            f"Wait for the calendar to load. "
            f"Use the 'Select date in Booking.com calendar' action to select the date {user_input['flight_date']}. "
            f"Click the check-out date field. "
            f"Wait for the calendar to load. "
            f"Use the 'Select date in Booking.com calendar' action to select the date {user_input['return_date']}. "
            f"Click the search button. "
            f"Wait for the search results to load. "
            f"Find and select the best value accommodation (considering price, location, and reviews). "
            f"Extract and return the following information in JSON format: "
            f"{{"
            f"    'name': name of the accommodation,"
            f"    'price_per_night': price per night,"
            f"    'total_price': total price for the stay,"
            f"    'location': location details,"
            f"    'rating': rating out of 10,"
            f"    'url': current URL of the selected accommodation"
            f"}}"
        ),
        llm=llm,
        browser=browser,
        controller=controller,
        validate_output=True,
        enable_memory=False  
    )
    await agent._verify_llm_connection()
    return agent

async def create_activities_agent(flight_data: Dict, accommodation_data: Dict):
    # Calculate number of days for activities
    start_date = datetime.strptime(user_input['flight_date'], '%d/%m/%Y')
    end_date = datetime.strptime(user_input['return_date'], '%d/%m/%Y')
    num_days = (end_date - start_date).days
    
    agent = Agent(
        task=(
            f"Go to https://www.tripadvisor.com. "
            f"Search for activities in {user_input['final_destination']}. "
            f"Click the date picker. "
            f"Wait for the calendar to load. "
            f"Use the 'Select date in TripAdvisor calendar' action to select the date {user_input['flight_date']}. "
            f"Click the end date picker. "
            f"Wait for the calendar to load. "
            f"Use the 'Select date in TripAdvisor calendar' action to select the date {user_input['return_date']}. "
            f"Click the search button. "
            f"Wait for the search results to load. "
            f"Find and select {num_days} different activities (one per day) that are: "
            f"1. Well-rated (4+ stars)"
            f"2. Within reasonable distance from the accommodation at {accommodation_data['location']}"
            f"3. Cover different types of experiences"
            f"Extract and return the following information in JSON format: "
            f"{{"
            f"    'activities': ["
            f"        {{"
            f"            'name': activity name,"
            f"            'type': type of activity,"
            f"            'price': price if applicable,"
            f"            'duration': estimated duration,"
            f"            'rating': rating out of 5,"
            f"            'url': URL of the activity"
            f"        }}"
            f"    ]"
            f"}}"
        ),
        llm=llm,
        browser=browser,
        controller=controller,
        validate_output=True,
        enable_memory=False  
    )
    await agent._verify_llm_connection()
    return agent

async def create_itinerary_planner(flight_data: Dict, accommodation_data: Dict, activities_data: Dict):
    agent = Agent(
    task=(
            f"Create a detailed travel itinerary based on the following information: "
            f"Flight: {flight_data}"
            f"Accommodation: {accommodation_data}"
            f"Activities: {activities_data}"
            f"Generate a day-by-day itinerary that: "
            f"1. Optimizes travel time between activities"
            f"2. Balances activity types (e.g., morning cultural, afternoon leisure)"
            f"3. Includes practical information (transportation, meal suggestions)"
            f"4. Considers opening hours and activity durations"
            f"Return the itinerary in a clear, structured format."
        ),
        llm=llm,
    browser=browser,
    controller=controller,
    validate_output=True,
    enable_memory=False  
  ) 
    await agent._verify_llm_connection()
    return agent

async def main():
    try:
        print("Initializing travel planning system...")
        
        # Initialize browser with error handling
        try:
            await initialize_browser()
        except Exception as e:
            print(f"Error initializing browser: {e}")
            return
            
        # Step 1: Check for CAPTCHA and immediately redirect if found
        print("Step 1: Checking for CAPTCHA...")
        has_captcha = await check_for_captcha(browser)
        if has_captcha:
            print("CAPTCHA detected. Redirecting to Google search...")
            await navigate_to_skyscanner(browser)
        else:
            print("No CAPTCHA detected. Proceeding directly to Skyscanner...")
            playwright_browser = await browser.get_playwright_browser()
            page = await playwright_browser.new_page()
            await page.goto("https://www.skyscanner.net")
            await page.close()
        
        # Step 2: Find flights with error handling
        print("\nStep 2: Finding flights...")
        try:
            flight_agent = await create_flight_agent()
            flight_result = await flight_agent.run()
            travel_data.flight_data = flight_result
            print(f"Flight found: {flight_result}")
        except Exception as e:
            print(f"Error finding flights: {e}")
            return

        await asyncio.sleep(30)  # <-- Add delay here

        # Step 3: Find accommodation
        print("\nStep 3: Finding accommodation...")
        try:
            accommodation_agent = await create_accommodation_agent(travel_data.flight_data)
            accommodation_result = await accommodation_agent.run()
            travel_data.accommodation_data = accommodation_result
            print(f"Accommodation found: {accommodation_result}")
        except Exception as e:
            print(f"Error finding accommodation: {e}")
            return

        await asyncio.sleep(30)  # <-- Add delay here

        # Step 4: Find activities
        print("\nStep 4: Finding activities...")
        try:
            activities_agent = await create_activities_agent(travel_data.flight_data, travel_data.accommodation_data)
            activities_result = await activities_agent.run()
            travel_data.activities_data = activities_result
            print(f"Activities found: {activities_result}")
        except Exception as e:
            print(f"Error finding activities: {e}")
            return

        await asyncio.sleep(30)  # <-- Add delay here

        # Step 5: Create itinerary
        print("\nStep 5: Creating itinerary...")
        try:
            itinerary_planner = await create_itinerary_planner(
                travel_data.flight_data,
                travel_data.accommodation_data,
                travel_data.activities_data
            )
            itinerary_result = await itinerary_planner.run()
            travel_data.itinerary = itinerary_result
            print("\nFinal Itinerary:")
            print(itinerary_result)
        except Exception as e:
            print(f"Error creating itinerary: {e}")
            return
            
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Clean up browser resources
        try:
            playwright_browser = await browser.get_playwright_browser()
            await playwright_browser.close()
        except:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        # Ensure event loop is properly closed
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.close()
        except:
            pass