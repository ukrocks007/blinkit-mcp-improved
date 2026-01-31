from .base import BaseService


class CheckoutService(BaseService):
    async def place_order(self):
        """Proceeds to checkout."""

        if await self._is_store_closed():
            return "CRITICAL: Store is closed."

        try:
            proceed_btn = (
                self.page.locator("button, div").filter(has_text="Proceed").last
            )

            # If Proceed not visible, try opening the cart first
            if not await proceed_btn.is_visible():
                print("Proceed button not visible. Attempting to open Cart drawer...")
                cart_btn = self.page.locator(
                    "div[class*='CartButton__Button'], div[class*='CartButton__Container']"
                )
                if await cart_btn.count() > 0:
                    await cart_btn.first.click()
                    print("Clicked 'My Cart' button.")
                    await self.page.wait_for_timeout(2000)
                else:
                    print("Could not find 'My Cart' button.")

            # Try clicking Proceed again
            if await proceed_btn.is_visible():
                await proceed_btn.click()
                print("Clicked Proceed to checkout.")
                await self.page.wait_for_timeout(3000)
                
                # Check if address selection screen appears
                if await self._is_address_selection_visible():
                    print("Address selection screen detected.")
                    return "ADDRESS_SELECTION_REQUIRED"
                elif await self._is_payment_screen_visible():
                    print("Payment screen detected.")
                    return "PAYMENT_SCREEN_READY"
                else:
                    print("Unknown checkout state after clicking Proceed.")
                    return "CHECKOUT_INITIATED"
            else:
                print("Proceed button not visible. Cart might be empty or Store Unavailable.")
                return "PROCEED_BUTTON_NOT_FOUND"

        except Exception as e:
            print(f"Error placing order: {e}")
            return f"ERROR: {e}"

    async def _is_address_selection_visible(self):
        """Check if address selection modal/screen is visible."""
        address_indicators = [
            "text='Select Address'",
            "text='Choose Address'", 
            "text='Delivery Address'",
            "div:has-text('Add Address')",
            "div:has-text('Home')",
            "div:has-text('Work')"
        ]
        
        for indicator in address_indicators:
            if await self.page.is_visible(indicator, timeout=2000):
                return True
        return False

    async def _is_payment_screen_visible(self):
        """Check if payment selection screen is visible."""
        payment_indicators = [
            "text='Payment Options'",
            "text='Cash on Delivery'", 
            "text='UPI'",
            "text='Credit Card'",
            "#payment_widget"
        ]
        
        for indicator in payment_indicators:
            if await self.page.is_visible(indicator, timeout=2000):
                return True
        return False

    async def get_addresses(self):
        """Get list of saved addresses."""
        print("Getting saved addresses...")
        try:
            addresses = []
            
            # Look for address cards/items
            address_cards = self.page.locator("div:has-text('Home'), div:has-text('Work'), div:has-text('Other')")
            count = await address_cards.count()
            
            for i in range(count):
                card = address_cards.nth(i)
                text = await card.inner_text()
                addresses.append({
                    "index": i,
                    "text": text,
                    "type": "Home" if "Home" in text else "Work" if "Work" in text else "Other"
                })
            
            print(f"Found {len(addresses)} saved addresses")
            return addresses
            
        except Exception as e:
            print(f"Error getting addresses: {e}")
            return []

    async def select_address(self, index: int = 0):
        """Select address by index (0 = first address)."""
        print(f"Selecting address at index {index}...")
        try:
            # Wait for address selection screen
            await self.page.wait_for_timeout(2000)
            
            # Look for address cards
            address_cards = self.page.locator("div[role='button']:has-text('Home'), div[role='button']:has-text('Work'), div[role='button']:has-text('Other')")
            
            # Alternative selectors
            if await address_cards.count() == 0:
                address_cards = self.page.locator("div:has-text('Home'), div:has-text('Work'), div:has-text('Other')")
            
            if await address_cards.count() > index:
                await address_cards.nth(index).click()
                print(f"Selected address {index}")
                await self.page.wait_for_timeout(2000)
                return True
            else:
                print(f"Address index {index} not found. Available addresses: {await address_cards.count()}")
                return False
                
        except Exception as e:
            print(f"Error selecting address: {e}")
            return False

    async def proceed_to_pay(self):
        """Click Proceed to payment after address selection."""
        print("Proceeding to payment...")
        try:
            # Look for Proceed/Continue button after address selection
            proceed_buttons = [
                "button:has-text('Proceed')",
                "button:has-text('Continue')", 
                "div:has-text('Proceed')",
                "div:has-text('Continue')"
            ]
            
            for btn_selector in proceed_buttons:
                btn = self.page.locator(btn_selector)
                if await btn.count() > 0 and await btn.is_visible():
                    await btn.click()
                    print("Clicked Proceed to payment")
                    await self.page.wait_for_timeout(3000)
                    return True
            
            print("Could not find Proceed button")
            return False
            
        except Exception as e:
            print(f"Error proceeding to payment: {e}")
            return False

    async def select_cod(self):
        """Select Cash on Delivery payment method."""
        print("Selecting Cash on Delivery...")
        try:
            # Wait for payment options to load
            await self.page.wait_for_timeout(2000)
            
            # Look for COD option with various texts
            cod_selectors = [
                "text='Cash on Delivery'",
                "text='COD'", 
                "div:has-text('Cash on Delivery')",
                "div:has-text('Pay on Delivery')",
                "label:has-text('Cash on Delivery')",
                "button:has-text('Cash on Delivery')"
            ]
            
            for selector in cod_selectors:
                cod_option = self.page.locator(selector)
                if await cod_option.count() > 0:
                    await cod_option.click()
                    print("Selected Cash on Delivery")
                    await self.page.wait_for_timeout(1000)
                    return True
            
            print("Could not find Cash on Delivery option")
            return False
            
        except Exception as e:
            print(f"Error selecting COD: {e}")
            return False

    async def place_cod_order(self):
        """Place the final COD order."""
        print("Placing COD order...")
        try:
            # Look for final order placement button
            place_order_buttons = [
                "button:has-text('Place Order')",
                "button:has-text('Confirm Order')", 
                "div:has-text('Place Order')",
                "div:has-text('Confirm Order')",
                "button:has-text('Order Now')"
            ]
            
            for btn_selector in place_order_buttons:
                btn = self.page.locator(btn_selector)
                if await btn.count() > 0 and await btn.is_visible():
                    await btn.click()
                    print("Order placed successfully! 🎉")
                    await self.page.wait_for_timeout(3000)
                    return True
            
            print("Could not find Place Order button")
            return False
            
        except Exception as e:
            print(f"Error placing COD order: {e}")
            return False

    async def get_upi_ids(self):
        """Proceeds to checkout."""

        if await self._is_store_closed():
            return "CRITICAL: Store is closed."

        try:
            proceed_btn = (
                self.page.locator("button, div").filter(has_text="Proceed").last
            )

            # If Proceed not visible, try opening the cart first
            if not await proceed_btn.is_visible():
                print("Proceed button not visible. Attempting to open Cart drawer...")
                cart_btn = self.page.locator(
                    "div[class*='CartButton__Button'], div[class*='CartButton__Container']"
                )
                if await cart_btn.count() > 0:
                    await cart_btn.first.click()
                    print("Clicked 'My Cart' button.")
                    await self.page.wait_for_timeout(2000)
                else:
                    print("Could not find 'My Cart' button.")

            # Try clicking Proceed again
            if await proceed_btn.is_visible():
                await proceed_btn.click()
                print(
                    "Cart checkout successfully.\nYou can select the payment method and proceed to pay."
                )
                await self.page.wait_for_timeout(3000)
            else:
                print(
                    "Proceed button not visible. Cart might be empty or Store Unavailable."
                )

        except Exception as e:
            print(f"Error placing order: {e}")

    async def get_upi_ids(self):
        """Scrapes available UPI IDs/options from the payment widget."""
        print("Getting available UPI IDs...")
        try:
            iframe_element = await self.page.wait_for_selector(
                "#payment_widget", timeout=30000
            )
            if not iframe_element:
                print("Payment widget iframe not found.")
                return []

            frame = await iframe_element.content_frame()
            if not frame:
                return []

            await frame.wait_for_load_state("networkidle")

            ids = []
            # Try to find elements that look like VPAs (contain @) inside the frame
            vpa_locators = frame.locator("text=/@/")
            count = await vpa_locators.count()
            for i in range(count):
                text = await vpa_locators.nth(i).inner_text()
                if "@" in text:
                    ids.append(text.strip())

            # Also add "Add new UPI ID" option if exists
            if await frame.locator("text='Add new UPI ID'").count() > 0:
                ids.append("Add new UPI ID")

            print(f"Found UPI IDs: {ids}")
            return ids

        except Exception as e:
            print(f"Error getting UPI IDs: {e}")
            return []

    async def select_upi_id(self, upi_id: str):
        """Selects a specific UPI ID or enters a new one."""
        print(f"Selecting UPI ID: {upi_id}...")
        try:
            iframe_element = await self.page.wait_for_selector(
                "#payment_widget", timeout=30000
            )
            if not iframe_element:
                return

            frame = await iframe_element.content_frame()
            if not frame:
                return

            # 1. Try to click on an existing saved VPA if it matches
            saved_vpa = frame.locator(f"text='{upi_id}'")
            if await saved_vpa.count() > 0:
                await saved_vpa.first.click()
                print(f"Clicked saved VPA: {upi_id}")
                return

            # 2. If not found, Select "UPI" / "Add new UPI ID" section
            # Click generic UPI header first if needed to expand
            upi_header = frame.locator("div").filter(has_text="UPI").last
            if await upi_header.count() > 0:
                await upi_header.click()

            await self.page.wait_for_timeout(500)

            # 3. Enter VPA in input
            input_locator = frame.locator(
                "input[placeholder*='UPI'], input[type='text']"
            )
            if await input_locator.count() > 0:
                await input_locator.first.fill(upi_id)
                print(f"Filled UPI ID: {upi_id}")

                # Verify
                verify_btn = frame.locator("text=Verify")
                if await verify_btn.count() > 0:
                    await verify_btn.click()
                    print("Clicked Verify button.")
            else:
                print("Could not find UPI input field.")

        except Exception as e:
            print(f"Error selecting UPI ID: {e}")

    async def click_pay_now(self):
        """Clicks the final Pay Now button."""
        try:
            # Strategy 1: Specific class partial match
            pay_btn_specific = self.page.locator(
                "div[class*='Zpayments__Button']:has-text('Pay Now')"
            )
            if (
                await pay_btn_specific.count() > 0
                and await pay_btn_specific.first.is_visible()
            ):
                await pay_btn_specific.first.click()
                print("Clicked 'Pay Now'. Please approve the payment on your UPI app.")
                return

            # Strategy 2: Text match on page
            pay_btn_text = (
                self.page.locator("div, button").filter(has_text="Pay Now").last
            )
            if await pay_btn_text.count() > 0 and await pay_btn_text.is_visible():
                await pay_btn_text.click()
                print("Clicked 'Pay Now'. Please approve the payment on your UPI app.")
                return

            # Strategy 3: Check inside iframe
            iframe_element = await self.page.query_selector("#payment_widget")
            if iframe_element:
                frame = await iframe_element.content_frame()
                if frame:
                    frame_btn = frame.locator("text='Pay Now'")
                    if await frame_btn.count() > 0:
                        await frame_btn.first.click()
                        print("Clicked 'Pay Now' inside iframe.")
                        return

            print("Could not find 'Pay Now' button (timeout or not in DOM).")

        except Exception as e:
            print(f"Error clicking Pay Now: {e}")
