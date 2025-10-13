# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python library for integration with ATOL fiscal cash register equipment through the ATOL Driver v.10 (libfptr10). The library provides a complete Python wrapper around the ATOL driver for fiscal operations, receipt creation, shift management, and device information retrieval.

**Primary Integration Method**: ATOL Driver v.10 (libfptr10) - Direct hardware communication
**Supported Models**: ATOL 42FS, 30F, 50F, 55F, 60F, 90F, 91F, 92F
**Connection Types**: TCP/IP, USB, Serial (COM-port), Bluetooth

## Development Commands

### Testing
```bash
# Run all tests
make test
# or
pytest tests/ -v

# Run tests with coverage
make test-cov
# or
pytest --cov=atol_integration --cov-report=html

# Run specific test suites
pytest tests/unit/        # Unit tests only
pytest tests/integration/ # Integration tests only
```

### Code Quality
```bash
# Format code (Black)
make format
# or
black atol_integration/ tests/ examples/

# Lint code (flake8 + mypy)
make lint
# or
flake8 atol_integration/ tests/ examples/
mypy atol_integration/

# Clean build artifacts and cache
make clean
```

### Running Examples
```bash
make run-example
# or
python examples/basic_usage.py
```

### Installation
```bash
# Install dependencies
make install
# or
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

## Architecture

### API Layer (`atol_integration/api/`)

**Primary integration class:**

- **`AtolDriver`** (`driver.py`): Complete Python wrapper for ATOL Driver v.10 (libfptr10)
  - Handles all fiscal device operations through native driver
  - Supports multiple connection types (TCP/IP, USB, Serial, Bluetooth)
  - Receipt operations: open, add items, payments, close, cancel
  - Shift management: open, close, get status, X/Z reports
  - Correction receipts: self-initiated and by prescription
  - Cash operations: income/outcome
  - Device info and status queries
  - Context manager support for automatic connection/disconnection
  - Comprehensive error handling with AtolDriverError exceptions

**Legacy/Alternative clients** (not yet fully implemented):

- **`AtolClient`** (`client.py`): Cloud API client for ATOL Online API (v5) - stub implementation
- **`AtolWebServer`** (`web_server.py`): Local API client for ATOL Web Server - stub implementation

### Models Layer (`atol_integration/models/`)

Domain models using dataclasses and IntEnum for type safety:

- **`Receipt`** (`receipt.py`): Core fiscal document model
  - Contains items, payments, and contact info
  - Supports all fiscal operations: sell, sell_return, buy, buy_return, corrections
  - Calculates total automatically from items

- **`Item`**: Individual receipt line item with comprehensive fiscal attributes
  - Price, quantity, VAT type
  - Payment method type (prepayment, advance, full payment, credit, etc.)
  - Payment object type (commodity, service, job, etc.)
  - Measure unit and department
  - Auto-calculates amount on initialization

- **`Payment`**: Payment information with type (cash, electronic, prepaid, credit, other)

- **`DeviceInfo`** (`device.py`): Cash register hardware information
  - Serial numbers, model, firmware version, fiscal drive number

**Important Enums** (all IntEnum for driver compatibility):
- `ReceiptType`: SELL=0, SELL_RETURN=1, BUY=2, BUY_RETURN=3, SELL_CORRECTION=4, BUY_CORRECTION=5
- `PaymentType`: CASH=0, ELECTRONICALLY=1, PREPAID=2, CREDIT=3, OTHER=4
- `TaxType`: NONE=0, VAT0=1, VAT10=2, VAT20=3, VAT110=4, VAT120=5
- `PaymentMethodType`: Values 1-7 for different payment methods per 54-FZ
- `PaymentObjectType`: Values 1-13 for item classification per 54-FZ

### Services Layer (`atol_integration/services/`)

Business logic that orchestrates API calls and model operations:

- **`FiscalService`** (`fiscal_service.py`): Handles fiscal operations workflow
  - Wraps AtolClient for receipt fiscalization
  - Tracks fiscalization status

### Configuration (`atol_integration/config/`)

- **`Settings`** (`settings.py`): Pydantic-based configuration using environment variables
  - ATOL API credentials and endpoints
  - ATOL Web Server connection parameters
  - Company information (INN, email, payment address)
  - Directory paths for logs, cache, receipts
  - Loads from `.env` file

- **Constants** (`constants.py`): Supported models list, timeouts, API versions, FFD version

## Key Implementation Notes

### API Integration Pattern

**Primary Method: ATOL Driver v.10**

The library now uses the ATOL Driver v.10 (libfptr10) as the primary integration method:
- Direct hardware communication with fiscal devices
- No dependency on web services or cloud APIs
- Works offline
- Supports multiple connection types (TCP/IP, USB, Serial, Bluetooth)
- Full compliance with 54-FZ federal law requirements

**Driver Installation Required:**
- Download from: https://fs.atol.ru/
- Install the driver before using this library
- The driver provides the `libfptr10` Python module

### Receipt Creation Flow with Driver

Basic workflow:
1. Create `AtolDriver` instance
2. Connect to device: `driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)`
3. Check/open shift: `driver.open_shift("Cashier Name")`
4. Open receipt: `driver.open_receipt(ReceiptType.SELL, "Cashier")`
5. Add items: `driver.add_item("Product", price, quantity, TaxType.VAT20)`
6. Add payments: `driver.add_payment(total, PaymentType.CASH)`
7. Close receipt: `result = driver.close_receipt()` - returns fiscal data
8. Disconnect: `driver.disconnect()`

**Context Manager Pattern (Recommended):**
```python
with AtolDriver() as driver:
    driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)
    # ... perform operations
    # automatic disconnect on exit
