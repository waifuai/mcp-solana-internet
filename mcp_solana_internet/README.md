# MCP Solana Internet - Enhanced Payment System

A robust Solana-based payment system with MCP (Model Context Protocol) integration for processing payments and managing resource access.

## 🚀 Features

- **Solana Blockchain Integration**: Direct SOL transfers with on-chain validation
- **MCP Server**: Tools for access control and payment processing
- **Flask Payment API**: RESTful endpoints for payment actions
- **Resource Management**: Configurable resource prices and access control
- **Payment History**: In-memory payment tracking with expiry
- **Comprehensive Validation**: Input validation, transaction verification, and error handling
- **Logging**: Detailed logging for debugging and monitoring
- **CORS Support**: Cross-origin request handling for web integration

## 📁 Project Structure

```
.
├── config.py          # Configuration and wallet management
├── payments.py        # Flask payment API endpoints
├── server.py          # MCP server with payment tools
├── utils.py           # Utility functions for Solana operations
├── __init__.py        # Package initialization
├── .env              # Environment variables (create this)
└── README.md         # This file
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Solana RPC endpoint
RPC_ENDPOINT=http://localhost:8899

# Payment wallet seed (comma-separated integers or hex with 0x prefix)
# Example: PAYMENT_WALLET_SEED=1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32
# Or hex: PAYMENT_WALLET_SEED=0x1234567890abcdef...

# Flask configuration
FLASK_DEBUG=true
FLASK_PORT=5001
```

### Resource Prices

Resources and their prices are configured in `server.py`:

```python
resource_prices = {
    "resource_1": 0.1,
    "resource_2": 0.5,
    "premium_content": 1.0,
    "basic_content": 0.05,
    "pro_content": 2.0,
}
```

## 🛠️ Installation

1. **Install dependencies:**
```bash
# Using uv (recommended)
python -m uv venv .venv
source .venv/Scripts/activate  # On Windows
.venv/Scripts/python.exe -m uv pip install -e .
```

2. **Set up environment variables:**
Create a `.env` file with the required configuration.

3. **Run the services:**

Start the payment API server:
```bash
python payments.py
```

Start the MCP server (in another terminal):
```bash
python server.py
```

## 💰 Payment Flow

### 1. Check Access
Use the MCP `check_access` tool to verify if a user has paid for a resource:

```python
# Check if user has access to premium content
result = await check_access(
    user_pubkey="UserPublicKeyHere",
    resource_id="premium_content"
)
```

### 2. Process Payment
If access is denied, the user needs to make a payment:

```python
# Process a completed payment transaction
result = await process_payment(
    amount_sol=1.0,
    payment_transaction="TransactionSignatureHere",
    client_ip="127.0.0.1",
    resource_id="premium_content",
    user_pubkey="UserPublicKeyHere"
)
```

### 3. Payment API
The Flask API provides endpoints for Solana Actions:

- `GET /process_payment_action` - Get payment action metadata
- `POST /process_payment_action` - Create payment transaction
- `GET /health` - Health check

## 🔧 API Endpoints

### Payment Action Metadata
```http
GET /process_payment_action
```

Response:
```json
{
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
      "min": 0.001,
      "max": 1000
    },
    {
      "name": "resource_id",
      "type": "select",
      "label": "Resource ID",
      "options": [
        {"label": "Resource 1", "value": "resource_1"},
        {"label": "Resource 2", "value": "resource_2"},
        {"label": "Premium Content", "value": "premium_content"}
      ]
    }
  ]
}
```

### Create Payment Transaction
```http
POST /process_payment_action
Content-Type: application/json

{
  "amount_sol": 1.0,
  "resource_id": "premium_content",
  "account": "UserPublicKeyHere"
}
```

## 🛡️ Validation & Security

### Payment Validation
- **Amount Limits**: 0.001 SOL minimum, 1000 SOL maximum
- **Resource Validation**: Only predefined resources are accepted
- **Transaction Verification**: Full on-chain validation including:
  - Transaction existence
  - Correct destination address
  - Sufficient payment amount
  - Valid instruction structure

### Error Handling
- Comprehensive input validation
- Graceful error responses with detailed messages
- Proper HTTP status codes
- Detailed logging for debugging

## 📊 Payment History

### View Payment History
```python
# Get all payments for a user
history = await get_payment_history(
    user_pubkey="UserPublicKeyHere"
)

# Get payments for specific resource
history = await get_payment_history(
    user_pubkey="UserPublicKeyHere",
    resource_id="premium_content"
)
```

### Payment Expiry
- Payments expire after 24 hours by default
- Automatic cleanup of expired records
- Configurable expiry time via `PAYMENT_EXPIRY_HOURS`

## 🧪 Testing

### Health Check
```bash
curl http://localhost:5001/health
```

### Test Payment Flow
1. Check access for a resource
2. If denied, create a payment transaction
3. Submit the signed transaction
4. Verify access is now granted

## 🔍 MCP Tools

### Available Tools

1. **`check_access`** - Check if user has paid for resource
2. **`process_payment`** - Process and validate SOL payment
3. **`get_resource_info`** - Get resource prices and information
4. **`get_payment_history`** - View user's payment history

### Tool Usage Example

```python
from mcp_solana_internet import check_access, process_payment

# Check access
access_result = await check_access(
    user_pubkey="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    resource_id="premium_content"
)

if not access_result["access"]:
    print(f"Payment required: {access_result['payment_amount_sol']} SOL")
    print(f"Payment URL: {access_result['payment_url']}")
```

## 🐛 Troubleshooting

### Common Issues

1. **"Invalid public key"**: Ensure the public key is a valid Solana address (32 bytes, base58 encoded)

2. **"Transaction not found"**: The transaction may not be confirmed yet. Wait for confirmation.

3. **"Insufficient payment"**: The payment amount is less than required for the resource.

4. **"RPC Error"**: Check that the Solana RPC endpoint is accessible and functioning.

### Logs
Check the console output for detailed error messages and transaction information.

## 📝 Development

### Adding New Resources
1. Add the resource to `resource_prices` in `server.py`
2. Update the `VALID_RESOURCE_IDS` in `payments.py`

### Custom Validation
Extend the validation functions in `utils.py` for custom business logic.

### Database Integration
For production use, replace the in-memory payment storage with a proper database.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT-0 License - see the LICENSE file for details.

## ⚠️ Production Considerations

1. **Security**: Use environment variables for sensitive configuration
2. **Database**: Replace in-memory storage with a persistent database
3. **Monitoring**: Add proper logging and monitoring
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Backup**: Regular backups of payment records
6. **Key Management**: Use secure key management systems for production wallets