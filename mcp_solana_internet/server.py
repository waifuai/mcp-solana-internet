import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple

import httpx
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
from config import RPC_ENDPOINT, PAYMENT_WALLET, LAMPORTS_PER_SOL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PAYMENT_EXPIRY_HOURS = 24  # Payments expire after 24 hours
MAX_PAYMENT_HISTORY = 1000  # Maximum payment records to keep in memory
REQUEST_TIMEOUT = 30.0      # RPC request timeout

# Data structures for payment tracking (in-memory storage for demo)
# In production, use a proper database
payment_records: Dict[str, List[Dict]] = {}  # user_pubkey -> list of payments
resource_prices: Dict[str, float] = {
    "resource_1": 0.1,
    "resource_2": 0.5,
    "premium_content": 1.0,
    "basic_content": 0.05,
    "pro_content": 2.0,
}

# Payment record structure
class PaymentRecord(BaseModel):
    user_pubkey: str
    resource_id: str
    amount_sol: float
    tx_signature: str
    timestamp: datetime
    status: str = "confirmed"  # pending, confirmed, failed

def cleanup_expired_payments():
    """Remove expired payment records."""
    cutoff_time = datetime.now() - timedelta(hours=PAYMENT_EXPIRY_HOURS)
    for user_pubkey in list(payment_records.keys()):
        payment_records[user_pubkey] = [
            record for record in payment_records[user_pubkey]
            if record["timestamp"] > cutoff_time
        ]
        if not payment_records[user_pubkey]:
            del payment_records[user_pubkey]


# --- Helper Functions ---
def get_resource_price(resource_id: str) -> float:
    """Returns the price (in SOL) of a resource."""
    return resource_prices.get(resource_id, 0.0)


async def validate_transaction_on_chain(tx_signature: str, expected_amount_sol: float) -> Tuple[bool, str]:
    """Validate transaction on Solana blockchain."""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                RPC_ENDPOINT,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [
                        tx_signature,
                        {
                            "encoding": "jsonParsed",
                            "commitment": "confirmed",
                            "maxSupportedTransactionVersion": 0,
                        },
                    ],
                },
            )
            response.raise_for_status()
            transaction_data = response.json()

            if "error" in transaction_data:
                return False, f"RPC Error: {transaction_data['error']}"

            tx = transaction_data.get("result", {}).get("transaction")
            if not tx:
                return False, "Transaction not found"

            # Validate transaction structure
            instructions = tx.get("message", {}).get("instructions", [])
            if not instructions:
                return False, "No instructions found"

            first_instruction = instructions[0]
            if first_instruction.get("programId") != "11111111111111111111111111111111":
                return False, "Not a system program transfer"

            # Validate transfer details
            transfer_info = first_instruction.get("parsed", {}).get("info", {})
            if not transfer_info:
                return False, "Invalid transfer instruction"

            destination = transfer_info.get("destination")
            if destination != str(PAYMENT_WALLET.pubkey()):
                return False, "Payment sent to wrong address"

            actual_lamports = transfer_info.get("lamports", 0)
            actual_sol = actual_lamports / LAMPORTS_PER_SOL

            if actual_sol < expected_amount_sol:
                return False, f"Insufficient payment: {actual_sol} SOL < {expected_amount_sol} SOL"

            return True, f"Valid payment: {actual_sol} SOL"

    except Exception as e:
        logger.error(f"Error validating transaction {tx_signature}: {e}")
        return False, f"Validation error: {str(e)}"


async def has_paid_for_access(user_pubkey: Pubkey, resource_id: str) -> bool:
    """Checks if a user has made a valid payment for a resource."""
    user_key = str(user_pubkey)

    # Clean up expired payments
    cleanup_expired_payments()

    # Check payment records
    user_payments = payment_records.get(user_key, [])

    for payment in user_payments:
        if (payment["resource_id"] == resource_id and
            payment["status"] == "confirmed" and
            payment["timestamp"] > datetime.now() - timedelta(hours=PAYMENT_EXPIRY_HOURS)):
            logger.info(f"Valid payment found for {user_key} accessing {resource_id}")
            return True

    return False


def record_payment(user_pubkey: str, resource_id: str, amount_sol: float, tx_signature: str):
    """Record a payment in our in-memory storage."""
    if user_pubkey not in payment_records:
        payment_records[user_pubkey] = []

    payment_record = {
        "user_pubkey": user_pubkey,
        "resource_id": resource_id,
        "amount_sol": amount_sol,
        "tx_signature": tx_signature,
        "timestamp": datetime.now(),
        "status": "confirmed"
    }

    payment_records[user_pubkey].append(payment_record)

    # Limit history size
    if len(payment_records[user_pubkey]) > MAX_PAYMENT_HISTORY:
        payment_records[user_pubkey] = payment_records[user_pubkey][-MAX_PAYMENT_HISTORY:]

    logger.info(f"Payment recorded: {amount_sol} SOL for {resource_id} by {user_pubkey}")


# --- MCP Setup ---
mcp = FastMCP(name="Solana Internet Server")
# mcp.flask_app.register_blueprint(payments_blueprint) # Removed - Flask app runs separately


