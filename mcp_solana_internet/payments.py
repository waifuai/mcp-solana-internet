from flask import Flask, request, jsonify
from urllib.parse import quote
from mcp_solana_internet.config import LAMPORTS_PER_SOL, PAYMENT_WALLET, RPC_ENDPOINT
 # Import from config
from solders.pubkey import Pubkey
from solders.hash import Hash as Blockhash
from solders.message import Message
from solders.transaction import Transaction
from solders.system_program import transfer, TransferParams
import httpx
import os

payment_app = Flask(__name__)


@payment_app.route("/process_payment_action", methods=["OPTIONS"])
def handle_options_process_payment():
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "3600",
    }
    return "", 204, headers


@payment_app.route("/process_payment_action", methods=["GET"])
def get_process_payment_action_metadata():
    metadata = {
        "type": "action",
        "icon": "URL_TO_YOUR_ICON",  # Replace with your icon URL
        "title": "Process Payment",
        "description": "Make a SOL payment to access content.",
        "label": "Pay with SOL",
        "input": [
            {"name": "amount_sol", "type": "number", "label": "Amount of SOL to pay"},
            {"name": "resource_id", "type": "string", "label": "Resource ID"},
        ],
    }
    headers = {"Access-Control-Allow-Origin": "*"}
    return jsonify(metadata), 200, headers


@payment_app.route("/process_payment_action", methods=["POST"])
async def post_process_payment_action():
    headers = {"Access-Control-Allow-Origin": "*"}
    try:
        user_input = request.get_json()
        amount_sol = user_input.get("amount_sol")
        resource_id = user_input.get("resource_id")

        if amount_sol is None or resource_id is None:
            return jsonify({"error": "Missing required parameters."}), 400, headers

        amount_lamports = int(amount_sol * LAMPORTS_PER_SOL)

        # Construct Solana transaction (direct SOL transfer)
        transfer_ix = transfer(
            TransferParams(
                from_pubkey=Pubkey.from_string("REPLACE_WITH_USER_PUBKEY"),  # Replace with user's public key
                to_pubkey=PAYMENT_WALLET.pubkey(),  # Or a dedicated payment receiving address
                lamports=amount_lamports,
            )
        )

        # Get latest blockhash
        async with httpx.AsyncClient() as client:
            blockhash_resp = await client.get(
                RPC_ENDPOINT,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getLatestBlockhash",
                    "params": [{"commitment": "finalized"}],
                },
            )
            blockhash_resp.raise_for_status()
            blockhash_str = blockhash_resp.json()["result"]["value"]["blockhash"]
            blockhash = Blockhash.from_string(blockhash_str)

        message = Message([transfer_ix])
        txn = Transaction.new_unsigned(message)
        txn.recent_blockhash = blockhash

        # Serialize the transaction
        serialized_transaction = txn.serialize().hex()

        return jsonify({"transaction": serialized_transaction}), 200, headers

    except Exception as e:
        return jsonify({"error": str(e)}), 500, headers


if __name__ == "__main__":
    payment_app.run(debug=True, port=5001)  # Different port from the main server