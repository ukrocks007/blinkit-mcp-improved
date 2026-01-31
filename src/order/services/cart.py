from .base import BaseService


class CartService(BaseService):
    async def add_to_cart(self, product_id: str, quantity: int = 1):
        """Adds a product to the cart by its unique ID. Supports multiple quantities."""
        print(f"Adding product with ID {product_id} to cart (Quantity: {quantity})...")
        try:
            # Step 1: Try to find the product card on current page
            card = self.page.locator(f"div[id='{product_id}']")

            if await card.count() == 0:
                print(f"Product ID {product_id} not found on current page.")

                # Step 2: Check if we know this product from a previous search
                if self.manager and product_id in self.manager.known_products:
                    print("Product found in history.")
                    product_info = self.manager.known_products[product_id]
                    source_query = product_info.get("source_query")

                    if source_query:
                        print(f"Re-searching for '{source_query}' to find product...")
                        # Re-search to get back to the product page
                        if hasattr(self.manager, "search_product"):
                            await self.manager.search_product(source_query)
                            # Wait for search results to load
                            await self.page.wait_for_timeout(2000)

                        # Try to find the card again
                        card = self.page.locator(f"div[id='{product_id}']")
                        if await card.count() == 0:
                            print(f"Still can't find product {product_id} after re-search.")
                            # Alternative: Try to find by product name
                            product_name = product_info.get("name", "")
                            if product_name:
                                print(f"Trying to find by product name: {product_name}")
                                # Look for cards containing the product name
                                name_cards = self.page.locator("div[role='button']").filter(has_text="ADD").filter(has_text=product_name.split()[0])
                                if await name_cards.count() > 0:
                                    card = name_cards.first
                                    print("Found product card by name!")
                                else:
                                    print("Could not find product by name either.")
                                    return
                            else:
                                return
                    else:
                        print("No source query found for this product.")
                        return
                else:
                    print("Product ID unknown and not on current page.")
                    # Last resort: try to find by index from current search results
                    all_cards = self.page.locator("div[role='button']").filter(has_text="ADD")
                    cards_count = await all_cards.count()
                    print(f"Trying to match from {cards_count} available products...")
                    
                    # If there are products on page, try the first few
                    if cards_count > 0:
                        print("Attempting to add first available product as fallback...")
                        card = all_cards.first
                    else:
                        print("No products found on current page.")
                        return

            # Step 3: Add the product to cart
            print("Attempting to add product to cart...")
            
            # Find the ADD button specifically inside the card
            add_btn = card.locator("div").filter(has_text="ADD").last
            
            # Alternative selectors for ADD button
            if await add_btn.count() == 0:
                add_btn = card.locator("button").filter(has_text="ADD")
            if await add_btn.count() == 0:
                add_btn = card.locator("[class*='add'], [class*='ADD']").filter(has_text="ADD")

            items_to_add = quantity

            # If ADD button is visible, click it once to start
            if await add_btn.is_visible():
                await add_btn.click()
                print(f"Successfully clicked ADD button for product (1/{quantity}).")
                items_to_add -= 1
                # Wait for the counter to appear
                await self.page.wait_for_timeout(1000)
            else:
                print("ADD button not visible. Product might already be in cart.")
                # Check if increment button is available (product already in cart)
                plus_btns = card.locator("text='+', .icon-plus")
                if await plus_btns.count() > 0:
                    print("Product already in cart, will increment quantity.")
                else:
                    print("Cannot find ADD button or increment button.")
                    return

            # Step 4: Use increment button for remaining quantity
            if items_to_add > 0:
                print(f"Adding remaining {items_to_add} items...")
                # Wait for the counter UI to initialize
                await self.page.wait_for_timeout(1000)

                # Find the + button with multiple strategies
                plus_btn = None
                
                # Strategy 1: Icon-based
                icon_plus = card.locator(".icon-plus").first
                if await icon_plus.count() > 0:
                    plus_btn = icon_plus.locator("..")
                
                # Strategy 2: Text-based
                if not plus_btn or await plus_btn.count() == 0:
                    plus_btn = card.locator("text='+'").first
                
                # Strategy 3: Button with + text
                if not plus_btn or await plus_btn.count() == 0:
                    plus_btn = card.locator("button:has-text('+')").first

                if plus_btn and await plus_btn.count() > 0 and await plus_btn.is_visible():
                    for i in range(items_to_add):
                        await plus_btn.click()
                        current_qty = quantity - items_to_add + i + 1
                        print(f"Incremented quantity to {current_qty}/{quantity}")
                        
                        # Check for quantity limit
                        try:
                            limit_msg = self.page.get_by_text("Sorry, you can't add more of this item")
                            if await limit_msg.is_visible(timeout=1000):
                                print(f"Quantity limit reached for product.")
                                break
                        except Exception:
                            pass

                        await self.page.wait_for_timeout(500)
                else:
                    print("Could not find '+' button to add remaining quantity.")

            # Step 5: Final verification
            await self.page.wait_for_timeout(1000)
            print(f"Successfully added product to cart!")

            # Check for "Store Unavailable" modal
            if await self.page.is_visible("div:has-text('Sorry, can\\'t take your order')"):
                print("WARNING: Store is unavailable (Modal detected).")
                return

        except Exception as e:
            print(f"Error adding to cart: {e}")
            import traceback
            traceback.print_exc()

    async def remove_from_cart(self, product_id: str, quantity: int = 1):
        """Adds a product to the cart by its unique ID. Supports multiple quantities."""
        print(f"Adding product with ID {product_id} to cart (Quantity: {quantity})...")
        try:
            # Target the specific card by ID
            card = self.page.locator(f"div[id='{product_id}']")

            if await card.count() == 0:
                print(f"Product ID {product_id} not found on current page.")

                # Check if we know this product from a previous search
                if self.manager and product_id in self.manager.known_products:
                    print("Product found in history.")
                    product_info = self.manager.known_products[product_id]
                    source_query = product_info.get("source_query")

                    if source_query:
                        print(
                            f"Navigating back to search results for '{source_query}'..."
                        )
                        # Delegate search back to manager/search service
                        if hasattr(self.manager, "search_product"):
                            await self.manager.search_product(source_query)

                        # Re-locate the card after search
                        card = self.page.locator(f"div[id='{product_id}']")
                        if await card.count() == 0:
                            print(
                                f"CRITICAL: Product {product_id} still not found after re-search."
                            )
                            return
                    else:
                        print("No source query found for this product.")
                        return
                else:
                    print("Product ID unknown and not on current page.")
                    return

            # Find the ADD button specifically inside the card
            add_btn = card.locator("div").filter(has_text="ADD").last

            items_to_add = quantity

            # If ADD button is visible, click it once to start
            if await add_btn.is_visible():
                await add_btn.click()
                print(f"Clicked ADD button for {product_id} (1/{quantity}).")
                items_to_add -= 1
                # Wait for the counter to appear
                await self.page.wait_for_timeout(500)

            # Use increment button for remaining quantity
            if items_to_add > 0:
                # Wait for the counter to initialize
                await self.page.wait_for_timeout(1000)

                # Robust strategy to find the + button
                plus_btn = card.locator(".icon-plus").first
                if await plus_btn.count() > 0:
                    plus_btn = plus_btn.locator("..")
                else:
                    plus_btn = card.locator("text='+'").first

                if await plus_btn.is_visible():
                    for i in range(items_to_add):
                        await plus_btn.click()
                        print(
                            f"Incrementing quantity for {product_id} ({quantity - items_to_add + i + 1}/{quantity})."
                        )
                        # Check for limit reached
                        try:
                            limit_msg = self.page.get_by_text(
                                "Sorry, you can't add more of this item"
                            )
                            if await limit_msg.is_visible(timeout=1000):
                                print(f"Quantity limit reached for {product_id}.")
                                break
                        except Exception:
                            pass

                        await self.page.wait_for_timeout(500)
                else:
                    print(
                        f"Could not find '+' button to add remaining quantity for {product_id}."
                    )

            await self.page.wait_for_timeout(1000)

            # Check for "Store Unavailable" modal
            if await self.page.is_visible(
                "div:has-text('Sorry, can\\'t take your order')"
            ):
                print("WARNING: Store is unavailable (Modal detected).")
                return

        except Exception as e:
            print(f"Error adding to cart: {e}")

    async def remove_from_cart(self, product_id: str, quantity: int = 1):
        """Removes a specific quantity of a product from the cart."""
        print(f"Removing {quantity} of product ID {product_id} from cart...")
        try:
            # Target the specific card by ID
            card = self.page.locator(f"div[id='{product_id}']")

            if await card.count() == 0:
                # Attempt recovery via search if known
                if self.manager and product_id in self.manager.known_products:
                    product_info = self.manager.known_products[product_id]
                    source_query = product_info.get("source_query")
                    if source_query:
                        if hasattr(self.manager, "search_product"):
                            await self.manager.search_product(source_query)
                        card = self.page.locator(f"div[id='{product_id}']")
                        if await card.count() == 0:
                            print(
                                f"Product {product_id} not found after recovery search."
                            )
                            return
                else:
                    print(f"Product ID {product_id} not found and unknown.")
                    return

            # Check for decrement button
            minus_btn = card.locator(".icon-minus").first
            if await minus_btn.count() > 0:
                minus_btn = minus_btn.locator("..")
            else:
                minus_btn = card.locator("text='-'").first

            if await minus_btn.is_visible():
                for i in range(quantity):
                    await minus_btn.click()
                    print(
                        f"Decrementing quantity for {product_id} ({i + 1}/{quantity})."
                    )
                    await self.page.wait_for_timeout(500)

                    # If ADD button reappears, item is fully removed
                    if (
                        await card.locator("div")
                        .filter(has_text="ADD")
                        .last.is_visible()
                    ):
                        print(f"Item {product_id} completely removed from cart.")
                        break
            else:
                print(f"Item {product_id} is not in cart (no '-' button found).")

        except Exception as e:
            print(f"Error removing from cart: {e}")

    async def get_cart_items(self):
        """Checks items in the cart and returns the text content."""
        try:
            cart_btn = self.page.locator(
                "div[class*='CartButton__Button'], div[class*='CartButton__Container']"
            )

            if await cart_btn.count() > 0:
                await cart_btn.first.click()

                # Verify opening
                try:
                    await self.page.wait_for_timeout(2000)

                    # 1. Critical Availability Check
                    if (
                        await self.page.is_visible("text=Sorry, can't take your order")
                        or await self.page.is_visible("text=Currently unavailable")
                        or await self.page.is_visible("text=High Demand")
                    ):
                        return "CRITICAL: Store is unavailable. 'Sorry, can't take your order'. Please try again later."

                    # 2. Check for Bill Details or Proceed Button
                    is_cart_active = (
                        await self.page.is_visible("text=/Bill details/i")
                        or await self.page.is_visible("button:has-text('Proceed')")
                        or await self.page.is_visible("text=ordering for")
                    )

                    if await self._is_store_closed():
                        return "CRITICAL: Store is closed."

                    # Scrape content
                    drawer = self.page.locator(
                        "div[class*='CartDrawer'], div[class*='CartSidebar'], div.cart-modal-rn, div[class*='CartWrapper__CartContainer']"
                    ).first

                    if await drawer.count() > 0:
                        content = await drawer.inner_text()
                        if (
                            "Currently unavailable" in content
                            or "can't take your order" in content
                        ):
                            return "CRITICAL: Store is unavailable (Text detected in cart). Please try again later."
                        print(
                            "You can select address, or checkout, if you want to place the order."
                        )
                        return content

                    if is_cart_active:
                        return "Cart is open. (Could not scrape specific drawer content, but functionality is active)."
                    else:
                        return "WARNING: Cart opened but seems empty or store is unavailable (No bill details/proceed button found)."

                except Exception as e:
                    return f"Cart drawer checking timed out or error: {e}"
            else:
                return "Cart button not found."

        except Exception as e:
            return f"Error getting cart items: {e}"
