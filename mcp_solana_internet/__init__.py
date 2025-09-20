"""
MCP Solana Internet - A Solana-based payment system with MCP integration.

This package provides:
- Solana blockchain payment processing
- Resource access control based on payments
- MCP server integration for external tools
- Flask-based payment API endpoints

Main components:
- config.py: Configuration and wallet management
- payments.py: Flask payment API endpoints
- server.py: MCP server with payment tools
- utils.py: Utility functions for Solana operations
"""

__version__ = "1.0.0"
__author__ = "MCP Solana Internet Team"
__description__ = "Solana payment system with MCP integration"

# Import main components for easy access
from .config import (
    RPC_ENDPOINT,
    PAYMENT_WALLET,
    LAMPORTS_PER_SOL,
    create_payment_wallet,
    validate_config
)

from .utils import (
    sol_to_lamports,
    lamports_to_sol,
    validate_pubkey,
    validate_signature,
    format_sol_amount,
    truncate_pubkey,
    truncate_signature,
    calculate_transaction_fee_estimate,
    setup_logging
)

# Make commonly used items available at package level
__all__ = [
    "RPC_ENDPOINT",
    "PAYMENT_WALLET",
    "LAMPORTS_PER_SOL",
    "create_payment_wallet",
    "validate_config",
    "sol_to_lamports",
    "lamports_to_sol",
    "validate_pubkey",
    "validate_signature",
    "format_sol_amount",
    "truncate_pubkey",
    "truncate_signature",
    "calculate_transaction_fee_estimate",
    "setup_logging"
]