import { chromium } from 'playwright';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';

export class PlaywrightAuth {
    constructor() {
        this.sessionPath = path.join(os.homedir(), '.blinkit_mcp/cookies/auth.json');
        this.browser = null;
        this.context = null;
        this.page = null;
        this.headless = false; // Set to false for debugging
    }

    async startBrowser() {
        console.error('Starting browser...');
        this.browser = await chromium.launch({ headless: this.headless });

        // Check if session exists
        const sessionExists = await fs.access(this.sessionPath).then(() => true).catch(() => false);

        if (sessionExists) {
            console.error('Loading existing session...');
            const sessionData = await fs.readFile(this.sessionPath, 'utf8');
            this.context = await this.browser.newContext({
                storageState: JSON.parse(sessionData),
                permissions: ['geolocation'],
                geolocation: { latitude: 18.470896, longitude: 73.86407 } // Pune
            });
        } else {
            console.error('Starting fresh session...');
            this.context = await this.browser.newContext({
                permissions: ['geolocation'],
                geolocation: { latitude: 18.470896, longitude: 73.86407 }
            });
        }

        this.page = await this.context.newPage();
        await this.page.goto('https://blinkit.com/', { waitUntil: 'domcontentloaded', timeout: 60000 });
        console.error('Navigated to Blinkit.com');

        // Handle location popup if it appears
        try {
            const locationBtn = this.page.locator('button:has-text("Detect my location")');
            await locationBtn.waitFor({ state: 'visible', timeout: 3000 });
            await locationBtn.click();
            console.error('Clicked location detection button');
            await this.page.waitForTimeout(1000);
        } catch (e) {
            // Location popup didn't appear, continue
        }

        return true;
    }

    async login(phoneNumber) {
        console.error(`Logging in with phone number: ${phoneNumber}...`);

        try {
            // Ensure we're on homepage
            if (!this.page.url().includes('blinkit.com')) {
                await this.page.goto('https://blinkit.com/', { waitUntil: 'domcontentloaded' });
            }

            // Click Login button
            const loginBtn = this.page.locator('text="Login"').first();
            if (await loginBtn.isVisible({ timeout: 5000 })) {
                await loginBtn.click();
                console.error('Clicked Login button');
            } else {
                console.error('Login button not found, might already be on login screen');
            }

            // Wait for phone input
            const phoneInput = await this.page.waitForSelector(
                'input[type="tel"], input[name="mobile"], input[type="text"]',
                { state: 'visible', timeout: 10000 }
            );

            await phoneInput.click();
            await phoneInput.fill(phoneNumber);
            console.error('Filled phone number');

            // Submit phone number
            await this.page.waitForTimeout(500);

            // Try different submit buttons
            if (await this.page.isVisible('text="Continue"')) {
                await this.page.click('text="Continue"');
            } else if (await this.page.isVisible('text="Next"')) {
                await this.page.click('text="Next"');
            } else {
                await this.page.keyboard.press('Enter');
            }

            console.error('Submitted phone number, waiting for OTP screen...');
            await this.page.waitForTimeout(2000);

            return { success: true, message: 'Phone number submitted. Please provide OTP.' };
        } catch (error) {
            console.error(`Login error: ${error.message}`);
            return { success: false, error: error.message };
        }
    }

