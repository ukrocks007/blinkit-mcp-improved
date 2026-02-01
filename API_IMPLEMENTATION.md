# Blinkit MCP Server - Implementation Documentation

## Overview

This document provides technical details about the Blinkit MCP Server implementation.

## Architecture

### Components

1. **MCP Server** (`src/index.js`)
   - Implements Model Context Protocol
   - Defines 7 tools for Blinkit interaction
   - Manages PlaywrightAuth instance lifecycle
   - Handles stdio communication

2. **Browser Automation** (`src/playwright_auth.js`)
   - Playwright-based browser automation
   - Session management and cookie persistence
   - All Blinkit interactions (login, search, cart, checkout)
   - Resilient selector strategies

3. **Test Client** (`src/test_client.js`)
   - Standalone testing tool
   - MCP protocol validation
   - Development/debugging aid

### Tool Implementation

Each MCP tool follows this pattern:

```javascript
{
  name: "tool_name",
  description: "What the tool does",
  inputSchema: {
    type: "object",
    properties: {
      param1: { type: "string", description: "..." }
    },
    required: ["param1"]
  }
}
```

When called, tools invoke methods on the `PlaywrightAuth` instance which handles all browser automation.

## Selector Strategy

### Challenge

Blinkit uses a mix of:
- Styled-components (hashed class names like `sc-abcd1234-0`)
- Tailwind CSS (utility classes like `tw-text-300`)
- Dynamic content loading
- Skeleton loaders during data fetching

### Solution

Multi-layered selector approach:

1. **Primary Selectors**: Use specific structural attributes
   ```javascript
   'div[tabindex="0"][role="button"][id]'
   'div[class*="CheckoutStrip__"][tabindex="0"]'
   ```

2. **Partial Class Matching**: Resilient to class name changes
   ```javascript
   'div[class*="CartProduct__"]'
   'div[class*="Shimmer"]'
   ```

3. **Text Content**: When structure is stable
   ```javascript
   ':has-text("Proceed To Pay")'
   'div:has-text("Grand total")'
   ```

4. **Fallback Chains**: Try multiple approaches
   ```javascript
   const selectors = [
     'div[class*="specific"]',
     'div[role="button"]',
     'div:has-text("fallback")'
   ];
   for (const selector of selectors) {
     if (await element.locator(selector).count() > 0) {
       // Found it!
     }
   }
   ```

## Wait Strategies

### Search Results

Uses `Promise.race` to proceed as soon as products appear:

```javascript
await Promise.race([
  page.waitForSelector('div[tabindex="0"][role="button"][id]', { timeout: 8000 }),
  page.waitForSelector('div[class*="Shimmer"]', { state: 'hidden', timeout: 5000 })
]);
```

This ensures fastest possible response while still being reliable.

### Payment Flow

Critical to wait for button enablement:

```javascript
const payNowBtn = page.locator('div[class*="Zpayments__Button"]').first();

// Poll disabled attribute
let isDisabled = true;
while (isDisabled && attempts < 10) {
  const disabled = await payNowBtn.getAttribute('disabled');
  if (disabled === null) {
    isDisabled = false;
  } else {
    await page.waitForTimeout(1000);
    attempts++;
  }
}
```

## Error Handling

### COD Restrictions

Detects minimum order value errors:

```javascript
const errorMessages = [
  'Cash on delivery is not applicable on orders with item total less than',
  'COD is not available for this order'
];

for (const errorMsg of errorMessages) {
  const errorEl = page.locator(`text="${errorMsg}"`);
  if (await errorEl.isVisible()) {
    return { success: false, error: fullErrorText };
  }
}
```

### Graceful Degradation

- Fallback selectors if primary fails
- Informative error messages to user
- State recovery where possible

## Session Management

### Browser Lifecycle

- One Chromium instance per server process
- Persistent across tool calls
- Browser context stored in `~/.blinkit_mcp/cookies/`
- Automatic cleanup on server shutdown

### Authentication State

1. `login()` - Opens login page, enters phone number
2. `verify_otp()` - Completes authentication, saves session
3. Subsequent calls - Use saved cookies, no re-login needed

### Session Persistence

Cookies stored in:
```
~/.blinkit_mcp/cookies/blinkit_session.json
```

Contains:
- Authentication tokens
- Session identifiers
- Cart state (server-side on Blinkit)

## Checkout Flow

Complete order placement sequence:

```
1. Cart → Click "View Cart"
2. Cart Modal → Click "Proceed" 
3. Address Selection → Select delivery address
4. Address Confirmed → Click "Proceed To Pay"
5. Payment Page → Expand "Cash" panel
6. Cash Panel → Select "Cash on Delivery" option
7. Wait for "Pay Now" button to become enabled
8. Click "Pay Now" button
9. Final Confirmation → Click "Proceed To Pay" (if present)
10. Order Placed ✓
```

Each step has:
- Specific selectors
- Wait conditions
- Error detection
- Fallback strategies

## Performance Optimizations

1. **Parallel waiting**: `Promise.race` for multiple conditions
2. **Minimal timeouts**: Only wait as long as necessary
3. **Smart polling**: Check button state efficiently
4. **Scoped queries**: Limit selectors to specific containers

## Known Limitations

1. **No UPI/Card support**: Only COD implemented (other payment methods require complex flows)
2. **Single browser instance**: One session per server
3. **Manual OTP entry**: No SMS integration
4. **India-specific**: Phone number and address formats

## Future Enhancements

Potential additions:

- [ ] UPI payment support
- [ ] Cart modification (remove/update qty)
- [ ] Order history retrieval
- [ ] Favorite products management
- [ ] Search filters (category, price range)
- [ ] Multiple delivery slots
- [ ] Scheduled orders

## Testing

### Unit Testing

Run test client:
```bash
node src/test_client.js
```

Tests:
- Server initialization
- Tool registration
- Stdio communication

### Integration Testing

Manual test sequence:
1. Start server
2. Connect MCP client
3. Execute full flow (login → search → cart → checkout)
4. Verify order confirmation

### Debug Mode

Enable browser visibility:

```javascript
// In src/playwright_auth.js
const browser = await chromium.launch({
  headless: false,  // Change to false
  // ...
});
```

Watch automation in real-time.

## Maintenance

### Updating Selectors

When Blinkit updates UI:

1. Run with `headless: false`
2. Identify failing selector
3. Inspect element in DevTools
4. Update selector in `playwright_auth.js`
5. Add fallback for robustness
6. Test thoroughly

### Monitoring API Changes

Blinkit may change:
- URL structure
- Form fields
- Button text
- Page flow

Monitor error logs and update accordingly.

## Security Considerations

1. **Credentials**: Never log phone numbers or OTPs
2. **Session tokens**: Stored locally, never transmitted
3. **Network**: All requests go directly to Blinkit (no proxy)
4. **Data**: No analytics or tracking
5. **Isolation**: Each user has separate browser profile

---

Last Updated: 2026-02-02