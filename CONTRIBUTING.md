# Contributing to Blinkit MCP

Thank you for your interest in contributing to the Blinkit MCP Server!

## Development Setup

### Prerequisites

- Node.js 18 or higher
- npm or yarn
- Git

### Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/blinkit-mcp-improved.git
   cd blinkit-mcp-improved
   ```

3. Install dependencies:
   ```bash
   cd src
   npm install
   ```

4. Install Playwright browsers:
   ```bash
   npx playwright install chromium
   ```

## Making Changes

### Code Style

- Use consistent formatting (2 spaces for indentation)
- Add comments for complex logic
- Use descriptive variable names
- Follow existing code patterns

### Testing Your Changes

1. **Test individual tools**:
   ```bash
   node src/test_client.js
   ```

2. **Test end-to-end flow**:
   - Test with Claude Desktop or another MCP client
   - Verify: login → search → cart → checkout

3. **Debug mode**:
   Edit `src/playwright_auth.js` line 12:
   ```javascript
   headless: false  // See browser automation
   ```

### Areas for Contribution

- **New Payment Methods**: UPI, cards, wallets
- **Cart Operations**: Remove items, update quantities
- **Order Management**: View history, track orders
- **Search Enhancements**: Filters, categories
- **Error Handling**: Better recovery, more informative messages
- **Performance**: Faster waits, optimized selectors
- **Documentation**: Improve guides, add examples

## Selector Updates

When Blinkit UI changes:

1. Run with `headless: false`
2. Use Chrome DevTools to inspect elements
3. Update selectors in `playwright_auth.js`
4. Add fallback selectors for robustness
5. Test thoroughly

## Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "feat: description of changes"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Open a Pull Request with:
   - Clear description of changes
   - Why the change is needed
   - How you tested it
   - Screenshots/recordings if UI-related

## Commit Message Format

Use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test updates
- `chore:` Maintenance tasks

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for general questions
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for helping make Blinkit MCP better! 🚀