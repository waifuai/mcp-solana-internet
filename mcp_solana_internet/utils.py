"""
Utility functions for the MCP Solana Internet payment system.

This module provides helper functions for:
- Solana-specific operations (key validation, amount conversion)
- Payment processing utilities (fee estimation, validation)
- Logging setup and configuration
- Data formatting and display utilities

Key utility functions:
- sol_to_lamports/lamports_to_sol: Convert between SOL and lamports
- validate_pubkey/validate_signature: Validate Solana keys and signatures
- format_sol_amount: Format SOL amounts with proper decimal places
- truncate_pubkey/truncate_signature: Display truncated keys/signatures
- calculate_transaction_fee_estimate: Estimate transaction fees
- is_valid_resource_id: Validate resource IDs against allowed list
- get_payment_expiry_info: Get payment expiry information
- setup_logging: Configure logging for the application

These utilities are used throughout the payment system for common operations
and data validation tasks.
"""
# Utility functions for mcp_solana_internet

import logging
from typing import Optional, Dict, Any
from solders.pubkey import Pubkey
from solders.signature import Signature
from config import LAMPORTS_PER_SOL

logger = logging.getLogger(__name__)


def sol_to_lamports(sol_amount: float) -> int:
    """Convert SOL amount to lamports."""
    return int(sol_amount * LAMPORTS_PER_SOL)


def lamports_to_sol(lamports: int) -> float:
    """Convert lamports to SOL amount."""
    return lamports / LAMPORTS_PER_SOL


def validate_pubkey(pubkey_str: str) -> Optional[Pubkey]:
    """Validate and parse a Solana public key string."""
    try:
        return Pubkey.from_string(pubkey_str)
    except Exception as e:
        logger.error(f"Invalid public key '{pubkey_str}': {e}")
        return None


def validate_signature(signature_str: str) -> Optional[Signature]:
    """Validate and parse a Solana transaction signature string."""
    try:
        return Signature.from_string(signature_str)
    except Exception as e:
        logger.error(f"Invalid signature '{signature_str}': {e}")
        return None


def format_sol_amount(amount: float, decimals: int = 6) -> str:
    """Format SOL amount with specified decimal places."""
    return f"{amount:.{decimals}f}"


def truncate_pubkey(pubkey: Pubkey, length: int = 8) -> str:
    """Truncate a public key for display purposes."""
    pubkey_str = str(pubkey)
    if len(pubkey_str) <= length * 2:
        return pubkey_str
    return f"{pubkey_str[:length]}...{pubkey_str[-length:]}"


def truncate_signature(signature: Signature, length: int = 8) -> str:
    """Truncate a signature for display purposes."""
    sig_str = str(signature)
    if len(sig_str) <= length * 2:
        return sig_str
    return f"{sig_str[:length]}...{sig_str[-length:]}"


def calculate_transaction_fee_estimate(
    num_signatures: int = 1,
    num_readonly_signed_accounts: int = 0,
    num_readonly_unsigned_accounts: int = 0,
    num_instructions: int = 1,
    base_fee: int = 5000  # Base fee in lamports
) -> int:
    """Estimate transaction fee based on Solana's fee structure."""
    # This is a simplified estimation
    # In practice, you'd use getFeeForMessage RPC call
    signature_fee = num_signatures * 5000  # 5000 lamports per signature
    return signature_fee + base_fee


def is_valid_resource_id(resource_id: str, valid_resources: Dict[str, float]) -> bool:
    """Check if a resource ID is valid."""
    return resource_id in valid_resources


def get_payment_expiry_info(hours: int = 24) -> Dict[str, Any]:
    """Get payment expiry information."""
    from datetime import datetime, timedelta
    expiry_time = datetime.now() + timedelta(hours=hours)
    return {
        "expires_at": expiry_time.isoformat(),
        "hours_remaining": hours,
        "expired": False
    }


def setup_logging(name: str, level: str = "INFO") -> logging.Logger:
    """Set up logging configuration."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(name)