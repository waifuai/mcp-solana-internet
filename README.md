# MCP Solana Internet

This project provides an MCP server for enabling paid access to content using direct SOL payments.

## Installation

1.  Clone the repository.
2.  Install dependencies using Poetry: `poetry install`
3.  Set up a Solana environment (Solana CLI and `solana-test-validator`).
4.  Create a `.env` file and set the `RPC_ENDPOINT` and `PAYMENT_WALLET_SEED` variables. **Important:** The `PAYMENT_WALLET_SEED` is a placeholder and should be replaced with a secure key management solution in a production environment.

## Usage

1.  Start the server: `poetry run python mcp_solana_internet/server.py`