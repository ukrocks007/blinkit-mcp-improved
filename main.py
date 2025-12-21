from src.auth.blinkit_auth import BlinkitAuth
from src.order.blinkit_order import BlinkitOrder


def main():
    # Initialize Auth
    # Headless=False to see the browser and debug
    auth = BlinkitAuth(headless=False)

    try:
        print("Starting browser...")
        auth.start_browser()

        # Check if already logged in
        auth.page.wait_for_timeout(3000)

        if not auth.is_logged_in():
            print("Not logged in.")
            phone = input("Enter your phone number: ")
            auth.login(phone)

            otp = input("Enter the OTP you received: ")
            auth.enter_otp(otp)

            print("Waiting for login to complete...")
            auth.page.wait_for_timeout(5000)

            if auth.is_logged_in():
                print("Login successful!")
                auth.save_session()
            else:
                print("Login failed or could not verify.")
                return

        print("Already logged in! Session valid.")

        # Initialize Order
        order = BlinkitOrder(auth.page)

        print("\n" + "=" * 50)
        print("      Welcome to Blinkit CLI Automation")
        print("=" * 50)
        print("Commands:")
        print("  search <query>   : Search for products (default: milk)")
        print("  add <index>      : Add item at index to cart")
        print("  cart             : View/Check cart status")
        print("  checkout         : Proceed to checkout & address selection")
        print("  address          : Manually trigger address selection")
        print("  login            : Re-initiate login flow")
        print("  quit / exit      : Close and exit")
        print("=" * 50 + "\n")

        while True:
            try:
                # Use a simple input prompt
                user_input = input("blinkit> ").strip()
                if not user_input:
                    continue

                parts = user_input.split()
                cmd = parts[0].lower()
                args = parts[1:]

                if cmd in ["quit", "exit"]:
                    print("Exiting...")
                    break

                elif cmd == "help":
                    print(
                        "Commands: search <query>, add <index>, cart, checkout, address, login, quit"
                    )

                elif cmd == "login":
                    if not auth.is_logged_in():
                        phone = input("Enter phone number: ")
                        auth.login(phone)
                        otp = input("Enter OTP: ")
                        auth.enter_otp(otp)
                        if auth.is_logged_in():
                            auth.save_session()
                    else:
                        print("Already logged in.")

                elif cmd == "search":
                    term = " ".join(args) if args else "milk"
                    order.search_product(term)
                    results = order.get_search_results()
                    if results:
                        print("\nSearch Results:")
                        for item in results:
                            print(f"[{item['index']}] {item['name']} - {item['price']}")
                    else:
                        print("No results found.")

                elif cmd == "add":
                    if args and args[0].isdigit():
                        order.add_to_cart(int(args[0]))
                    else:
                        print("Usage: add <item_index>")

                elif cmd == "cart":
                    order.get_cart_items()

                elif cmd == "address":
                    addresses = order.get_saved_addresses()
                    if addresses:
                        print("\nSelect Delivery Address:")
                        for addr in addresses:
                            print(
                                f"[{addr['index']}] {addr['label']} - {addr['details'][:50]}..."
                            )

                        sel = input("Select index (Enter to cancel): ")
                        if sel.strip().isdigit():
                            order.select_address(int(sel))
                    else:
                        print("Address selection not available (modal not open?).")

                elif cmd == "checkout":
                    order.place_order()
                    print("Checking for address selection after checkout...")
                    auth.page.wait_for_timeout(2000)
                    # Auto-check address
                    addresses = order.get_saved_addresses()
                    if addresses:
                        print("\nSelect Delivery Address:")
                        for addr in addresses:
                            print(
                                f"[{addr['index']}] {addr['label']} - {addr['details'][:50]}..."
                            )

                        sel = input("Select index (Enter to keep current): ")
                        if sel.strip().isdigit():
                            order.select_address(int(sel))
                            order.place_order()

                else:
                    print(f"Unknown command: {cmd}")

            except KeyboardInterrupt:
                print("\nType 'quit' to exit.")
                break
            except Exception as e:
                print(f"Error executing command: {e}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Check if auth is defined before closing
        if "auth" in locals():
            auth.close()


if __name__ == "__main__":
    main()
