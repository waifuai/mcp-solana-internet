import asyncio
import json
import os
import time
from typing import Dict, Optional

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from solders.hash import Hash as Blockhash
from solders.signature import Signature
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.system_program import transfer, TransferParams
from urllib.parse import quote

from mcp.server.fastmcp import Context, FastMCP
from mcp_solana_internet.payments import payment_app as payments_blueprint # Import the blueprint

load_dotenv()

# --- Configuration ---
RPC_ENDPOINT = os.getenv("RPC_ENDPOINT", "http://localhost:8899")
# Placeholder: In a real application, use a secure key management system.
PAYMENT_WALLET = Keypair.from_seed(
    bytes([int(x) for x in os.getenv("PAYMENT_WALLET_SEED", "1" * 32).split(",")])
)
LAMPORTS_PER_SOL = 10**9


# --- Helper Functions ---
def get_resource_price(resource_id: str) -> float:
    """Returns the price (in SOL) of a resource."""
    prices = {
        "resource_1": 0.1,
        "resource_2": 0.5,
        "premium_content": 1.0,
    }  # Hardcoded prices for now
    return prices.get(resource_id, 0.0)  # Default to 0.0 if not found


async def has_paid_for_access(user_pubkey: Pubkey, resource_id: str) -> bool:
    """Checks if a user has made a direct SOL payment for a resource.

    This is a simplified example.  In a real system, you would:
    1.  Store a record of payments (user, resource, amount, timestamp, tx_signature) in a database.
    2.  Query the database to see if there's a valid, recent payment from the user for the resource.
    3.  Potentially check the transaction on-chain to confirm it hasn't been reversed.
    """
    # Placeholder:  For now, assume no one has paid.
    return False


# --- MCP Setup ---
mcp = FastMCP(name="Solana Internet Server")
mcp.flask_app.register_blueprint(payments_blueprint) # Register the blueprint


# --- MCP Resources ---
@mcp.resource("access://check")
async def check_access(
    context: Context,
    user_pubkey: str = Field(..., description="The user's public key."),
    resource_id: str = Field(..., description="The ID of the resource being accessed."),
) -> str:
    """Checks if a user has access to a specific resource."""
    try:
        user_pubkey_obj = Pubkey.from_string(user_pubkey)
    except ValueError:
        return json.dumps({"access": False, "error": "Invalid public key."})

    access_granted = await has_paid_for_access(user_pubkey_obj, resource_id)

    if access_granted:
        return json.dumps({"access": True})
    else:
        payment_amount_sol = get_resource_price(resource_id)
        action_api_url = (
            f"/process_payment_action?amount_sol={payment_amount_sol}&resource_id={resource_id}"
        )
        blink_url = "solana-action:" + quote(action_api_url)

        return json.dumps(
            {"access": False, "message": "Payment required.", "payment_url": blink_url}
        )


# --- MCP Tools ---
@mcp.tool()
async def process_payment(
    context: Context,
    amount_sol: float = Field(..., description="The amount of SOL to pay."),
    payment_transaction: str = Field(
        ...,
        description=(
            "The transaction signature of the SOL payment.  Provide a transaction "
            "that is already signed and contains all the required fields."
        ),
    ),
    client_ip: str = Field(..., description="The client's IP address."),
    resource_id: Optional[str] = Field(
        None, description="The ID of the resource being purchased (optional)."
    ),
) -> str:
    """Processes a SOL payment."""
    async with httpx.AsyncClient() as client:
        try:
            # Basic validation (in a real system, do more thorough checks)
            if amount_sol <= 0:
                return "Invalid amount. Must be greater than 0."

            try:
                tx_signature = Signature.from_string(payment_transaction)
            except ValueError as e:
                return f"Invalid transaction signature: {e}"

            # In a real system:
            # 1. Validate the transaction signature and contents.
            # 2. Check that the payment is to the correct address (PAYMENT_WALLET).
            # 3. Check that the amount is correct.
            # 4. Record the payment in a database.
            transaction_response = await client.post(
                RPC_ENDPOINT,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [
                        str(tx_signature),
                        {
                            "encoding": "jsonParsed",
                            "commitment": "confirmed",
                            "maxSupportedTransactionVersion": 0,
                        },
                    ],
                },
            )
            transaction_response.raise_for_status()
            transaction_data = transaction_response.json()

            if "error" in transaction_data:
                return (f"Error fetching transaction: {transaction_data['error']}")

            tx = transaction_data["result"]["transaction"]

            # **CRUCIAL VALIDATION:**  Thoroughly check *ALL* aspects of this transaction:
            instructions = tx["message"]["instructions"]
            if (
                not instructions
                or instructions[0]["programId"] != "11111111111111111111111111111111"
            ):  # System Program ID
                return ("Invalid transaction. Not a system program transfer.")

            transfer_info = instructions[0]["parsed"]["info"]
            transfer_amount_lamports = transfer_info["lamports"]
            transfer_amount_sol = transfer_amount_lamports / LAMPORTS_PER_SOL

            if transfer_amount_sol < amount_sol:
                return(
                    f"Insufficient payment. Required: {amount_sol} SOL. Received: {transfer_amount_sol} SOL"
                )
            # Placeholder: Record the payment (replace with database interaction)
            print(
                f"Payment received: {amount_sol} SOL for resource {resource_id} from {transfer_info['source']}"
            )

            return f"Payment of {amount_sol:.6f} SOL received."

        except Exception as e:
            return f"An error occurred: {e}"


if __name__ == "__main__":
    import asyncio

    asyncio.run(mcp.run(transport="stdio"))