    async verifyOTP(otp) {
        console.error(`Verifying OTP: ${otp}...`);

        try {
            // Wait for OTP inputs
            await this.page.waitForSelector('input', { timeout: 10000 });

            const inputs = this.page.locator('input');
            const count = await inputs.count();

            if (count === 4) {
                // 4 separate inputs for each digit
                console.error('Detected 4-digit OTP inputs');
                for (let i = 0; i < 4; i++) {
                    await inputs.nth(i).fill(otp[i]);
                    await this.page.waitForTimeout(100);
                }
            } else {
                // Single input or different layout
                console.error(`Detected ${count} inputs, trying first relevant one`);
                const otpInput = this.page.locator(
                    'input[data-test-id="otp-input"], input[name*="otp"], input[id*="otp"]'
                ).first();

                if (await otpInput.isVisible()) {
                    await otpInput.fill(otp);
                } else {
                    await inputs.first().fill(otp);
                }
            }

            console.error('Entered OTP, submitting...');
            await this.page.keyboard.press('Enter');

            // Wait for navigation or success indicator
            await this.page.waitForTimeout(3000);

            // Check if logged in
            const loggedIn = await this.isLoggedIn();

            if (loggedIn) {
                await this.saveSession();
                return { success: true, message: 'Login successful! Session saved.' };
            } else {
                return { success: false, error: 'OTP verification might have failed. Please check.' };
            }
        } catch (error) {
            console.error(`OTP verification error: ${error.message}`);
            return { success: false, error: error.message };
        }
    }

    async isLoggedIn() {
        try {
            // Check for indicators of being logged in
            const loginVisible = await this.page.isVisible('text="Login"', { timeout: 2000 }).catch(() => false);

            if (!loginVisible) {
                // Login button not visible means likely logged in
                return true;
            }

            // Also check for user profile indicators
            const profileVisible = await this.page.isVisible('text="My Account"', { timeout: 2000 }).catch(() => false);

            return profileVisible;
        } catch (error) {
            return false;
        }
    }

    async saveSession() {
        try {
            const sessionDir = path.dirname(this.sessionPath);
            await fs.mkdir(sessionDir, { recursive: true });

            const storageState = await this.context.storageState();
            await fs.writeFile(this.sessionPath, JSON.stringify(storageState, null, 2));

            console.error(`Session saved to ${this.sessionPath}`);
            return true;
        } catch (error) {
            console.error(`Error saving session: ${error.message}`);
            return false;
        }
    }

    async searchProducts(query, limit = 20) {
        console.error(`Searching for: ${query}...`);

        try {
            // Navigate to homepage if not already there
            const currentUrl = this.page.url();
            if (!currentUrl.includes('blinkit.com') || currentUrl === 'https://blinkit.com/' || currentUrl.includes('blinkit.com/#')) {
                await this.page.goto('https://blinkit.com/', { waitUntil: 'domcontentloaded' });
                await this.page.waitForTimeout(2000);
            }

            // Click the search bar link to navigate to search page
            const searchBar = this.page.locator('a[href="/s/"]').first();
            if (await searchBar.isVisible({ timeout: 5000 })) {
                console.error('Clicking search bar to navigate to search page...');
                await searchBar.click();
                await this.page.waitForTimeout(2000);
            }

            // Now find the actual search input on the search page
            const searchInput = await this.page.waitForSelector(
                'input[class*="SearchBarContainer__Input"], input[placeholder*="atta"], input[placeholder*="Search"]',
                { state: 'visible', timeout: 10000 }
            );

            await searchInput.click();
            await searchInput.fill(query);
            console.error('Entering search query...');
            await this.page.keyboard.press('Enter');

            console.error('Search submitted, waiting for results to load...');

            // Wait for skeleton loaders to appear and then disappear
            // First wait a bit for the search to trigger
            await this.page.waitForTimeout(1000);

            // Wait for skeleton loaders to disappear (they have "Shimmer" in class name)
            try {
                await this.page.waitForSelector('div[class*="Shimmer"]', { state: 'visible', timeout: 3000 }).catch(() => { });
                console.error('Skeleton loaders appeared, waiting for them to disappear...');
                await this.page.waitForSelector('div[class*="Shimmer"]', { state: 'hidden', timeout: 10000 }).catch(() => { });
            } catch (e) {
                console.error('No skeleton loaders found or they disappeared already');
            }

            // Wait for actual product cards to appear with Tailwind structure
            try {
                await this.page.waitForSelector('div[tabindex="0"][role="button"][id]', { state: 'visible', timeout: 5000 });
                console.error('Product cards loaded');
            } catch (e) {
                console.error('Timeout waiting for product cards, proceeding anyway...');
            }

            // Additional wait to ensure products are fully rendered
            await this.page.waitForTimeout(2000);

            // Extract product information
            const products = [];

            // Look for product cards - try multiple selectors
            let productCards = this.page.locator('div[tabindex="0"][role="button"][id]');

            // Fallback selectors
            if (await productCards.count() === 0) {
                productCards = this.page.locator('div[class*="Product__"]');
            }
            if (await productCards.count() === 0) {
                productCards = this.page.locator('div[class*="plp-product"]');
            }
            if (await productCards.count() === 0) {
                productCards = this.page.locator('a[href*="/p/"], a[href*="/product/"]');
            }

            const count = Math.min(await productCards.count(), limit);
            console.error(`Found ${count} product cards`);

            for (let i = 0; i < count; i++) {
                try {
                    const card = productCards.nth(i);

                    // Get all text from the card
                    const allText = await card.innerText().catch(() => '');
                    const lines = allText.split('\n').filter(l => l.trim());

                    // First non-empty line is usually the product name
                    const name = lines[0] || 'Unknown Product';

                    // Find price (line containing ₹)
                    const priceLine = lines.find(l => l.includes('₹')) || '₹0';

                    products.push({
                        id: `product_${i}`,
                        name: name,
                        price: priceLine,
                        index: i
                    });
                } catch (e) {
                    console.error(`Error extracting product ${i}: ${e.message}`);
                }
            }

            console.error(`Extracted ${products.length} products`);
            return products;
        } catch (error) {
            console.error(`Search error: ${error.message}`);
            throw error;
        }
    }

