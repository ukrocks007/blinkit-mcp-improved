from playwright.sync_api import Page


class BlinkitOrder:
    def __init__(self, page: Page):
        self.page = page

    def search_product(self, product_name: str):
        """Searches for a product using the search bar."""
        print(f"Searching for item: {product_name}...")
        try:
            # 1. Activate Search
            if self.page.is_visible("a[href='/s/']"):
                self.page.click("a[href='/s/']")
            elif self.page.is_visible("div[class*='SearchBar__PlaceholderContainer']"):
                self.page.click("div[class*='SearchBar__PlaceholderContainer']")
            else:
                # Fallback: type directly if input is visible, or click generic search text
                if self.page.is_visible("input[placeholder*='Search']"):
                    self.page.click("input[placeholder*='Search']")
                else:
                    self.page.click("text='Search'", timeout=3000)

            # 2. Type and Submit
            search_input = self.page.wait_for_selector(
                "input[placeholder*='Search'], input[type='text']",
                state="visible",
                timeout=5000,
            )
            search_input.fill(product_name)
            self.page.keyboard.press("Enter")

            # 3. Wait for results
            print("Waiting for results...")
            try:
                # Wait for product cards (divs with role button that act as products)
                # The provided HTML shows products have class structure or role='button' and contain 'ADD'
                self.page.wait_for_selector(
                    "div[role='button']:has-text('ADD')", timeout=10000
                )
                print("Search results loaded.")
            except Exception:
                print(
                    "Timed out waiting for product cards. Checking for 'No results'..."
                )
                if self.page.is_visible("text='No results found'"):
                    print("No results found for this query.")
                else:
                    print("Could not detect standard product cards.")

        except Exception as e:
            print(f"Error during search: {e}")

    def get_search_results(self, limit=5):
        """Parses search results and returns a list of product details."""
        results = []
        try:
            # Locate product cards: div[role='button'] that contains a price symbol (₹) and 'ADD' button area
            # We filter by "₹" to avoid matching the "ADD" button itself, which is also a div[role='button']
            cards = (
                self.page.locator("div[role='button']")
                .filter(has_text="ADD")
                .filter(has_text="₹")
            )

            count = cards.count()
            print(f"Found {count} product cards.")

            for i in range(min(count, limit)):
                card = cards.nth(i)
                text_content = card.inner_text()

                # Extract Name (usually specifically in a line-clamp div)
                name_locator = card.locator("div[class*='line-clamp-2']")
                if name_locator.count() > 0:
                    name = name_locator.first.inner_text()
                else:
                    # Fallback: split text
                    lines = [line for line in text_content.split("\n") if line.strip()]
                    name = lines[0] if lines else "Unknown Product"

                # Extract Price
                price = "Unknown Price"
                if "₹" in text_content:
                    # Find the line with ₹
                    for part in text_content.split("\n"):
                        if "₹" in part:
                            price = part.strip()
                            break

                results.append({"index": i, "name": name, "price": price})

        except Exception as e:
            print(f"Error extracting search results: {e}")

        return results

    def add_to_cart(self, item_index: int = 0):
        """Adds the Nth item from search results to the cart."""
        print(f"Adding item at index {item_index} to cart...")
        try:
            # Use the same locator strategy as get_search_results to ensure index alignment
            cards = (
                self.page.locator("div[role='button']")
                .filter(has_text="ADD")
                .filter(has_text="₹")
            )

            if cards.count() <= item_index:
                print(
                    f"Item index {item_index} out of range (found {cards.count()} items)."
                )
                return

            card = cards.nth(item_index)

            # Find the ADD button specifically inside the card
            # It's usually a div with text "ADD"
            add_btn = card.locator("div").filter(has_text="ADD").last

            if add_btn.is_visible():
                add_btn.click()
                print("Clicked ADD button.")
            else:
                # Check for checkmark/counter indicating already added
                if card.locator("text='+'").is_visible():
                    print("Item already in cart. Incrementing...")
                    card.locator("text='+'").click()
                else:
                    print("Could not find ADD button or increment controls.")

            self.page.wait_for_timeout(1000)

            # Check for "Store Unavailable" modal
            if self.page.is_visible("div:has-text('Sorry, can\\'t take your order')"):
                print("WARNING: Store is unavailable (Modal detected).")
                return

        except Exception as e:
            print(f"Error adding to cart: {e}")

    def get_saved_addresses(self):
        """Scrapes saved addresses from the selection modal."""
        print("Checking for address selection modal...")
        try:
            # Wait for modal or text
            if not self.page.is_visible("text='Select delivery address'"):
                print("Address selection modal not visible.")
                return []

            print("Address modal detected. Parsing addresses...")
            # Use specific class part or flexible selector
            address_items = self.page.locator(
                "div[class*='AddressList__AddressItemWrapper']"
            )
            count = address_items.count()

            addresses = []
            for i in range(count):
                item = address_items.nth(i)
                # Parse label (Home, Work, etc)
                label_el = item.locator("div[class*='AddressList__AddressLabel']")
                label = label_el.inner_text() if label_el.count() > 0 else "Unknown"

                # Parse details
                details_el = item.locator(
                    "div[class*='AddressList__AddressDetails']"
                ).last
                details = details_el.inner_text() if details_el.count() > 0 else ""

                addresses.append({"index": i, "label": label, "details": details})
            return addresses

        except Exception as e:
            print(f"Error getting addresses: {e}")
            return []

    def select_address(self, index: int):
        """Selects an address by index."""
        try:
            items = self.page.locator("div[class*='AddressList__AddressItemWrapper']")
            if index < items.count():
                print(f"Selecting address at index {index}...")
                items.nth(index).click()
                # Wait for modal to close or location to update
                self.page.wait_for_timeout(2000)
            else:
                print(f"Invalid address index: {index}")
        except Exception as e:
            print(f"Error selecting address: {e}")

    def get_cart_items(self):
        """Checks items in the cart."""
        print("Checking cart...")
        try:
            cart_btn = self.page.locator(
                "div[class*='CartButton__Button'], div[class*='CartButton__Container']"
            )

            if cart_btn.count() > 0:
                cart_btn.first.click()
                print("Clicked My Cart.")

                # Verify opening
                try:
                    # Check for modal first
                    if self.page.is_visible(
                        "div:has-text('Sorry, can\\'t take your order')"
                    ):
                        print(
                            "WARNING: Store is unavailable (Modal detected). Cannot view cart."
                        )
                        return

                    # Checking for common elements inside the cart sidebar
                    # Use a regex or case-insensitive text match for Bill Details
                    self.page.wait_for_selector("text=/Bill details/i", timeout=5000)
                    print("Cart drawer confirmed open.")
                except:
                    print(
                        "Cart drawer checking timed out. Might be empty, blocked by modal, or verifying Proceed button."
                    )
            else:
                print("Cart button not found.")

        except Exception as e:
            print(f"Error getting cart items: {e}")

    def place_order(self):
        """Proceeds to checkout."""
        print("Proceeding to Place Order...")
        try:
            # "Proceed" button logic
            proceed_btn = (
                self.page.locator("button, div").filter(has_text="Proceed").last
            )

            if proceed_btn.is_visible():
                proceed_btn.click()
                print("Clicked Proceed.")
                self.page.wait_for_timeout(3000)
            else:
                print("Proceed button not visible.")

        except Exception as e:
            print(f"Error placing order: {e}")
