"""
Configuration module for the MCP Solana Internet payment system.

This module handles:
- Loading environment variables for Solana RPC endpoint and payment wallet configuration
- Creating and validating the payment wallet from environment variables
- Setting up logging configuration for the entire application
- Validating all required configuration on import

The module supports multiple seed formats for the payment wallet:
- Comma-separated integers: "1,2,3,4,..."
- Hex string format: "0x1234567890abcdef..."

Environment variables required:
- RPC_ENDPOINT: Solana RPC endpoint URL (default: http://localhost:8899)
- PAYMENT_WALLET_SEED: Payment wallet seed in supported format
- FLASK_DEBUG: Flask debug mode setting
- FLASK_PORT: Flask server port (default: 5001)
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv
from solders.keypair import Keypair

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# --- Configuration ---
# Solana RPC endpoint configuration
RPC_ENDPOINT = os.getenv("RPC_ENDPOINT", "http://localhost:8899")
if not RPC_ENDPOINT.startswith(('http://', 'https://')):
    raise ValueError("RPC_ENDPOINT must be a valid HTTP/HTTPS URL")

# Payment wallet configuration
def create_payment_wallet() -> Keypair:
    """
    Create payment wallet from environment variable or use emergency seed.
    In production, use a secure key management system.
    """
    seed_str = os.getenv("PAYMENT_WALLET_SEED")

    if not seed_str:
        logger.warning("PAYMENT_WALLET_SEED not found in environment. Using emergency seed for development only!")
        seed_bytes = bytes([1] * 32)
        return Keypair.from_seed(seed_bytes)

    try:
        # Support both comma-separated integers and hex string formats
        if ',' in seed_str:
            seed_values = [int(x.strip()) for x in seed_str.split(",")]
            if len(seed_values) != 32:
                raise ValueError(f"Expected 32 seed values, got {len(seed_values)}")
            seed_bytes = bytes(seed_values)
        elif seed_str.startswith('0x'):
            # Hex format
            seed_bytes = bytes.fromhex(seed_str[2:])
            if len(seed_bytes) != 32:
                raise ValueError(f"Expected 32 bytes from hex, got {len(seed_bytes)}")
        else:
            raise ValueError("Seed must be comma-separated integers or hex string starting with 0x")

        return Keypair.from_seed(seed_bytes)

    except (ValueError, TypeError) as e:
        logger.error(f"Invalid PAYMENT_WALLET_SEED format: '{seed_str}'. Error: {e}")
        logger.warning("Using emergency seed for development only!")
        seed_bytes = bytes([1] * 32)
        return Keypair.from_seed(seed_bytes)

PAYMENT_WALLET = create_payment_wallet()
LAMPORTS_PER_SOL = 10**9

# Validate configuration
def validate_config():
    """Validate that all required configuration is present and valid."""
    if not PAYMENT_WALLET:
        raise ValueError("Failed to create payment wallet")

    # Log configuration (without sensitive data)
    logger.info(f"RPC Endpoint: {RPC_ENDPOINT}")
    logger.info(f"Payment Wallet Pubkey: {PAYMENT_WALLET.pubkey()}")
    logger.info("Configuration loaded successfully")

# Validate on import
validate_config()