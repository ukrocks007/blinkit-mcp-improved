#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { PlaywrightAuth } from "./playwright_auth.js";
import dotenv from "dotenv";

dotenv.config();

class BlinkitBrowserServer {
  constructor() {
    this.server = new McpServer({
      name: "blinkit-browser-mcp",
      version: "2.0.0",
    });

    this.playwright = null;
    this.setupTools();
  }

  async ensureBrowser() {
    if (!this.playwright) {
      this.playwright = new PlaywrightAuth();
      await this.playwright.startBrowser();
    }
    return this.playwright;
  }

  setupTools() {
    // Define all tools using the new McpServer API
    this.server.tool(
      "login",
      "Login to Blinkit with phone number (starts OTP flow)",
      {
        phoneNumber: {
          type: "string",
          description: "10-digit Indian phone number"
        },
      },
      async ({ phoneNumber }) => {
        return await this.handleLogin(phoneNumber);
      }
    );

    this.server.tool(
      "verify_otp",
      "Verify OTP received on phone to complete login",
      {
        otp: {
          type: "string",
          description: "4-digit OTP code"
        },
      },
      async ({ otp }) => {
        return await this.handleVerifyOTP(otp);
      }
    );

    this.server.tool(
      "search_products",
      "Search for products on Blinkit",
      {
        query: {
          type: "string",
          description: "Search query (e.g., 'milk', 'bread')"
        },
        limit: {
          type: "number",
          description: "Maximum number of results to return",
          default: 10
        },
      },
      async ({ query, limit }) => {
        return await this.handleSearch(query, limit || 10);
      }
    );

    this.server.tool(
      "add_to_cart",
      "Add a product to cart by its index from search results",
      {
        productIndex: {
          type: "number",
          description: "Index of the product from search results (0-based)"
        },
        quantity: {
          type: "number",
          description: "Quantity to add",
          default: 1
        },
      },
      async ({ productIndex, quantity }) => {
        return await this.handleAddToCart(productIndex, quantity || 1);
      }
    );

    this.server.tool(
      "check_cart",
      "View current items in cart",
      {},
      async () => {
        return await this.handleCheckCart();
      }
    );

    this.server.tool(
      "get_addresses",
      "Get information about saved delivery addresses",
      {},
      async () => {
        return await this.handleGetAddresses();
      }
    );

    this.server.tool(
      "place_order_cod",
      "Complete checkout and place order using Cash on Delivery",
      {
        addressIndex: {
          type: "number",
          description: "Index of the delivery address to use (0 = first address)",
          default: 0
        },
      },
      async ({ addressIndex }) => {
        return await this.handlePlaceOrderCOD(addressIndex || 0);
      }
    );
  }

  async handleLogin(phoneNumber) {
    try {
      const browser = await this.ensureBrowser();
      const result = await browser.login(phoneNumber);

      if (result.success) {
        return {
          content: [{
            type: "text",
            text: `✅ ${result.message}\n\nPlease check your phone for the OTP and use the 'verify_otp' tool to complete login.`
          }]
        };
      } else {
        return {
          content: [{ type: "text", text: `❌ Login failed: ${result.error}` }],
          isError: true
        };
      }
    } catch (error) {
      return {
        content: [{ type: "text", text: `❌ Login error: ${error.message}` }],
        isError: true
      };
    }
  }

  async handleVerifyOTP(otp) {
    try {
      if (!this.playwright) {
        return {
          content: [{ type: "text", text: "❌ Please call 'login' first to start the authentication flow." }],
          isError: true
        };
      }

      const result = await this.playwright.verifyOTP(otp);

      if (result.success) {
        return {
          content: [{
            type: "text",
            text: `🎉 ${result.message}\n\nYou can now search for products and place orders!`
          }]
        };
      } else {
        return {
          content: [{ type: "text", text: `❌ OTP verification failed: ${result.error}` }],
          isError: true
        };
      }
    } catch (error) {
      return {
        content: [{ type: "text", text: `❌ OTP verification error: ${error.message}` }],
        isError: true
      };
    }
  }

  async handleSearch(query, limit = 10) {
    try {
      const browser = await this.ensureBrowser();
      const products = await browser.searchProducts(query, limit);

      if (products.length === 0) {
        return {
          content: [{ type: "text", text: `No products found for "${query}".` }]
        };
      }

      let text = `🔍 Found ${products.length} products for "${query}":\n\n`;
      products.forEach((p, i) => {
        text += `${i}. ${p.name}\n   ${p.price}\n   [Use index ${i} to add to cart]\n\n`;
      });

      return { content: [{ type: "text", text }] };
    } catch (error) {
      return {
        content: [{ type: "text", text: `❌ Search failed: ${error.message}` }],
        isError: true
      };
    }
  }

  async handleAddToCart(productIndex, quantity) {
    try {
      if (!this.playwright) {
        return {
          content: [{ type: "text", text: "❌ Please search for products first before adding to cart." }],
          isError: true
        };
      }

      const result = await this.playwright.addToCart(productIndex, quantity);

      if (result.success) {
        return {
          content: [{
            type: "text",
            text: `✅ ${result.message}\n\nUse 'check_cart' to view your cart.`
          }]
        };
      } else {
        return {
          content: [{ type: "text", text: `❌ ${result.error}` }],
          isError: true
        };
      }
    } catch (error) {
      return {
        content: [{ type: "text", text: `❌ Add to cart failed: ${error.message}` }],
        isError: true
      };
    }
  }

  async handleCheckCart() {
    try {
      const browser = await this.ensureBrowser();
      const cart = await browser.getCart();

      if (cart.items.length === 0) {
        return {
          content: [{ type: "text", text: "🛒 Your cart is empty." }]
        };
      }

      let text = `🛒 Cart (${cart.items.length} items):\n\n`;
      cart.items.forEach((item, i) => {
        text += `${i + 1}. ${item.name}\n   ${item.quantity} - ${item.price}\n\n`;
      });
      text += `${cart.total}\n\n`;
      text += `Use 'place_order_cod' to checkout with Cash on Delivery.`;

      return { content: [{ type: "text", text }] };
    } catch (error) {
      return {
        content: [{ type: "text", text: `❌ Failed to get cart: ${error.message}` }],
        isError: true
      };
    }
  }

  async handleGetAddresses() {
    try {
      const browser = await this.ensureBrowser();
      const result = await browser.getAddresses();

      return {
        content: [{
          type: "text",
          text: `📍 ${result.message}`
        }]
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `❌ Failed to get addresses: ${error.message}` }],
        isError: true
      };
    }
  }

  async handlePlaceOrderCOD(addressIndex) {
    try {
      if (!this.playwright) {
        return {
          content: [{ type: "text", text: "❌ Please ensure you're logged in and have items in cart before placing order." }],
          isError: true
        };
      }

      const result = await this.playwright.placeOrderCOD(addressIndex);

      if (result.success) {
        return {
          content: [{
            type: "text",
            text: `🎉 ${result.message}\n\nYour order has been placed! Check the Blinkit app for order details.`
          }]
        };
      } else {
        return {
          content: [{ type: "text", text: `❌ Order placement failed: ${result.error}` }],
          isError: true
        };
      }
    } catch (error) {
      return {
        content: [{ type: "text", text: `❌ Order placement error: ${error.message}` }],
        isError: true
      };
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Blinkit Browser MCP Server running on stdio");

    // Cleanup on exit
    process.on('SIGINT', async () => {
      console.error('Shutting down...');
      if (this.playwright) {
        await this.playwright.close();
      }
      process.exit(0);
    });
  }
}

const server = new BlinkitBrowserServer();
server.run().catch(console.error);