    async addToCart(productIndex, quantity = 1) {
        console.error(`Adding product at index ${productIndex} to cart...`);

        try {
            // Find product cards - now using Tailwind structure
            // Product cards have tabindex="0" role="button" with an id
            let productCards = this.page.locator('div[tabindex="0"][role="button"][id]');

            // Fallback to class-based selectors
            if (await productCards.count() === 0) {
                productCards = this.page.locator('div[class*="Product__"], div[class*="plp-product"]');
            }

            if (await productCards.count() > productIndex) {
                const card = productCards.nth(productIndex);

                // Look for ADD button - it has "ADD" text and green styling
                const addBtn = card.locator('div:has-text("ADD")[role="button"], button:has-text("ADD")').first();

                if (await addBtn.isVisible({ timeout: 3000 })) {
                    await addBtn.click();
                    console.error('Clicked Add button');
                    await this.page.waitForTimeout(1000);

                    // If quantity > 1, click + button to increase quantity
                    if (quantity > 1) {
                        for (let i = 1; i < quantity; i++) {
                            const plusBtn = card.locator('div:has-text("+")[role="button"], button:has-text("+")').first();
                            if (await plusBtn.isVisible({ timeout: 2000 })) {
                                await plusBtn.click();
                                await this.page.waitForTimeout(500);
                            }
                        }
                    }

                    return { success: true, message: `Added product to cart (quantity: ${quantity})` };
                } else {
                    return { success: false, error: 'Add button not found for this product' };
                }
            } else {
                return { success: false, error: `Product index ${productIndex} not found` };
            }
        } catch (error) {
            console.error(`Add to cart error: ${error.message}`);
            return { success: false, error: error.message };
        }
    }

