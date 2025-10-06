# PMCT - Praćenje Maloprodajnih Cijena Trgovaca

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> A comprehensive Python system for automatically collecting, processing, and storing retail price data from Croatian retailers' publicly available price files.

---

## 📋 Table of Contents

- [What Does This Project Do?](#what-does-this-project-do)
- [Why Does This Exist?](#why-does-this-exist)
- [Key Features](#key-features)
- [Supported Retailers](#supported-retailers)
- [Project Architecture](#project-architecture)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Data Flow](#data-flow)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 What Does This Project Do?

PMCT (Praćenje Maloprodajnih Cijena Trgovaca) is an automated system that collects retail price information from major Croatian retailers. Think of it as a digital assistant that visits retailer websites every day, downloads their price lists, reads through thousands of product prices, and organizes all this information into a structured database. Handles different file formats (CSV, XML, XLSX) and ensures the data is clean, validated, and ready for analysis.

---

## 🤔 Why Does This Exist?

Croatian retailers are legally required to publish their daily prices on their websites. This regulation aims to increase price transparency for consumers. However, this data exists in scattered locations across different websites, in various file formats, with inconsistent structures.

This project bridges that gap by:
- **Automating data collection** from multiple retailers
- **Standardizing diverse formats** into a unified structure
- **Validating data quality** to ensure accuracy
- **Storing historical data** for trend analysis
- **Providing a foundation** for price comparison tools and market analysis

---

## ✨ Key Features

### Automated Web Scraping
The system automatically visits retailer websites and downloads daily price files without manual intervention. It handles website availability checks, retries on failures, and manages different authentication requirements.

### Multi-Format Support
Retailers publish their data in different formats. PMCT handles:
- **CSV files** (comma, semicolon, and tab-separated)
- **XML files** (various schemas)
- **XLSX files** (Excel spreadsheets with multiple sheets)
- **ZIP archives** (containing multiple price files)

### Intelligent Data Processing
Each retailer structures their data differently. The system includes custom parsers for each retailer that:
- Extract relevant price information
- Handle special characters and encoding issues (Croatian diacritics: č, ć, š, ž, đ)
- Clean and normalize product names
- Validate prices and product codes
- Flag promotional prices and special offers

### Robust Error Handling
The system includes comprehensive logging and error recovery:
- Detailed logs for every operation
- Automatic retry mechanisms for network issues
- Graceful handling of malformed data
- Status tracking for each file processed

### Database Integration
All collected data is stored in an Oracle database with:
- Proper data validation using Pydantic models
- Relational structure linking retailers, stores, and products
- Historical price tracking
- Duplicate detection and handling

---

## 🏪 Supported Retailers

The system currently supports **18 Croatian retail chains**, each with custom integration logic:

| Retailer | Stores | File Format | Special Features |
|----------|--------|-------------|-----------------|
| Boso | 14+ | CSV | Special character handling |
| DM | 1 (Physical/Online) | XLSX | Multi-sheet workbooks |
| Eurospin | 30+ | CSV (ZIP) | Encoding fixes |
| Kaufland | 50+ | CSV | SSL certificate handling |
| Konzum | 180+ | CSV | Multi-page pagination |
| KTC | 30+ | CSV | Dynamic URL generation |
| Lidl | 110+ | CSV (ZIP) | ZIP archive extraction |
| Metro | 10+ | CSV | B2B format |
| NTL | 9+ | CSV | Historical data access |
| Plodine | 140+ | CSV (ZIP) | SSL special handling |
| Ribola | 60+ | XML | Custom XML schema |
| Spar | 140+ | CSV | Custom headers required |
| Studenac | 20+ | XML (ZIP) | 7-Zip extraction |
| Tommy | 80+ | CSV | API integration |
| Trgocentar | 6+ | XML | Alternative XML format |
| Trgovina Krk | 14+ | CSV | Encoding fixes |
| Vrutak | 4+ | XML | Supermarket/Hipermarket split |
| Žabac | 1 | CSV | Single-store format |

---

## 🏗️ Project Architecture

### Directory Structure

```
PMCT/
├── src/
│   ├── database/           # Database connection and operations
│   │   └── db_connection.py    # Oracle DB interface with logging
│   ├── lanci/             # Retailer-specific scrapers
│   │   ├── konzum/        # Konzum-specific logic
│   │   ├── lidl/          # Lidl-specific logic
│   │   ├── kaufland/      # Kaufland-specific logic
│   │   └── ...           # One folder per retailer
│   ├── logger/            # Logging system
│   │   └── Logger.py      # Custom logger with file output
│   ├── models/            # Data models
│   │   └── TrgovackiLanci.py  # Retailer enum definitions
│   ├── schemas/           # Pydantic data validation models
│   │   ├── CijenaDTO.py       # Price data structure
│   │   ├── DatotekaDTO.py     # File metadata structure
│   │   └── ProdajniObjektDTO.py  # Store information structure
│   └── utils/             # Utility functions
│       ├── data/          # Data processing utilities
│       ├── db/            # Database utilities
│       ├── web/           # Web scraping utilities
│       └── file_encoding.py   # Character encoding fixes
├── pyproject.toml         # Project dependencies and metadata
├── LICENSE               # MIT License
└── README.md            # This file
```

### Key Components Explained

**Web Scrapers** (`src/lanci/*/`): Each retailer has two main scripts:
- `*_web_scraper.py` - Downloads files from retailer websites
- `*_file_reader.py` - Processes already downloaded files from disk
- `*_utils.py` - Helper functions specific to that retailer

**Database Layer** (`src/database/`): Manages all database operations with built-in logging, connection pooling, and transaction management.

**Data Models** (`src/schemas/`): Pydantic models ensure data validation before database insertion. They automatically validate data types, check constraints, and clean input data.

**Utilities** (`src/utils/`): Shared functionality used across the project, including encoding fixes for Croatian characters, web request helpers, and data transformation functions.

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9 or higher** - [Download Python](https://www.python.org/downloads/)
- **Oracle Database** - Access to an Oracle database instance
- **Git** - [Download Git](https://git-scm.com/downloads)
- **7-Zip** (for Windows) - Required for Studenac retailer only

### Installation

**Step 1: Clone the Repository**

```bash
git clone https://github.hnb.hr/dkralj/PMCT.git
cd PMCT
```

**Step 2: Create a Virtual Environment**

Creating a virtual environment isolates your project dependencies from other Python projects on your system.

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

**Step 3: Install Dependencies**

```bash
pip install -e .
```

This installs all required packages listed in `pyproject.toml`, including:
- `pandas` - Data manipulation and CSV processing
- `beautifulsoup4` - HTML parsing for web scraping
- `requests` - HTTP library for downloading files
- `oracledb` - Oracle database connectivity
- `pydantic` - Data validation
- `lxml` - XML processing
- `chardet` - Character encoding detection

**Step 4: Configure Environment Variables**

Create a `.env` file in the project root directory with your database credentials and configuration:

```env
# Database Configuration
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_HOST=your_oracle_host:port/service_name

# Database Queries (SQL statements)
GET_ID_TL=SELECT id FROM db_table WHERE ? = :?
# ... (add other SQL queries as needed)

# Application Settings
APP_NAME=PMCT
LOG_DIR_NAME=Log
DATE_FORMAT=%d.%m.%Y
FILE_DATE=%Y-%m-%d

# Email Configuration (optional)
SENDER_MAIL_ADDRESS=your_email@example.com
```

---

## ⚙️ Configuration

### Database Setup

The system expects an Oracle database with the following table structure:

**pmct_trgovacki_lanac** - Retailer information
**pmct_prodajni_objekt** - Individual store locations
**pmct_datoteka** - Metadata about downloaded files
**pmct_cijena** - Individual product prices

Run your database migration scripts to create these tables before first use.

### Retailer Configuration

Each retailer's configuration is stored in `src/models/TrgovackiLanci.py`. This enum defines:
- Base URL and pricing page URL
- File format (CSV, XML, XLSX)
- CSV separator character
- Column names for price data

Example:
```python
KONZUM = (
    "https://www.konzum.hr",           # Base URL
    "https://www.konzum.hr/cjenici",   # Price page URL
    DatotekaFormatEnum.CSV,            # File format
    ["MALOPRODAJNA CIJENA", ...],      # Price column names
    ",",                               # CSV separator
)
```

---

## 💡 Usage Examples

### Example 1: Download Today's Prices from Konzum

```python
from datetime import datetime
from src.lanci.konzum.konzum_web_scraper import *

# The script automatically:
# 1. Connects to the database
# 2. Visits Konzum's website
# 3. Downloads all price files for today
# 4. Parses each file
# 5. Validates the data
# 6. Stores prices in the database
# 7. Logs all operations

# Simply run:
# python src/lanci/konzum/konzum_web_scraper.py
```

### Example 2: Process Historical Files from Disk

If you have previously downloaded files stored locally:

```python
from src.lanci.konzum.konzum_file_reader import *

# Edit the datum_cijena variable in the script:
datum_cijena = "26.09.2025"  # Set your target date

# Run:
# python src/lanci/konzum/konzum_file_reader.py
```

### Example 3: Add a New Retailer

To add support for a new retailer:

**Step 1:** Add retailer definition to `src/models/TrgovackiLanci.py`

```python
NEW_RETAILER = (
    "https://www.newretailer.hr",
    "https://www.newretailer.hr/prices",
    DatotekaFormatEnum.CSV,
    ["Price", "Product Name", "Barcode"],
    ";",
)
```

**Step 2:** Create retailer folder and scripts

```bash
mkdir src/lanci/newretailer
touch src/lanci/newretailer/newretailer_web_scraper.py
touch src/lanci/newretailer/newretailer_utils.py
```

**Step 3:** Implement scraping logic based on existing retailer examples.

---

## 🔄 Data Flow

Understanding how data moves through the system:

```
1. WEB SCRAPING PHASE
   ↓
   [Retailer Website] → Web Scraper → Downloads Files
   ↓
   Files saved to: C:/Cijene/{date}/{retailer_name}/

2. FILE PROCESSING PHASE
   ↓
   [Local Files] → Parser → Extracts Data
   ↓
   Creates DTO objects (Data Transfer Objects)

3. VALIDATION PHASE
   ↓
   [DTO Objects] → Pydantic Validators → Checks:
   - Price format (must be decimal, 2 places)
   - Product name (required, cleaned)
   - Barcode (8-13 digits)
   - Date (cannot be future)
   - Special characters (Croatian diacritics)

4. DATABASE PHASE
   ↓
   [Validated Data] → Database Connection → Stores:
   - File metadata (name, format, status)
   - Store information (address, city)
   - Product prices (current and historical)

5. LOGGING PHASE
   ↓
   [All Operations] → Logger → Creates:
   - Detailed log files
   - Error reports
   - Execution time statistics
   - Success/failure counts
```

---

## :toolbox: Development

### Coding Style Guidelines

This project follows these standards:

- **PEP 8** - Python's style guide for readable code
- **Black** - Automatic code formatting (line length: 88)
- **Type hints** - Use Python type annotations where possible
- **Docstrings** - Document all functions, classes, and modules
- **Meaningful names** - Variables and functions should be self-explanatory

Example of good code style:
```python
def get_product_prices(retailer: TrgLanci, date: str) -> List[CijenaDTO]:
    """
    Fetch product prices for a specific retailer and date.
    
    Args:
        retailer: The retailer enum (e.g., TrgLanci.KONZUM)
        date: Date in format 'dd.mm.YYYY'
    
    Returns:
        List of validated price objects
    
    Raises:
        ValueError: If date format is invalid
        RuntimeError: If retailer website is unavailable
    """
    # Implementation here
```

### Development Tools

Install development dependencies:

```bash
pip install -e ".[dev]"
```

This includes:
- `black` - Code formatter
- `mypy` - Static type checker
- `ruff` - Fast Python linter

Format your code before committing:
```bash
black src/
```

Check for type errors:
```bash
mypy src/
```

---

## 📊 Project Status

**Current Version:** 1.0.0

**Active Development:** This project is actively maintained and regularly updated to handle changes in retailer websites and data formats.

**Supported Retailers:** 18 major Croatian retail chains

**Database Records:** Capable of processing millions of price records daily

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**What does this mean?**
- ✅ You can use this code commercially
- ✅ You can modify and distribute the code
- ✅ You can use it privately
- ⚠️ You must include the original license and copyright notice
- ❌ The software is provided "as is" without warranty

---

## 📧 Contact & Support

**Project Maintainer:** Dino Kralj (dino.kralj@hnb.hr)

---