# --- MCP Resources ---
@mcp.tool()
async def check_access(
    context: Context,
    user_pubkey: str = Field(..., description="The user's public key."),
    resource_id: str = Field(..., description="The ID of the resource being accessed."),
) -> str:
    """Checks if a user has access to a specific resource based on payment history."""
    try:
        user_pubkey_obj = Pubkey.from_string(user_pubkey)
    except ValueError:
        return json.dumps({
            "access": False,
            "error": "Invalid public key format"
        })

    # Check if resource exists
    if resource_id not in resource_prices:
        return json.dumps({
            "access": False,
            "error": f"Unknown resource: {resource_id}"
        })

    access_granted = await has_paid_for_access(user_pubkey_obj, resource_id)

    if access_granted:
        return json.dumps({
            "access": True,
            "message": f"Access granted to {resource_id}",
            "resource_id": resource_id
        })
    else:
        payment_amount_sol = get_resource_price(resource_id)
        payment_url = f"http://localhost:5001/process_payment_action"

        return json.dumps({
            "access": False,
            "message": f"Payment required for {resource_id}",
            "payment_amount_sol": payment_amount_sol,
            "payment_url": payment_url,
            "resource_id": resource_id,
            "user_pubkey": user_pubkey
        })


@mcp.tool()
async def get_resource_info(
    context: Context,
    resource_id: Optional[str] = Field(None, description="Specific resource ID, or get all if not provided")
) -> str:
    """Get information about available resources and their prices."""
    if resource_id:
        if resource_id not in resource_prices:
            return json.dumps({"error": f"Resource {resource_id} not found"})

        return json.dumps({
            "resource_id": resource_id,
            "price_sol": resource_prices[resource_id],
            "description": f"Access to {resource_id.replace('_', ' ')}"
        })
    else:
        return json.dumps({
            "resources": [
                {
                    "id": rid,
                    "name": rid.replace("_", " ").title(),
                    "price_sol": price
                }
                for rid, price in resource_prices.items()
            ]
        })


@mcp.tool()
async def get_payment_history(
    context: Context,
    user_pubkey: str = Field(..., description="The user's public key"),
    resource_id: Optional[str] = Field(None, description="Filter by specific resource")
) -> str:
    """Get payment history for a user."""
    try:
        user_pubkey_obj = Pubkey.from_string(user_pubkey)
    except ValueError:
        return json.dumps({"error": "Invalid public key"})

    user_key = str(user_pubkey_obj)
    user_payments = payment_records.get(user_key, [])

    if resource_id:
        user_payments = [p for p in user_payments if p["resource_id"] == resource_id]

    # Clean up expired payments for response
    cutoff_time = datetime.now() - timedelta(hours=PAYMENT_EXPIRY_HOURS)
    valid_payments = [p for p in user_payments if p["timestamp"] > cutoff_time]

    return json.dumps({
        "user_pubkey": user_pubkey,
        "payment_count": len(valid_payments),
        "payments": [
            {
                "resource_id": p["resource_id"],
                "amount_sol": p["amount_sol"],
                "tx_signature": p["tx_signature"],
                "timestamp": p["timestamp"].isoformat(),
                "status": p["status"]
            }
            for p in valid_payments
        ]
    })


# --- MCP Tools ---
@mcp.tool()
async def process_payment(
    context: Context,
    amount_sol: float = Field(..., description="The amount of SOL to pay.", ge=0.001),
    payment_transaction: str = Field(
        ...,
        description="The transaction signature of the SOL payment."
    ),
    client_ip: str = Field(..., description="The client's IP address."),
    resource_id: Optional[str] = Field(
        None, description="The ID of the resource being purchased."
    ),
    user_pubkey: str = Field(..., description="The user's public key."),
) -> str:
    """Processes a SOL payment and grants access to the requested resource."""
    try:
        # Input validation
        if amount_sol <= 0:
            return json.dumps({"error": "Amount must be greater than 0"})

        if amount_sol > 1000:  # Reasonable upper limit
            return json.dumps({"error": "Amount exceeds maximum limit of 1000 SOL"})

        # Validate transaction signature format
        try:
            tx_signature = Signature.from_string(payment_transaction)
        except ValueError as e:
            return json.dumps({"error": f"Invalid transaction signature: {e}"})

        # Validate user public key
        try:
            user_pubkey_obj = Pubkey.from_string(user_pubkey)
        except Exception:
            return json.dumps({"error": "Invalid user public key"})

        logger.info(f"Processing payment: {amount_sol} SOL for {resource_id} from {user_pubkey}")

        # Validate transaction on-chain
        is_valid, validation_message = await validate_transaction_on_chain(
            payment_transaction, amount_sol
        )

        if not is_valid:
            logger.warning(f"Payment validation failed: {validation_message}")
            return json.dumps({"error": validation_message})

        # Record the payment
        record_payment(user_pubkey, resource_id or "general", amount_sol, payment_transaction)

        # Log successful payment
        logger.info(f"Payment processed successfully: {amount_sol} SOL for {resource_id} by {user_pubkey}")

        return json.dumps({
            "success": True,
            "message": f"Payment of {amount_sol:.6f} SOL received and confirmed",
            "resource_id": resource_id,
            "tx_signature": payment_transaction,
            "access_granted": True
        })

    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        return json.dumps({"error": f"Payment processing failed: {str(e)}"})


if __name__ == "__main__":
    import asyncio

    # Log startup information
    logger.info("Starting Solana Internet MCP Server")
    logger.info(f"RPC Endpoint: {RPC_ENDPOINT}")
    logger.info(f"Payment Wallet: {PAYMENT_WALLET.pubkey()}")
    logger.info(f"Available resources: {list(resource_prices.keys())}")
    logger.info("Server ready to accept connections")

    try:
        asyncio.run(mcp.run(transport="stdio"))
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise