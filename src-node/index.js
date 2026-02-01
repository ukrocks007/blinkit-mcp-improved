import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { BlinkitAPIClient } from "./client.js";
import dotenv from "dotenv";

dotenv.config();

class BlinkitNodeServer {
  constructor() {
    this.server = new Server(
      {
        name: "blinkit-node-mcp",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.client = new BlinkitAPIClient();
    this.setupTools();
  }

  setupTools() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "search_products",
          description: "Search for products on Blinkit using API",
          inputSchema: {
            type: "object",
            properties: {
              query: { type: "string", description: "Search query (e.g., 'milk', 'bread')" },
              limit: { type: "number", default: 20 },
            },
            required: ["query"],
          },
        },
        {
          name: "get_addresses",
          description: "Get saved delivery addresses",
          inputSchema: {
            type: "object",
            properties: {},
          },
        },
        {
          name: "check_cart",
          description: "Check items in the current cart",
          inputSchema: {
            type: "object",
            properties: {},
          },
        },
        {
          name: "add_to_cart",
          description: "Add a product to the cart",
          inputSchema: {
            type: "object",
            properties: {
              productId: { type: "string", description: "The ID of the product to add" },
              quantity: { type: "number", default: 1 },
            },
            required: ["productId"],
          },
        },
        {
          name: "place_order",
          description: "Place an order using Cash on Delivery (COD)",
          inputSchema: {
            type: "object",
            properties: {
              addressId: { type: "string", description: "The ID of the delivery address" },
            },
            required: ["addressId"],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        await this.client.loadAuthTokensFromSession();

        switch (name) {
          case "search_products":
            return await this.handleSearch(args.query, args.limit);
          case "get_addresses":
            return await this.handleGetAddresses();
          case "check_cart":
            return await this.handleCheckCart();
          case "add_to_cart":
            return await this.handleAddToCart(args.productId, args.quantity);
          case "place_order":
            return await this.handlePlaceOrder(args.addressId);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [{ type: "text", text: `Error: ${error.message}` }],
          isError: true,
        };
      }
    });
  }

  async handleSearch(query, limit = 20) {
    // Primary search API discovered in Python implementation
    const endpoint = '/v1/layout/search';
    const payload = {
        query: query,
        page: 0,
        size: limit,
        lat: 18.470896,   // Working Pune location
        lng: 73.86407
    };
    
    try {
        const data = await this.client.post(endpoint, payload);
        if (data && !data.error) {
            // Focus on layout products based on discovery
            const products = [];
            if (data.items) {
                data.items.forEach(item => {
                    if (item.type === 'product' && item.objects) {
                        item.objects.forEach(obj => {
                            products.push({
                                id: obj.id,
                                name: obj.name,
                                price: obj.price,
                                brand: obj.brand
                            });
                        });
                    }
                });
            }

            if (products.length === 0) {
                return { content: [{ type: "text", text: "No products found." }] };
            }

            let text = `Found ${products.length} products:\n\n`;
            products.slice(0, limit).forEach((p, i) => {
                text += `${i + 1}. ${p.name} - ₹${p.price} (ID: ${p.id})\n`;
            });
            return { content: [{ type: "text", text }] };
        }
    } catch (e) {
        return { content: [{ type: "text", text: `Search failed: ${e.message}` }], isError: true };
    }
    
    return { content: [{ type: "text", text: "Search API returned an unexpected response." }] };
  }

  async handleGetAddresses() {
    const endpoint = '/v4/address';
    try {
        const data = await this.client.get(endpoint);
        if (data.error) throw new Error(data.message || 'Failed to fetch addresses');
        
        const addresses = data.addresses || [];
        if (addresses.length === 0) {
            return { content: [{ type: "text", text: "No saved addresses found." }] };
        }

        let text = `Found ${addresses.length} addresses:\n\n`;
        addresses.forEach((a, i) => {
          text += `${i + 1}. [${a.tag}] ${a.address_string} (ID: ${a.id})\n`;
        });
        return { content: [{ type: "text", text }] };
    } catch (e) {
        return { content: [{ type: "text", text: `Failed to get addresses: ${e.message}` }], isError: true };
    }
  }

  async handleCheckCart() {
    const endpoint = '/v5/carts';
    try {
        const data = await this.client.get(endpoint);
        if (data.error) throw new Error(data.message || 'Failed to fetch cart');
        
        const cart = data.cart || {};
        const items = cart.items || [];
        
        if (items.length === 0) {
            return { content: [{ type: "text", text: "Your cart is empty." }] };
        }

        let text = `Cart items (${items.length}):\n\n`;
        items.forEach((item, i) => {
          text += `${i + 1}. ${item.name} x ${item.quantity} - ₹${item.price}\n`;
        });
        return { content: [{ type: "text", text: text + `\nTotal: ₹${cart.total_amount || 0}` }] };
    } catch (e) {
        return { content: [{ type: "text", text: `Failed to check cart: ${e.message}` }], isError: true };
    }
  }

  async handleAddToCart(productId, quantity = 1) {
    const endpoint = '/v5/carts';
    const payload = {
        items: [{
            product_id: productId,
            quantity: quantity
        }]
    };
    
    try {
        const data = await this.client.post(endpoint, payload);
        if (data.error) throw new Error(data.message || 'Failed to add to cart');
        
        return { content: [{ type: "text", text: `Successfully added product ${productId} to cart (Quantity: ${quantity}).` }] };
    } catch (e) {
        return { content: [{ type: "text", text: `Failed to add to cart: ${e.message}` }], isError: true };
    }
  }

  async handlePlaceOrder(addressId) {
    // This is a simplified implementation based on the hybrid approach
    return { 
        content: [{ 
            type: "text", 
            text: "Order placement via direct API requires final checkout validation. Please use the browser to confirm payment for Address ID: " + addressId 
        }] 
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Blinkit Node MCP Server running on stdio");
  }
}

const server = new BlinkitNodeServer();
server.run().catch(console.error);