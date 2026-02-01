import { spawn } from 'child_process';
import readline from 'readline';

const server = spawn('node', ['index.js'], {
    stdio: ['pipe', 'pipe', 'inherit']
});

const rl = readline.createInterface({
    input: server.stdout,
    terminal: false
});

let step = 0;

rl.on('line', (line) => {
    try {
        const msg = JSON.parse(line);
        if (Object.keys(msg).length === 0) return;

        if (step === 0 && msg.id === 1) {
            console.log("\n✅ Server initialized successfully!");

            const initializedMsg = {
                jsonrpc: "2.0",
                method: "notifications/initialized",
                params: {}
            };
            server.stdin.write(JSON.stringify(initializedMsg) + "\n");

            console.log("\n📋 Listing available tools...");
            const listToolsMsg = {
                jsonrpc: "2.0",
                id: 2,
                method: "tools/list",
                params: {}
            };
            server.stdin.write(JSON.stringify(listToolsMsg) + "\n");
            step = 1;
        } else if (step === 1 && msg.id === 2) {
            if (msg.result && msg.result.tools) {
                console.log("\n✅ Available Tools:");
                msg.result.tools.forEach((tool, i) => {
                    console.log(`\n${i + 1}. ${tool.name}`);
                    console.log(`   ${tool.description}`);
                });

                console.log("\n\n🎉 Blinkit Browser MCP Server is ready!");
                console.log("\nAvailable tools:");
                console.log("  - login: Start authentication with phone number");
                console.log("  - verify_otp: Complete login with OTP");
                console.log("  - search_products: Search for products");
                console.log("  - add_to_cart: Add items to cart");
                console.log("  - check_cart: View cart contents");
                console.log("  - get_addresses: Get delivery addresses");
                console.log("  - place_order_cod: Complete COD checkout");
                console.log("\n💡 The browser will open when you call any tool.");
                console.log("💡 Use with MCP clients like Claude Desktop or test manually.\n");
            }
            server.kill();
            process.exit(0);
        }
    } catch (e) {
        // Not JSON, likely console.error output
    }
});

const initMsg = {
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: {
        protocolVersion: "2024-11-05",
        capabilities: {},
        clientInfo: {
            name: "test-client",
            version: "1.0.0"
        }
    }
};

console.log("🚀 Testing Blinkit Browser MCP Server...\n");
server.stdin.write(JSON.stringify(initMsg) + "\n");

// Timeout after 30 seconds
setTimeout(() => {
    console.log("\n❌ Test timeout");
    server.kill();
    process.exit(1);
}, 30000);