```

### Configuration Management

Settings are loaded via Pydantic from `.env` file. Required environment variables:
- `atol_api_url`, `atol_login`, `atol_password`, `atol_group_code`
- `atol_ws_host`, `atol_ws_port` (for local server)
- `company_inn`, `company_payment_address`, `company_email`

Access via: `from atol_integration.config.settings import settings`

### VAT Handling

VAT types defined in `TaxType` enum (IntEnum):
- NONE=0: Without VAT
- VAT0=1: VAT 0%
- VAT10=2: VAT 10%
- VAT20=3: VAT 20%
- VAT110=4: VAT 10/110 (calculated VAT)
- VAT120=5: VAT 20/120 (calculated VAT)

Russian fiscal requirements (54-FZ) must be met for all items.

### Error Handling

All driver operations can raise `AtolDriverError` exceptions. Always wrap operations in try-except:
```python
try:
    driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)
    # ... operations
except AtolDriverError as e:
    logger.error(f"Driver error: {e}")
    # Handle error, possibly cancel receipt
```

### Driver Parameter Constants

The driver uses numeric parameter codes (from libfptr10). Key constants:
- 1001: Data type / Receipt type / Payment type
- 1021: Operator (cashier) name
- 1030: Item name
- 1000: Price
- 1023: Quantity
- 1031: Sum (payment amount)
- 1199: Tax type
- 1008: Customer contact (email/phone)
- 1173-1179: Correction receipt parameters

Refer to `driver.py` for complete parameter list and usage.

## Current Implementation Status

**Fully Implemented (v0.2.0, Beta):**
- Complete AtolDriver wrapper for libfptr10
- All receipt operations (sell, return, buy, corrections)
- Shift management (open, close, status, reports)
- Cash operations (income, outcome)
- Device information queries
- Multiple connection types
- Context manager support
- Comprehensive examples

**Not Yet Implemented:**
- AtolClient (cloud API) - stub only
- AtolWebServer (local web server) - stub only
- FiscalService business logic layer
- DeviceInfo.from_dict() method
- Unit and integration tests

When extending this library, refer to:
- ATOL Driver documentation: https://integration.atol.ru/api/
- 54-FZ federal law requirements
- Examples in `examples/driver_*.py`

## Dependencies

**Core:**
- requests>=2.31.0
- pydantic>=2.0.0
- python-dotenv>=1.0.0
- libfptr10 (provided by ATOL Driver installation)

**Development:**
- pytest>=7.4.0
- pytest-cov>=4.1.0
- black>=23.0.0
- flake8>=6.0.0
- mypy>=1.5.0

**Documentation:**
- sphinx>=7.0.0
- sphinx-rtd-theme>=1.3.0

**Python Version:** >=3.8 (tested on 3.8-3.12)

## Examples

See `examples/` directory:
- `driver_basic_usage.py` - Simple sale receipt example with TCP connection
- `driver_advanced_usage.py` - Complete examples including:
  - Return receipts
  - Mixed payments (cash + card)
  - Correction receipts
  - Cash operations
  - Shift management
  - Various connection types (USB, Serial, Bluetooth)
  - Context manager usage
