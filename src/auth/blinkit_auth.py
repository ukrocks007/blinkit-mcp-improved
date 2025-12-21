import os
from playwright.sync_api import sync_playwright


class BlinkitAuth:
    def __init__(self, headless: bool = False, session_path: str = "cookies/auth.json"):
        self.headless = headless
        self.session_path = session_path
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start_browser(self):
        """Starts the Playwright browser (Firefox)."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.firefox.launch(headless=self.headless)

        if os.path.exists(self.session_path):
            print(f"Loading session from {self.session_path}")
            self.context = self.browser.new_context(storage_state=self.session_path)
        else:
            print("No existing session found. Starting fresh.")
            self.context = self.browser.new_context()

        self.page = self.context.new_page()
        self.page.goto("https://blinkit.com/")
        print("Opened Blinkit.com")

    def login(self, phone_number: str):
        """Initiates the login process with a phone number."""
        print(f"Attempting to log in with {phone_number}...")

        # 1. Click Login Button
        try:
            # Try multiple strategies to find the Login button
            if self.page.is_visible("text='Login'"):
                self.page.click("text='Login'")
                print("Clicked 'Login' text.")
            elif self.page.is_visible("div[class*='ProfileButton__Container']"):
                self.page.locator("div[class*='ProfileButton__Container']").click()
                print("Clicked ProfileButton container.")
            else:
                print(
                    "Could not find explicit Login button. Checking if already on login screen..."
                )
        except Exception as e:
            print(f"Error clicking login button: {e}")

        # 2. Wait for Login Modal / Phone Input
        try:
            # Wait for the modal to appear.
            # We look for the mobile input field.
            # Common selectors for mobile input:
            # name='mobile', type='tel', placeholder containing 'Mobile'

            print("Waiting for phone number input...")
            # Increased timeout and generic selector
            phone_input = self.page.wait_for_selector(
                "input[type='tel'], input[name='mobile'], input[type='text']",
                state="visible",
                timeout=5000,
            )

            if phone_input:
                phone_input.click()
                phone_input.fill(phone_number)
                print(f"Filled phone number: {phone_number}")

                # 3. Submit Phone Number
                # Usually a 'Next' or 'Continue' button
                # We need to find the button *inside* the modal or form
                self.page.wait_for_timeout(500)  # slight delay for UI update

                # Try to find a submit button
                # Strategy: Button with text 'Next', 'Continue', 'Get OTP'
                # or simple 'button' tag inside the form

                # Check for "Get OTP" or "Next"
                if self.page.is_visible("text='Next'"):
                    self.page.click("text='Next'")
                elif self.page.is_visible("text='Continue'"):
                    self.page.click("text='Continue'")
                else:
                    # Fallback: press Enter on the input
                    self.page.keyboard.press("Enter")
                    print("Pressed Enter to submit.")

            else:
                print("Phone input found but None returned?")

        except Exception as e:
            print(f"Error entering phone number: {e}")
            # Dump partial page source for debugging if needed
            # print(self.page.content())

    def enter_otp(self, otp: str):
        """Enters the OTP."""
        try:
            print("Waiting for OTP input...")
            # Wait for any input to be visible (4 digit boxes or single input)
            self.page.wait_for_selector("input", timeout=10000)

            # Check for OTP inputs
            # Often apps use 4 separate inputs for OTP
            inputs = self.page.locator("input")
            count = inputs.count()

            if count == 4:
                print("Detected 4-digit OTP inputs.")
                for i, digit in enumerate(otp):
                    if i < 4:
                        inputs.nth(i).fill(digit)
                        self.page.wait_for_timeout(100)  # small delay
            else:
                # Single input?
                print(f"Detected {count} inputs. Trying to fill first/relevant one.")
                # Look for input with 'otp' in name or id or class
                otp_input = self.page.locator(
                    "input[data-test-id='otp-input'], input[name*='otp'], input[id*='otp']"
                ).first
                if otp_input.is_visible():
                    otp_input.fill(otp)
                else:
                    # Fallback: fill generic input
                    self.page.fill("input", otp)

            print("Entered OTP. Waiting for auto-submit or button...")
            # Some apps need a click on Verify
            # self.page.click("text='Verify'") # Uncomment if needed
            self.page.keyboard.press("Enter")

        except Exception as e:
            print(f"Error entering OTP: {e}")

    def is_logged_in(self) -> bool:
        """Checks if the user is logged in."""
        try:
            # Check for "Profile" or "Account" or absence of "Login"
            # self.page.wait_for_selector("text=My Account", timeout=5000)
            if self.page.is_visible("text=My Account") or self.page.is_visible(
                ".user-profile"
            ):
                return True

            # Another check: "Login" button should NOT be visible
            if not self.page.is_visible("text=Login"):
                # And some user element is visible?
                return True

            return False
        except:
            return False

    def save_session(self):
        """Saves functionality cookies to file."""
        self.context.storage_state(path=self.session_path)
        print(f"Session saved to {self.session_path}")

    def close(self):
        """Closes the browser."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