    async getCart() {
        console.error('Getting cart contents...');

        try {
            // Check if cart modal is already open
            const cartModalOpen = await this.page.isVisible('div.cart-modal-rn', { timeout: 2000 }).catch(() => false);

            if (!cartModalOpen) {
                // Click on cart button to open cart drawer
                const cartBtn = this.page.locator('div[class*="CartButton__"]').first();
                await cartBtn.click();
                console.error('Opened cart');
                await this.page.waitForTimeout(2000);
            } else {
                console.error('Cart modal already open');
            }

            // Get reference to cart modal container to scope all queries
            const cartModal = this.page.locator('div.cart-modal-rn').first();

            // Verify cart modal is visible
            if (!await cartModal.isVisible()) {
                throw new Error('Cart modal not found or not visible');
            }

            // Extract cart items - scoped within cart modal only
            const items = [];

            // Cart items are in CartProduct__Container with DefaultProductCard inside
            const cartItems = cartModal.locator('div[class*="CartProduct__"], div[class*="DefaultProductCard__Container"]');
            const count = await cartItems.count();
            console.error(`Found ${count} cart item containers`);

            for (let i = 0; i < count; i++) {
                try {
                    const item = cartItems.nth(i);

                    // Product title is in DefaultProductCard__ProductTitle
                    const nameEl = item.locator('div[class*="ProductTitle"]');
                    const name = await nameEl.innerText().catch(() => 'Unknown Product');

                    // Variant/size info
                    const variantEl = item.locator('div[class*="ProductVariant"]');
                    const variant = await variantEl.innerText().catch(() => '');

                    // Price is in DefaultProductCard__Price
                    const priceEl = item.locator('div[class*="Price"]:has-text("₹")');
                    const price = await priceEl.innerText().catch(() => '₹0');

                    // Quantity from AddToCart component (between minus and plus buttons)
                    const quantityEl = item.locator('div[class*="AddToCart__UpdatedButtonContainer"]');
                    let quantity = '1';
                    if (await quantityEl.count() > 0) {
                        const qtyText = await quantityEl.innerText().catch(() => '1');
                        // Extract just the number from the text
                        const qtyMatch = qtyText.match(/\d+/);
                        quantity = qtyMatch ? qtyMatch[0] : '1';
                    }

                    items.push({
                        name: name.trim(),
                        variant: variant.trim(),
                        quantity: quantity,
                        price: price.trim()
                    });
                } catch (e) {
                    console.error(`Error extracting cart item ${i}: ${e.message}`);
                }
            }

            // Get total from BillCard - look for "Grand total" within cart modal
            let total = 'Total unavailable';
            const grandTotalEl = cartModal.locator('div:has-text("Grand total")').last();
            if (await grandTotalEl.count() > 0) {
                // Get the price element next to "Grand total"
                const totalPriceEl = cartModal.locator('div[class*="BillItemRight"] div:has-text("₹")').last();
                total = await totalPriceEl.innerText().catch(() => 'Total unavailable');
            }

            console.error(`Cart has ${items.length} items`);
            return { items, total };
        } catch (error) {
            console.error(`Get cart error: ${error.message}`);
            throw error;
        }
    }

    async getAddresses() {
        console.error('Getting saved addresses...');

        try {
            // Navigate to account/addresses if needed
            // For now, addresses will be visible during checkout
            return { message: 'Addresses will be shown during checkout. Call place_order_cod to proceed.' };
        } catch (error) {
            console.error(`Get addresses error: ${error.message}`);
            throw error;
        }
    }

