import asyncio
import json
import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from urllib.parse import quote
from config import LAMPORTS_PER_SOL, PAYMENT_WALLET, RPC_ENDPOINT
from solders.pubkey import Pubkey
from solders.hash import Hash as Blockhash
from solders.message import Message
from solders.transaction import Transaction
from solders.system_program import transfer, TransferParams
import httpx

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
payment_app = Flask(__name__)

# Configuration
MAX_PAYMENT_AMOUNT_SOL = 1000.0  # Maximum payment amount in SOL
MIN_PAYMENT_AMOUNT_SOL = 0.001   # Minimum payment amount in SOL
REQUEST_TIMEOUT = 30.0           # RPC request timeout in seconds

# Resource validation
VALID_RESOURCE_IDS = {
    "resource_1",
    "resource_2",
    "premium_content",
    "basic_content",
    "pro_content"
}

def validate_payment_input(amount_sol: Any, resource_id: Any) -> tuple[bool, str]:
    """Validate payment input parameters."""
    if amount_sol is None:
        return False, "Missing required parameter: amount_sol"

    if resource_id is None:
        return False, "Missing required parameter: resource_id"

    try:
        amount = float(amount_sol)
    except (ValueError, TypeError):
        return False, "Invalid amount_sol: must be a number"

    if amount <= 0:
        return False, "Amount must be greater than 0"

    if amount < MIN_PAYMENT_AMOUNT_SOL:
        return False, f"Amount must be at least {MIN_PAYMENT_AMOUNT_SOL} SOL"

    if amount > MAX_PAYMENT_AMOUNT_SOL:
        return False, f"Amount cannot exceed {MAX_PAYMENT_AMOUNT_SOL} SOL"

    if not isinstance(resource_id, str) or not resource_id.strip():
        return False, "Invalid resource_id: must be a non-empty string"

    if resource_id not in VALID_RESOURCE_IDS:
        return False, f"Invalid resource_id: {resource_id}"

    return True, ""

async def get_latest_blockhash() -> Optional[Blockhash]:
    """Get the latest blockhash from Solana RPC."""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                RPC_ENDPOINT,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getLatestBlockhash",
                    "params": [{"commitment": "finalized"}],
                },
            )
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                logger.error(f"RPC Error: {result['error']}")
                return None

            blockhash_str = result["result"]["value"]["blockhash"]
            return Blockhash.from_string(blockhash_str)

    except httpx.TimeoutException:
        logger.error("Timeout getting latest blockhash")
        return None
    except Exception as e:
        logger.error(f"Error getting latest blockhash: {e}")
        return None

def create_cors_headers() -> Dict[str, str]:
    """Create CORS headers for responses."""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "3600",
    }


@payment_app.route("/process_payment_action", methods=["OPTIONS"])
def handle_options_process_payment():
    """Handle CORS preflight requests."""
    return "", 204, create_cors_headers()


@payment_app.route("/process_payment_action", methods=["GET"])
def get_process_payment_action_metadata():
    """Return payment action metadata for Solana Actions."""
    metadata = {
        "type": "action",
        "icon": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png",
        "title": "Process Payment",
        "description": "Make a SOL payment to access premium content.",
        "label": "Pay with SOL",
        "input": [
            {
                "name": "amount_sol",
                "type": "number",
                "label": "Amount of SOL to pay",
                "min": MIN_PAYMENT_AMOUNT_SOL,
                "max": MAX_PAYMENT_AMOUNT_SOL
            },
            {
                "name": "resource_id",
                "type": "select",
                "label": "Resource ID",
                "options": [{"label": rid.replace("_", " ").title(), "value": rid} for rid in VALID_RESOURCE_IDS]
            },
        ],
    }
    return jsonify(metadata), 200, create_cors_headers()


@payment_app.route("/process_payment_action", methods=["POST"])
def post_process_payment_action():
    """Process payment action and create Solana transaction."""
    headers = create_cors_headers()

    try:
        # Parse and validate input
        user_input = request.get_json()
        if not user_input:
            return jsonify({"error": "Invalid JSON payload"}), 400, headers

        amount_sol = user_input.get("amount_sol")
        resource_id = user_input.get("resource_id")
        user_pubkey_str = user_input.get("account")  # Solana Actions standard field

        # Validate inputs
        is_valid, error_msg = validate_payment_input(amount_sol, resource_id)
        if not is_valid:
            return jsonify({"error": error_msg}), 400, headers

        # Validate user public key
        if not user_pubkey_str:
            return jsonify({"error": "Missing user account public key"}), 400, headers

        try:
            user_pubkey = Pubkey.from_string(user_pubkey_str)
        except Exception:
            return jsonify({"error": "Invalid user account public key"}), 400, headers

        # Convert amount to lamports
        amount_lamports = int(float(amount_sol) * LAMPORTS_PER_SOL)

        logger.info(f"Creating payment transaction: {amount_sol} SOL to {resource_id} for {user_pubkey_str}")

        # Create transfer instruction
        transfer_ix = transfer(
            TransferParams(
                from_pubkey=user_pubkey,
                to_pubkey=PAYMENT_WALLET.pubkey(),
                lamports=amount_lamports,
            )
        )

        # Get latest blockhash (using asyncio.run since Flask doesn't support async natively)
        blockhash = asyncio.run(get_latest_blockhash())
        if not blockhash:
            return jsonify({"error": "Failed to get latest blockhash from RPC"}), 503, headers

        # Create transaction
        message = Message([transfer_ix])
        txn = Transaction.new_unsigned(message)
        txn.recent_blockhash = blockhash

        # Serialize transaction
        try:
            serialized_transaction = txn.serialize().hex()
        except Exception as e:
            logger.error(f"Failed to serialize transaction: {e}")
            return jsonify({"error": "Failed to create transaction"}), 500, headers

        logger.info(f"Payment transaction created successfully for {amount_sol} SOL")

        return jsonify({
            "transaction": serialized_transaction,
            "message": f"Payment of {amount_sol} SOL for {resource_id}"
        }), 200, headers

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format"}), 400, headers
    except Exception as e:
        logger.error(f"Unexpected error in payment processing: {e}")
        return jsonify({"error": "Internal server error"}), 500, headers


@payment_app.route("/health")
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "payment_processor",
        "rpc_endpoint": RPC_ENDPOINT
    }), 200


if __name__ == "__main__":
    # Development server configuration
    debug_mode = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    port = int(os.getenv("FLASK_PORT", 5001))

    logger.info(f"Starting payment service on port {port} (debug={debug_mode})")
    logger.info(f"Valid resource IDs: {VALID_RESOURCE_IDS}")
    logger.info(f"Payment wallet: {PAYMENT_WALLET.pubkey()}")

    payment_app.run(
        debug=debug_mode,
        port=port,
        host="0.0.0.0"  # Allow external connections
    )