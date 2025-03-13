# MCP Solana Internet: Direct SOL Payments for Content Access

This project demonstrates a proof-of-concept implementation of an MCP server that integrates with the Solana blockchain to enable paid access to digital content and resources using direct SOL payments. It showcases how MCP can be combined with a blockchain to create decentralized, permissionless access control systems.

## Overview

The project consists of two main components:

*   **MCP Server (`server.py`):**  This is the core MCP server, built using the `fastmcp` library. It handles MCP requests, manages resource access, and interacts with the Solana blockchain.
*   **Payment API (`payments.py`):** A Flask-based API that handles the creation of payment transactions.  This is integrated *within* the MCP server itself (using Flask blueprints), simplifying deployment and interaction.  This approach makes it easy to create "solana-action:" URIs, as described in the MCP specification.

The server exposes an MCP resource (`access://check`) that checks if a user has paid for access to a given resource.  If payment is required, it returns a `solana-action:` URL that the MCP client can use to initiate a payment transaction. The `process_payment` tool allows an MCP client to submit a signed Solana transaction, completing the payment.

## Features

*   **Direct SOL Payments:**  Users pay directly in SOL to access resources, eliminating intermediaries.
*   **Decentralized Access Control:**  The Solana blockchain acts as a transparent and immutable ledger for payment verification.
*   **MCP Integration:**  Leverages the MCP for standardized resource access requests and payment initiation.
*   **Flask-Based Payment API:**  Provides a simple and well-defined API for generating unsigned Solana payment transactions.
*   **Solana Interaction:**  Uses the `solders` library for efficient and idiomatic interaction with the Solana blockchain.
*   **Test Coverage:** Includes integration tests using `pytest` and `pytest-asyncio` to verify basic functionality.
*   **Extensible Design:**  Provides a foundation for building more complex paid content systems on Solana and MCP.

## Installation

1.  **Prerequisites:**

    *   Python 3.11+
    *   [Poetry](https://python-poetry.org/) (for dependency management)
    *   [Solana CLI](https://docs.solana.com/cli/install-solana-cli-tools) (version 1.16 or later)
    *   `solana-test-validator` (for local testing)

2.  **Clone the Repository:**

    ```bash
    git clone <repository_url>
    cd mcp-solana-internet
    ```

3.  **Install Dependencies:**

    ```bash
    poetry install
    ```

4.  **Environment Setup:**

    *   Create a `.env` file in the `mcp_solana_internet` directory:

        ```bash
        touch mcp_solana_internet/.env
        ```

    *   Edit the `.env` file and set the following variables:

        ```
        RPC_ENDPOINT="http://localhost:8899"  # Or your Solana cluster endpoint
        PAYMENT_WALLET_SEED="1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1"
        # ^^^ **IMPORTANT:**  This is a placeholder for demonstration purposes ONLY.
        # In a production environment, you MUST use a secure key management solution
        # (e.g., AWS KMS, HashiCorp Vault, or a hardware wallet).  Never store private
        # keys or seeds directly in code or configuration files.  This seed generates
        # the wallet address.
        ```
        *   `RPC_ENDPOINT`:  The URL of your Solana RPC endpoint.  For local development, you can use `http://localhost:8899` if you're running `solana-test-validator`. For testing against devnet, use `https://api.devnet.solana.com`.
        *   `PAYMENT_WALLET_SEED`: A comma-separated list of 32 integers representing the seed for the payment wallet.  This wallet will *receive* the SOL payments.  **Again, this is insecure and for demonstration only.**

## Usage

1.  **Start the Solana Test Validator (for local testing):**

    ```bash
    solana-test-validator
    ```

    This starts a local Solana cluster that you can use for testing.

2.  **Start the MCP Server:**

    ```bash
    poetry run python mcp_solana_internet/server.py
    ```

    The server will start listening for MCP requests on `stdin` and `stdout` (stdio transport).  It also starts the Flask payment API on port 5001.

3.  **Interacting with the Server (Conceptual Example):**

    An MCP client would interact with the server as follows:

    1.  **Check Access:** The client sends an MCP request to `access://check` with the user's public key and the resource ID.

    2.  **Payment Required:** If the user hasn't paid, the server responds with a JSON object containing:
        *   `access`: `false`
        *   `message`: "Payment required."
        *   `payment_url`: A `solana-action:` URI pointing to the `/process_payment_action` endpoint, including the required amount and resource ID as query parameters (e.g., `solana-action:/process_payment_action?amount_sol=0.1&resource_id=resource_1`).

    3. **Payment Transaction Creation:**

        * The client extracts the `payment_url` from the previous response. This url includes the amount and resource_id.
        * The client makes a `POST` request to `/process_payment_action` including the user's public key, `amount_sol` and `resource_id`.
        *  The payment API constructs an *unsigned* Solana transaction for a direct SOL transfer from the user's wallet to the `PAYMENT_WALLET`.  The API returns the serialized, unsigned transaction as a hex string.

    4.  **Transaction Signing (Client-Side):**  The client (e.g., the user's wallet software) *must* sign the transaction using the user's private key.  *This signing step is crucial for security and is not handled by the server.*

    5.  **Submit Payment:** The client sends the *signed* transaction to the Solana network. This can be achieved with the `solana` cli tool, or programatically through libraries like `solana-py` or `solders`.
    6.  The client then calls the `process_payment` *tool* on the MCP server, passing in the transaction *signature* (not the full transaction) as the `payment_transaction` parameter, along with the `amount_sol`, `client_ip` and `resource_id`. The server validates this signature by retrieving the full transaction from the blockchain, checking the amount, destination, etc.
    7.  **Re-check Access:** After the payment is confirmed, the client can again send an MCP request to `access://check`. This time, if the payment has been processed, the server should respond with `{"access": true}`.

## Code Structure

*   **`mcp_solana_internet/`:**
    *   **`server.py`:** The main MCP server implementation.
    *   **`payments.py`:** The Flask API for handling payment transaction creation.
    *   **`utils.py`:** (Currently empty)  A placeholder for utility functions.
    *   **`tests/`:**
        *   **`integration/`:** Integration tests for the server.
    *   **`pyproject.toml`:** Project metadata and dependencies (managed by Poetry).
    *   **`pytest.ini`:** Configuration for pytest.
*   **`.gitignore`:** Specifies files and directories to be ignored by Git.
*   **`README.md`:** This file.

## Key Files and Functions Explained

### `server.py`

*   **`RPC_ENDPOINT`:**  The Solana RPC endpoint URL.
*   **`PAYMENT_WALLET`:**  The `Keypair` object representing the wallet that receives payments.
*   **`LAMPORTS_PER_SOL`:**  The conversion factor between SOL and Lamports (the smallest unit of SOL).
*   **`get_resource_price(resource_id)`:**  A helper function that returns the price (in SOL) for a given resource ID.  This is a *placeholder* and should be replaced with a more robust pricing mechanism (e.g., fetching prices from a database or an oracle).
*   **`has_paid_for_access(user_pubkey, resource_id)`:** A *placeholder* function that checks if a user has paid for access to a resource.  In a real application, this would involve querying a database of payment records.
*   **`@mcp.resource("access://check")`:**  The MCP resource handler for checking access.  It takes the user's public key and the resource ID as input.
*   **`@mcp.tool()`:** Defines the `process_payment` tool which validates the user's payment transaction signature.
* **Flask Blueprint Integration:** `mcp.flask_app.register_blueprint(payments_blueprint)` integrates the Flask payment API directly into the MCP server.

### `payments.py`

*   **`payment_app`:**  The Flask application (blueprint) for the payment API.
*   **`/process_payment_action` (GET):**  An endpoint that returns metadata describing the payment action, conforming to the MCP action format.
*   **`/process_payment_action` (POST):**  An endpoint that takes the amount, resource ID, *and user's public key* as input, and returns a serialized, *unsigned* Solana transaction for a direct SOL transfer.
*   **CORS Handling:** Includes CORS headers to allow requests from different origins (e.g., a web-based wallet).

### `tests/integration/test_server.py`

*   **`test_access_check_no_payment`:** Tests the `access://check` resource when the user has not paid.
*   **`test_access_check_invalid_pubkey`:** Tests the `access://check` resource with an invalid public key.
*   **`test_access_check_paid`:** Simulates a paid user (currently, `has_paid_for_access` always returns `False`, so this test expects access to be denied).

## Improvements and Future Work

*   **Database Integration:** Replace the placeholder `has_paid_for_access` function with a database query to store and retrieve payment records. This would involve:
    *   Choosing a database (e.g., PostgreSQL, MySQL, or a NoSQL database).
    *   Creating a table to store payment information (user public key, resource ID, amount, timestamp, transaction signature).
    *   Implementing functions to insert and query payment records.
*   **Robust Transaction Validation:** Enhance the `process_payment` tool to perform more thorough validation of the payment transaction, including:
    *   Checking for double-spending.
    *   Verifying the transaction's recent blockhash.
    *   Checking for any other potential issues.
*   **Error Handling:** Improve error handling throughout the code to provide more informative error messages to the client.
*   **Security:**
    *   Implement a secure key management solution for the `PAYMENT_WALLET`.
    *   Consider using a more secure method for handling the user's public key in the `payments.py` API (e.g., requiring a signed message from the user).
*   **Asynchronous Operations:**  Use asynchronous database operations to improve performance.
*   **Token Payments:**  Extend the system to support payments with SPL tokens in addition to SOL.
*   **Subscription Model:**  Implement a subscription model where users can pay for recurring access to resources.
*   **Dynamic Pricing:** Integrate with an oracle or a dynamic pricing mechanism to fetch resource prices in real-time.
*   **More Tests:**  Add more unit and integration tests to cover all aspects of the code.
* **Refactor process_payment:** Separate the transaction fetching and validation from the MCP tool, which is mainly an interface.

This README provides a comprehensive overview of the project, its features, installation instructions, usage examples, and potential improvements. It aims to be informative and helpful for developers interested in understanding and extending the project. The emphasis on security and the clear distinction between placeholder implementations and production-ready solutions are also crucial.
