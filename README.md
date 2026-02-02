# Blinkit MCP Server

A Model Context Protocol (MCP) server that provides programmatic access to Blinkit's grocery shopping platform. Built with Node.js and Playwright for robust browser automation.

## Features

✅ **Authentication** - Login with phone number and OTP verification  
✅ **Product Search** - Search for products with detailed information  
✅ **Cart Management** - Add items to cart and view cart contents  
✅ **Checkout** - Place orders with Cash on Delivery (COD)  
✅ **Address Management** - View saved delivery addresses  

## Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
git clone https://github.com/ukrocks007/blinkit-mcp-improved.git
cd blinkit-mcp-improved
npm install
npx playwright install chromium
```

### Running the Server

The server runs in stdio mode for MCP clients:

```bash
npm start
# or
node src/index.js
```

### Testing

Test the server with the included test client:

```bash
npm test
# or
node src/test_client.js
```

## Available Tools

### 1. `login`
Start authentication by providing a phone number.

**Arguments:**
- `phoneNumber` (string): Indian phone number (10 digits)

**Returns:** Success message indicating OTP has been sent

### 2. `verify_otp`
Complete login by verifying the OTP received on your phone.

**Arguments:**
- `otp` (string): 4-digit OTP code

**Returns:** Authentication success confirmation

### 3. `search_products`
Search for products on Blinkit.

**Arguments:**
- `query` (string): Search term (e.g., "milk", "bread")
- `limit` (number, optional): Maximum results to return (default: 10)

**Returns:** Array of products with name, variant, price, and index

### 4. `add_to_cart`
Add a product to your cart by its index from search results.

**Arguments:**
- `productIndex` (number): Index of product from search results (0-based)
- `quantity` (number, optional): Quantity to add (default: 1)

**Returns:** Confirmation of item added to cart

### 5. `check_cart`
View current items in your cart.

**Returns:** Array of cart items with details and grand total

### 6. `get_addresses`
Get information about saved delivery addresses.

**Returns:** List of saved addresses with details

### 7. `place_order_cod`
Complete checkout and place order using Cash on Delivery.

**Arguments:**
- `addressIndex` (number, optional): Index of address to use (default: 0)

**Returns:** Order placement confirmation or error details

## Claude Desktop Integration

Add to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "blinkit": {
      "command": "node",
      "args": ["/absolute/path/to/blinkit-mcp-improved/src/index.js"]
    }
  }
}
```

After updating the config, restart Claude Desktop.

## Usage Example

```javascript
// In Claude Desktop or any MCP client:

// 1. Login
await login({ phoneNumber: "9876543210" });

// 2. Verify OTP (check your phone)
await verify_otp({ otp: "1234" });

// 3. Search for products
const products = await search_products({ query: "milk", limit: 10 });

// 4. Add first product to cart
await add_to_cart({ productIndex: 0, quantity: 2 });

// 5. Check cart
const cart = await check_cart();

// 6. View addresses
const addresses = await get_addresses();

// 7. Place order
await place_order_cod({ addressIndex: 0 });
```

## Technical Details

### Architecture

- **Language:** Node.js (requires 18+)
- **MCP SDK:** `@modelcontextprotocol/sdk`
- **Browser Automation:** Playwright
- **Transport:** stdio

### Session Management

- Browser sessions are automatically managed
- Cookies stored in `~/.blinkit_mcp/cookies/`
- One browser instance per server process
- Sessions persist across tool calls

### Selector Strategy

Uses resilient selectors designed to handle:
- Styled-components (class name hashing)
- Tailwind CSS utility classes
- Dynamic content loading
- Skeleton loaders

Combines:
- Partial class matching `[class*=""]`
- Structural attributes (`tabindex`, `role`, `id`)
- Text content `:has-text()`
- Fallback chains for robustness

### Error Handling

- COD minimum order validation
- Address selection verification
- Payment method enablement checks
- Graceful degradation with informative errors

## Troubleshooting

### "Session expired" errors
Re-run the `login` and `verify_otp` tools to establish a new session.

### Search returns no results
- Check if products appear in browser window
- Wait times are optimized but may need adjustment for slow connections
- Try more specific search terms

### COD order placement fails
- Verify address is selected correctly
- Check cart total meets COD minimum (usually ₹100-200)
- Ensure "Cash" payment panel expands and COD option is visible

### Browser doesn't close
Browser windows are kept open during server lifetime for session persistence. They close when the server stops.

### Browser not found
```bash
npx playwright install chromium
```

## Development

### Project Structure

```
blinkit-mcp-improved/
├── src/
│   ├── index.js           # MCP server implementation
│   ├── playwright_auth.js # Browser automation logic
│   └── test_client.js     # Test harness
├── package.json           # Dependencies
├── README.md              # This file
└── start.sh               # Launch script
```

### Key Files

- **src/index.js**: Implements MCP protocol, defines tools
- **src/playwright_auth.js**: All browser automation (authentication, search, cart, checkout)
- **src/test_client.js**: Standalone tester for debugging

### Running in Debug Mode

Edit `src/playwright_auth.js` to see the browser window:

```javascript
this.browser = await chromium.launch({
  headless: false  // Shows browser window
});
```

### Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector node src/index.js
```

### Adding New Features

1. Add method to `PlaywrightAuth` class in `src/playwright_auth.js`
2. Register new tool in `src/index.js` with schema
3. Test with `npm test`

## Security & Privacy

- **No data collection**: All interactions stay local
- **Session isolation**: Each server instance has its own browser profile
- **Credentials**: Phone number and OTP used only for Blinkit authentication
- **Local storage**: Cookies stored only in `~/.blinkit_mcp/cookies/`

## Limitations

- **COD only**: Currently supports Cash on Delivery payment method only
- **Single session**: One active browser session per server process
- **Manual OTP**: Requires user to enter OTP from phone
- **India only**: Works with Indian phone numbers and addresses

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test thoroughly (especially checkout flows)
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built with:
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Playwright](https://playwright.dev/)
- [Node.js](https://nodejs.org/)

---

**Note:** This is an unofficial tool and is not affiliated with, endorsed by, or connected to Blinkit/Zomato. Use responsibly and in accordance with Blinkit's Terms of Service.