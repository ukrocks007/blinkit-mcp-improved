# Contributing to Blinkit MCP Server Enhanced

Thank you for your interest in contributing! This project aims to provide reliable automation for Blinkit grocery orders.

## 🚀 Quick Start

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/blinkit-mcp-improved.git
   cd blinkit-mcp-improved
   ```
3. **Set up development environment**:
   ```bash
   uv sync --dev
   uv run playwright install firefox
   ```

## 📋 Development Guidelines

### **Code Style**
- Follow existing code patterns
- Add comprehensive error handling
- Include detailed logging for debugging
- Write clear docstrings for new functions

### **Testing**
Before submitting:
1. Test login flow with real phone number
2. Test search functionality with various queries
3. Test cart operations in different scenarios
4. Verify checkout flow works end-to-end

### **Browser Automation Best Practices**
- Use multiple selector strategies for robustness
- Add appropriate wait times for UI changes
- Handle dynamic content gracefully
- Include fallback strategies for element detection

## 🐛 Bug Fixes

### **Common Areas Needing Attention**
1. **Cart Operations**: Product detection, ADD button clicking
2. **Checkout Flow**: Address selection, payment method detection
3. **Session Management**: Login persistence, state tracking
4. **Error Handling**: Graceful failures, informative messages

### **Debugging Tips**
- Use browser DevTools to inspect element selectors
- Test with different product types and categories
- Verify functionality during different times of day
- Check for Blinkit UI changes that might break automation

## ✨ Feature Requests

### **Priority Areas**
1. **Multi-product ordering**: Batch operations
2. **Scheduled ordering**: Recurring orders
3. **Price tracking**: Compare prices over time
4. **Inventory alerts**: Notify when products are in stock
5. **Order history**: Track past purchases

### **UI/UX Improvements**
- Better error messages
- Progress indicators for long operations
- Configuration management
- Alternative payment methods

## 🧪 Testing Strategy

### **Manual Testing Checklist**
- [ ] Login with OTP works
- [ ] Search finds products consistently
- [ ] Add to cart succeeds reliably
- [ ] Checkout flow completes without errors
- [ ] COD payment selection works
- [ ] Order placement succeeds

### **Edge Cases to Test**
- [ ] Out of stock products
- [ ] Store unavailable scenarios
- [ ] Network timeouts
- [ ] Invalid addresses
- [ ] Payment method unavailable

## 📝 Submission Process

1. **Create feature branch**: `git checkout -b feature/your-feature-name`
2. **Make changes with tests**
3. **Update documentation** if needed
4. **Commit with clear messages**:
   ```bash
   git commit -m "🐛 Fix cart detection for new Blinkit UI
   
   - Updated selectors for product cards
   - Added fallback strategy for ADD buttons
   - Improved error messages for debugging"
   ```
5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

## 🔧 Development Environment

### **Required Tools**
- Python 3.8+
- uv (package manager)
- Firefox browser
- mcporter (MCP client)

### **Optional Tools**
- Browser DevTools for selector debugging
- Playwright Inspector for automation debugging

## 🛡️ Security Considerations

- **Never commit credentials** or phone numbers
- **Use environment variables** for sensitive data
- **Respect rate limits** to avoid being blocked
- **Handle OTP securely** in file-based system

## 🤝 Community

- **Be respectful** and constructive in discussions
- **Share knowledge** about Blinkit's UI changes
- **Help debug** issues reported by other users
- **Document** solutions for common problems

## 📞 Contact

For questions or discussions:
- Create an issue for bugs or features
- Start a discussion for general questions
- Maintained by Ace (OpenClaw Assistant)

---

**Happy contributing! 🛒⚡**