    async placeOrderCOD(addressIndex = 0) {
        console.error('Starting COD checkout process...');

        try {
            // Step 1: Open cart modal if not already open
            // Check if cart is already open
            const cartModalOpen = await this.page.isVisible('div.cart-modal-rn', { timeout: 2000 }).catch(() => false);

            if (!cartModalOpen) {
                const cartBtn = this.page.locator('div[class*="CartButton__"]').first();
                await cartBtn.click();
                console.error('Opened cart modal');
                await this.page.waitForTimeout(2000);
            } else {
                console.error('Cart modal already open');
            }

            // Step 2: Click Proceed button in the checkout strip
            // The Proceed button is in CheckoutStrip with tabindex and has "Proceed" text
            const proceedBtn = this.page.locator(
                'div[class*="CheckoutStrip__"][tabindex="0"]:has-text("Proceed")'
            ).first();

            if (await proceedBtn.isVisible({ timeout: 3000 })) {
                await proceedBtn.click();
                console.error('Clicked Proceed to checkout');
                await this.page.waitForTimeout(3000);
            } else {
                return { success: false, error: 'Proceed button not found. Cart might be empty.' };
            }

            // Step 3: Select delivery address
            await this.page.waitForTimeout(2000);

            // Look for address items in the AddressList
            // Address items are in AddressList__AddressItemWrapper
            let addressCards = this.page.locator('div[class*="AddressList__AddressItemWrapper"]');

            // Fallback to other possible selectors
            if (await addressCards.count() === 0) {
                addressCards = this.page.locator('div[role="button"]:has-text("Home"), div[role="button"]:has-text("Work"), div[role="button"]:has-text("Other")');
            }
            if (await addressCards.count() === 0) {
                addressCards = this.page.locator('div[class*="Address"][role="button"]');
            }

            const addressCount = await addressCards.count();
            console.error(`Found ${addressCount} addresses`);

            if (addressCount > addressIndex) {
                await addressCards.nth(addressIndex).click();
                console.error(`Selected address ${addressIndex}`);
                await this.page.waitForTimeout(3000);

                // Address selection might auto-proceed, check if we're on payment page
                const onPaymentPage = await this.page.isVisible('text="Cash on Delivery"', { timeout: 3000 }).catch(() => false);

                if (onPaymentPage) {
                    console.error('Auto-proceeded to payment page');
                } else {
                    // Click Continue/Proceed button after address selection if needed
                    const continueBtn = this.page.locator(
                        'button:has-text("Continue"), button:has-text("Proceed"), div[role="button"]:has-text("Continue")'
                    ).first();

                    if (await continueBtn.isVisible({ timeout: 3000 })) {
                        await continueBtn.click();
                        console.error('Clicked Continue after address');
                        await this.page.waitForTimeout(2000);
                    }
                }
            } else if (addressCount === 0) {
                console.error('No addresses found, attempting to continue anyway...');
                // Try to continue even without selecting address
                const continueBtn = this.page.locator(
                    'button:has-text("Continue"), button:has-text("Proceed"), div[role="button"]:has-text("Continue")'
                ).first();

                if (await continueBtn.isVisible({ timeout: 3000 })) {
                    await continueBtn.click();
                    await this.page.waitForTimeout(2000);
                }
            } else {
                return { success: false, error: `Address index ${addressIndex} not found (only ${addressCount} addresses available)` };
            }

            // Step 4: Click "Proceed To Pay" button after address is confirmed
            await this.page.waitForTimeout(2000);

            // After address selection, the cart shows "Proceed To Pay" button
            const proceedToPayBtn = this.page.locator(
                'div[class*="CheckoutStrip__"][tabindex="0"]:has-text("Proceed To Pay"), div:has-text("Proceed To Pay")'
            ).first();

            if (await proceedToPayBtn.isVisible({ timeout: 3000 })) {
                await proceedToPayBtn.click();
                console.error('Clicked Proceed To Pay button');
                await this.page.waitForTimeout(3000);
            } else {
                console.error('Proceed To Pay button not found, continuing anyway...');
            }

            // Step 5: Select COD payment method
            await this.page.waitForTimeout(2000);

            // First, click on the "Cash" panel to expand it
            const cashPanelSelectors = [
                'div[title="Cash"]',
                'div[aria-label="Cash"]',
                'div[role="button"]:has-text("Cash")',
                'h5:has-text("Cash")'
            ];

            let cashPanelClicked = false;
            for (const selector of cashPanelSelectors) {
                const cashPanel = this.page.locator(selector);
                if (await cashPanel.count() > 0 && await cashPanel.isVisible()) {
                    await cashPanel.first().click();
                    console.error('Clicked Cash payment panel');
                    await this.page.waitForTimeout(2000);
                    cashPanelClicked = true;
                    break;
                }
            }

            if (!cashPanelClicked) {
                console.error('Cash panel not found, looking for COD option directly...');
            }

            // Now look for the Cash on Delivery option within the expanded panel
            const codSelectors = [
                'text="Cash on Delivery"',
                'text="COD"',
                'div:has-text("Cash on Delivery")',
                'div:has-text("Pay on Delivery")',
                'label:has-text("Cash on Delivery")',
                'p:has-text("Cash on Delivery")'
            ];

            let codSelected = false;
            for (const selector of codSelectors) {
                const codOption = this.page.locator(selector);
                if (await codOption.count() > 0) {
                    await codOption.first().click();
                    console.error('Selected Cash on Delivery');
                    await this.page.waitForTimeout(1000);
                    codSelected = true;
                    break;
                }
            }

            if (!codSelected) {
                console.error('COD option not found in Cash panel, checking if it\'s pre-selected...');
                // COD might already be selected, try to proceed anyway
            }

            // Check for COD restriction messages
            await this.page.waitForTimeout(1500);
            const codErrorMessages = [
                'Cash on delivery is not applicable on orders with item total less than',
                'COD is not available for this order',
                'Cash on Delivery not available'
            ];

            for (const errorMsg of codErrorMessages) {
                const errorEl = this.page.locator(`text="${errorMsg}"`);
                if (await errorEl.count() > 0 && await errorEl.isVisible()) {
                    const fullErrorText = await errorEl.innerText().catch(() => errorMsg);
                    console.error(`COD restriction: ${fullErrorText}`);
                    return {
                        success: false,
                        error: `Cash on Delivery not available for this order. ${fullErrorText}`
                    };
                }
            }


            // Step 6: Click "Pay Now" button after selecting Cash/COD
            await this.page.waitForTimeout(2000);

            const payNowSelectors = [
                'div[class*="Zpayments__Button"]:has-text("Pay Now")',
                'button:has-text("Pay Now")',
                'div:has-text("Pay Now")'
            ];

            let payNowClicked = false;
            for (const selector of payNowSelectors) {
                const payNowBtn = this.page.locator(selector);
                if (await payNowBtn.count() > 0 && await payNowBtn.isVisible()) {
                    await payNowBtn.click();
                    console.error('Clicked Pay Now button');
                    await this.page.waitForTimeout(3000);
                    payNowClicked = true;
                    break;
                }
            }

            if (!payNowClicked) {
                console.error('Pay Now button not found, looking for final confirmation button...');
            }

            // Step 7: Final order confirmation
            // After Pay Now, there might be another confirmation step
            await this.page.waitForTimeout(2000);

            const placeOrderButtons = [
                'div[class*="CheckoutStrip__"][tabindex="0"]:has-text("Proceed To Pay")',
                'div[class*="CheckoutStrip__"]:has-text("Proceed")',
                'button:has-text("Proceed To Pay")',
                'button:has-text("Place Order")',
                'button:has-text("Confirm Order")',
                'button:has-text("Order Now")',
                'div[role="button"]:has-text("Place Order")',
                'div[class*="PlaceOrder"]'
            ];

            for (const btnSelector of placeOrderButtons) {
                const btn = this.page.locator(btnSelector).first();
                if (await btn.count() > 0 && await btn.isVisible()) {
                    await btn.click();
                    console.error('Clicked final order confirmation button! 🎉');
                    await this.page.waitForTimeout(3000);
                    return { success: true, message: 'Order placed successfully with Cash on Delivery!' };
                }
            }

            // If no button found, the order might have been placed already
            console.error('No final confirmation button found, checking if order was placed...');
            return { success: true, message: 'Order likely placed (no confirmation button needed)' };
        } catch (error) {
            console.error(`COD checkout error: ${error.message}`);
            return { success: false, error: error.message };
        }
    }

    async close() {
        if (this.browser) {
            await this.browser.close();
            console.error('Browser closed');
        }
    }
}
