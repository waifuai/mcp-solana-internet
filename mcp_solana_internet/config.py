import os
from dotenv import load_dotenv
from solders.keypair import Keypair

load_dotenv()

# --- Configuration ---
RPC_ENDPOINT = os.getenv("RPC_ENDPOINT", "http://localhost:8899")
# Placeholder: In a real application, use a secure key management system.
# Generate the seed bytes correctly
seed_str = os.getenv("PAYMENT_WALLET_SEED", ",".join(["1"] * 32))
try:
    seed_bytes = bytes([int(x) for x in seed_str.split(",")])
    if len(seed_bytes) != 32:
        raise ValueError("Seed must be 32 bytes long.")
except (ValueError, TypeError):
    print(f"Warning: Invalid PAYMENT_WALLET_SEED format: '{seed_str}'. Using default emergency seed.")
    seed_bytes = bytes([1] * 32) # Default emergency seed

PAYMENT_WALLET = Keypair.from_seed(seed_bytes)
LAMPORTS_PER_SOL = 10**9