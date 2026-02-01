# Blinkit Node.js MCP Server

A fully browser-based Model Context Protocol (MCP) server for Blinkit that enables automated grocery shopping through Claude or any MCP client.

## Features

🔐 **Authentication**
- Login with phone number + OTP verification
- Session persistence across restarts

🛍️ **Shopping**
- Search for products
- Add items to cart
- View cart contents

💰 **Checkout**
- Select delivery address
- Place orders with Cash on Delivery (COD)

## Installation

```bash
cd src-node
npm install
npx playwright install chromium
```

## Quick Test

Test the MCP server to verify it's working:

```bash
node test_client.js
```

You should see all 7 tools listed successfully.

## Usage

### Standalone Mode

Start the server directly:

```bash
node index.js
```

The server communicates via stdio using the MCP protocol.

### With Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "blinkit": {
      "command": "node",
      "args": ["/Users/utkarshmehta/Uk/blinkit-mcp-improved/src-node/index.js"]
    }
  }
}
```

Restart Claude Desktop, and you'll see the Blinkit tools available.

## Available Tools

### 1. `login`
Start authentication with your phone number.

**Input:**
- `phoneNumber` (string): 10-digit Indian phone number

**Example:**
```
Use login tool with phoneNumber: "9168054254"
```

### 2. `verify_otp`
Complete login with the OTP received on your phone.

**Input:**
- `otp` (string): 4-digit OTP code

**Example:**
```
Use verify_otp tool with otp: "1234"
```

### 3. `search_products`
Search for products on Blinkit.

**Input:**
- `query` (string): Search term (e.g., "milk", "bread")
- `limit` (number, optional): Max results (default: 10)

**Example:**
```
Use search_products with query: "milk"
```

### 4. `add_to_cart`
Add a product to cart using its index from search results.

**Input:**
- `productIndex` (number): Index from search results (0-based)
- `quantity` (number, optional): Quantity to add (default: 1)

**Example:**
```
Use add_to_cart with productIndex: 0, quantity: 2
```

### 5. `check_cart`
View current items in your cart.

**Example:**
```
Use check_cart tool
```

### 6. `get_addresses`
Get information about saved delivery addresses.

**Example:**
```
Use get_addresses tool
```

### 7. `place_order_cod`
Complete checkout and place order with Cash on Delivery.

**Input:**
- `addressIndex` (number, optional): Address to use (default: 0 = first address)

**Example:**
```
Use place_order_cod with addressIndex: 0
```

## Complete Workflow Example

Using Claude Desktop or any MCP client:

1. **Login:**
   ```
   Use the login tool with my phone number 9168054254
   ```

2. **Verify OTP:**
   ```
   I received OTP 1234, verify it
   ```

3. **Search:**
   ```
   Search for milk products
   ```

4. **Add to Cart:**
   ```
   Add the first product to my cart
   ```

5. **Check Cart:**
   ```
   Show me what's in my cart
   ```

6. **Checkout:**
   ```
   Place the order using Cash on Delivery to my first address
   ```

## Browser Behavior

- **First run**: Browser opens in headless mode to perform actions
- **Headless**: Set to `true` by default (no visible browser window)
- **Debugging**: Set `this.headless = false` in `playwright_auth.js` to see the browser

## Session Management

Sessions are saved to `~/.blinkit_mcp/cookies/auth.json` after successful login. This allows:
- Persistent authentication across server restarts
- No need to re-login every time
- Automatic session restoration

## Troubleshooting

### Browser not found
```bash
npx playwright install chromium
```

### Login timeout
- Try setting `headless: false` to see what's happening
- Check your internet connection
- Verify phone number format (10 digits, no country code)

### Products not found
- Ensure you're logged in first
- Try different search terms
- Check if Blinkit is available in your area

### Order placement fails
- Verify you have items in cart
- Ensure delivery address is set up in your Blinkit account
- Check if store is open in your area

## Architecture

**Full Browser Automation** using Playwright:
- All operations use browser automation for maximum reliability
- Authenticates like a real user
- Works even if Blinkit changes their API
- Session cookies stored for persistence

**API Knowledge Retained:**
- `client.js` kept for future optimizations
- Can switch to API mode later if needed

## Development

### File Structure
```
src-node/
├── index.js              # Main MCP server
├── playwright_auth.js    # Browser automation module
├── client.js             # API client (for future reference)
├── test_client.js        # Test suite
└── package.json          # Dependencies
```

### Testing
```bash
# Quick test
node test_client.js

# Manual testing with MCP Inspector
npx @modelcontextprotocol/inspector node index.js
```

## License

See parent project LICENSE
