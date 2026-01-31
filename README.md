# Blinkit MCP Server - Enhanced Edition 🛒

An improved Model Context Protocol (MCP) server for automating Blinkit grocery orders with enhanced cart functionality, robust checkout flow, and automated ordering capabilities.

## 🚀 Key Improvements

This enhanced version includes major fixes and improvements over the original:

### ✅ **Fixed Cart Functionality**
- **Robust Product Detection**: Enhanced product ID matching and fallback strategies
- **Re-search Capability**: Automatically re-searches when products aren't found
- **Multiple ADD Button Strategies**: Uses various selectors to find and click ADD buttons
- **Smart Error Handling**: Graceful fallbacks when cart operations fail

### ✅ **Enhanced Checkout Flow**
- **Address Selection**: Automated address detection and selection
- **COD Support**: Cash on Delivery payment method selection
- **Step-by-Step Checkout**: Proper handling of checkout state transitions
- **Order Completion**: Full end-to-end order placement

### ✅ **New Tools Added**
- `search_and_add_to_cart`: Search and immediately add products to cart
- `complete_order_flow`: Full automation from search to order placement
- `get_addresses`: Get saved delivery addresses
- `select_address`: Select delivery address by index
- `select_cod`: Select Cash on Delivery payment
- `place_cod_order`: Complete the order with COD

### ✅ **Improved Session Management**
- **File-based OTP System**: Real-time OTP coordination using file system
- **Session Persistence**: Reliable browser state saving and loading
- **Login Status Tracking**: Better authentication state management

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- uv (Python package manager)
- Firefox browser (for Playwright)

### Setup
```bash
# Clone the repository
git clone https://github.com/ukrocks007/blinkit-mcp-improved.git
cd blinkit-mcp-improved

# Install dependencies
uv sync

# Install Firefox for Playwright
uv run playwright install firefox

# Configure with mcporter
mcporter add blinkit /path/to/blinkit-mcp-improved/main.py --stdio
```

## 📱 Usage

### Authentication
```bash
# Login with OTP (phone number: your 10-digit number)
mcporter call blinkit.login_prepare_and_wait --args '{"phone_number": "9168054254"}'

# When you receive OTP via SMS/call, create the OTP file:
echo "1234" > /tmp/blinkit_otp.txt

# Check login status
mcporter call blinkit.check_login
```

### Quick Order (Recommended)
```bash
# Complete end-to-end order in one command
mcporter call blinkit.complete_order_flow --args '{"query": "davidoff decaf coffee", "item_index": 0, "address_index": 0}'
```

### Step-by-Step Order
```bash
# 1. Search for products
mcporter call blinkit.search --args '{"query": "milk"}'

# 2. Add to cart (using search_and_add_to_cart for better reliability)
mcporter call blinkit.search_and_add_to_cart --args '{"query": "milk", "item_index": 0}'

# 3. Proceed to checkout
mcporter call blinkit.checkout

# 4. Select address (if prompted)
mcporter call blinkit.get_addresses
mcporter call blinkit.select_address --args '{"index": 0}'

# 5. Select COD and place order
mcporter call blinkit.select_cod
mcporter call blinkit.place_cod_order
```

## 🔧 Available Tools

### Authentication
- `check_login`: Check if logged in
- `login_prepare_and_wait`: Start login process with phone number
- `enter_otp`: Enter OTP (alternative to file-based system)

### Shopping
- `search`: Search for products
- `search_and_add_to_cart`: Search and immediately add to cart (recommended)
- `add_to_cart`: Add product by ID to cart
- `remove_from_cart`: Remove product from cart
- `check_cart`: View current cart contents

### Checkout & Payment
- `checkout`: Proceed to checkout
- `get_addresses`: Get saved delivery addresses
- `select_address`: Select address by index
- `proceed_to_pay`: Continue to payment after address selection
- `select_cod`: Select Cash on Delivery
- `place_cod_order`: Complete COD order

### Advanced
- `complete_order_flow`: End-to-end automation
- `get_upi_ids`: Get available UPI payment options
- `select_upi_id`: Select UPI payment method
- `pay_now`: Complete UPI payment

## 🎯 Key Fixes Implemented

### **Cart System Overhaul**
The original cart functionality failed because:
- Products weren't found after search due to session state issues
- ADD buttons had various selectors that weren't covered
- No fallback strategies when product IDs didn't match

**Our fixes:**
- Multi-strategy product detection (ID, name, position)
- Re-search capability when products aren't found
- Robust ADD button detection with multiple selectors
- Smart fallback to available products when exact match fails

### **Checkout Flow Enhancement**
The original checkout was incomplete:
- No address selection handling
- No COD payment method support
- No proper state transition management

**Our improvements:**
- Full address selection automation
- COD payment method detection and selection
- State-aware checkout progression
- Order completion verification

### **OTP System Reliability**
Enhanced the file-based OTP system:
- Real-time file monitoring
- Automatic cleanup after use
- Better error messages and status updates

## 📋 Example Workflows

### **Coffee Order**
```bash
mcporter call blinkit.complete_order_flow --args '{"query": "davidoff coffee", "item_index": 0, "address_index": 0}'
```

### **Grocery Shopping**
```bash
# Search and add multiple items
mcporter call blinkit.search_and_add_to_cart --args '{"query": "bread", "item_index": 0}'
mcporter call blinkit.search_and_add_to_cart --args '{"query": "milk", "item_index": 0}'
mcporter call blinkit.search_and_add_to_cart --args '{"query": "eggs", "item_index": 0}'

# Complete checkout
mcporter call blinkit.checkout
mcporter call blinkit.select_address --args '{"index": 0}'
mcporter call blinkit.select_cod
mcporter call blinkit.place_cod_order
```

## 🐛 Troubleshooting

### Common Issues

**"Product ID not found"**
- Use `search_and_add_to_cart` instead of separate `search` + `add_to_cart`
- This function maintains session state between search and cart operations

**"Store unavailable"**
- Blinkit availability varies by location and time
- Try during peak hours (morning/evening)
- Check if your delivery area is serviceable

**"Could not find COD option"**
- Some products/locations may not support COD
- Try UPI payment as alternative
- Check if minimum order value is met

**Login Issues**
- Ensure phone number is correct (10 digits)
- OTP file should be created immediately after receiving SMS
- Check `/tmp/blinkit_otp.txt` permissions

## 🤝 Contributing

This is a maintained fork with active improvements. Issues and pull requests welcome!

### Development Setup
```bash
git clone https://github.com/ukrocks007/blinkit-mcp-improved.git
cd blinkit-mcp-improved
uv sync --dev
```

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Original Blinkit MCP by [hereisSwapnil](https://github.com/hereisSwapnil/blinkit-mcp)
- Enhanced and maintained by Ace (OpenClaw Assistant)

---

**⚡ Ready to automate your grocery shopping!** 🛒