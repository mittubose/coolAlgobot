"""
CSV Import Parser for Portfolio Trades
Supports: Zerodha, Upstox, ICICI, Generic formats
Enhanced with flexible column detection, fuzzy matching, and data cleaning
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid
import re
from difflib import SequenceMatcher


class CSVImportParser:
    """
    Universal CSV parser for broker trade reports

    Supported Brokers:
    - Zerodha (tradebook.csv)
    - Upstox (trade_report.csv)
    - ICICI Direct (trade_history.csv)
    - Generic (custom CSV with required columns)
    """

    # Column mappings for different brokers
    BROKER_MAPPINGS = {
        'zerodha': {
            'trade_date': 'trade_date',
            'symbol': 'symbol',
            'exchange': 'exchange',
            'action': 'trade_type',  # BUY/SELL
            'quantity': 'quantity',
            'price': 'price',
            'order_id': 'order_id',
            'trade_id': 'trade_id',
            # Charges
            'brokerage': 'brokerage',
            'stt': 'stt_ctt',
            'exchange_charges': 'exchange_txn_charge',
            'gst': 'gst',
            'sebi_charges': 'sebi_turnover_fee',
            'stamp_duty': 'stamp_duty'
        },
        'upstox': {
            'trade_date': 'Trade Date',
            'symbol': 'Symbol',
            'exchange': 'Exchange',
            'action': 'Transaction Type',  # Buy/Sell
            'quantity': 'Quantity',
            'price': 'Price',
            'order_id': 'Order No',
            'trade_id': 'Trade No',
            # Charges (Upstox combines them differently)
            'brokerage': 'Brokerage',
            'stt': 'STT',
            'exchange_charges': 'Transaction Charges',
            'gst': 'GST',
            'sebi_charges': 'SEBI Charges',
            'stamp_duty': 'Stamp Duty'
        },
        'icici': {
            'trade_date': 'Trade Date',
            'symbol': 'Symbol',
            'exchange': 'Exchange',
            'action': 'Buy/Sell',
            'quantity': 'Qty',
            'price': 'Rate',
            'order_id': 'Order Number',
            'trade_id': 'Trade Number',
            # ICICI has different charge structure
            'brokerage': 'Brokerage',
            'stt': 'STT',
            'exchange_charges': 'Transaction Charge',
            'gst': 'Service Tax',
            'sebi_charges': 'SEBI Fee',
            'stamp_duty': 'Stamp Duty'
        },
        'groww': {
            'trade_date': 'Date',
            'symbol': 'Stock',
            'exchange': 'Exchange',
            'action': 'Type',  # Buy/Sell
            'quantity': 'Quantity',
            'price': 'Price',
            'order_id': 'Order ID',
            'trade_id': 'Trade ID',
            # Charges
            'brokerage': 'Brokerage',
            'stt': 'STT',
            'exchange_charges': 'Transaction Charges',
            'gst': 'GST',
            'sebi_charges': 'SEBI Charges',
            'stamp_duty': 'Stamp Duty'
        },
        'generic': {
            # Generic format (user must ensure column names match)
            'trade_date': 'date',
            'symbol': 'symbol',
            'exchange': 'exchange',
            'action': 'action',  # Must be BUY or SELL
            'quantity': 'quantity',
            'price': 'price',
            'order_id': 'order_id',
            'trade_id': 'trade_id',
            # Optional charges
            'brokerage': 'brokerage',
            'stt': 'stt',
            'exchange_charges': 'exchange_charges',
            'gst': 'gst',
            'sebi_charges': 'sebi_charges',
            'stamp_duty': 'stamp_duty'
        }
    }

    # Fuzzy matching keywords for column detection
    COLUMN_KEYWORDS = {
        'trade_date': ['date', 'trade_date', 'tradedate', 'transaction_date', 'txn_date', 'dt', 'day'],
        'symbol': ['symbol', 'stock', 'scrip', 'instrument', 'ticker', 'code', 'name', 'security'],
        'exchange': ['exchange', 'exch', 'market', 'seg', 'segment'],
        'action': ['action', 'type', 'trade_type', 'tradetype', 'transaction', 'buy_sell', 'side', 'order_type'],
        'quantity': ['quantity', 'qty', 'volume', 'shares', 'units', 'lot', 'amount'],
        'price': ['price', 'rate', 'avg_price', 'trade_price', 'execution_price', 'ltp', 'value'],
        'order_id': ['order_id', 'orderid', 'order_no', 'orderno', 'order_number', 'ref'],
        'trade_id': ['trade_id', 'tradeid', 'trade_no', 'tradeno', 'trade_number', 'execution_id'],
        'brokerage': ['brokerage', 'broker', 'commission', 'fees'],
        'stt': ['stt', 'stt_ctt', 'securities_transaction_tax'],
        'exchange_charges': ['exchange_charges', 'exchange_txn_charge', 'transaction_charges', 'exch_charges'],
        'gst': ['gst', 'tax', 'service_tax', 'goods_and_services_tax'],
        'sebi_charges': ['sebi_charges', 'sebi_turnover_fee', 'sebi_fee', 'regulatory_fee'],
        'stamp_duty': ['stamp_duty', 'stamp', 'duty']
    }

    def __init__(self, broker: str = 'zerodha', flexible_mode: bool = True):
        """
        Initialize parser with broker configuration

        Args:
            broker: Broker name (zerodha, upstox, icici, generic, groww)
            flexible_mode: Enable flexible column detection with fuzzy matching
        """
        self.broker = broker.lower()
        self.flexible_mode = flexible_mode

        if not flexible_mode and self.broker not in self.BROKER_MAPPINGS:
            raise ValueError(f"Unsupported broker: {broker}. Choose from {list(self.BROKER_MAPPINGS.keys())}")

        self.column_mapping = self.BROKER_MAPPINGS.get(self.broker, {})
        self.import_batch_id = str(uuid.uuid4())
        self.detected_columns = {}  # Store detected column mappings

    def parse_csv(self, file_path: str, portfolio_id: int) -> Tuple[List[Dict], Dict]:
        """
        Parse CSV or Excel file and return list of trade dictionaries
        Enhanced with flexible column detection, data cleaning, and sorting

        Args:
            file_path: Path to CSV or Excel file (.csv, .xlsx, .xls)
            portfolio_id: Portfolio ID to associate trades with

        Returns:
            Tuple of (trades_list, import_stats)
        """
        try:
            # Read CSV or Excel based on file extension
            file_ext = file_path.lower().split('.')[-1]

            if file_ext in ['xlsx', 'xls']:
                # Read Excel file
                df = pd.read_excel(file_path, engine='openpyxl' if file_ext == 'xlsx' else 'xlrd')
                print(f"✅ Read Excel file: {len(df)} rows")
            elif file_ext == 'csv':
                # Read CSV file (try different encodings)
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file_path, encoding='latin-1')
                    except:
                        df = pd.read_csv(file_path, encoding='iso-8859-1')
                print(f"✅ Read CSV: {len(df)} rows")
            else:
                raise ValueError(f"Unsupported file format: .{file_ext}. Supported: .csv, .xlsx, .xls")

            # Clean the dataframe
            df = self._clean_dataframe(df)
            print(f"🧹 Cleaned data: {len(df)} rows remaining")

            # Auto-detect broker if generic or flexible mode
            if self.broker == 'generic' or self.flexible_mode:
                self.broker = self._detect_broker(df)
                self.column_mapping = self.BROKER_MAPPINGS.get(self.broker, {})
                print(f"🔍 Auto-detected broker: {self.broker}")

            # Intelligent column mapping (flexible mode)
            if self.flexible_mode:
                self._detect_column_mapping(df)
                print(f"🎯 Mapped columns: {len(self.detected_columns)} fields detected")

            # Validate required columns (flexible validation)
            self._validate_columns(df)

            # Parse trades
            trades = []
            failed_rows = []

            for idx, row in df.iterrows():
                try:
                    trade = self._parse_row(row, portfolio_id)
                    trades.append(trade)
                except Exception as e:
                    failed_rows.append({
                        'row_index': idx,
                        'error': str(e),
                        'data': row.to_dict()
                    })

            # Sort trades by date (oldest first)
            if trades:
                trades.sort(key=lambda x: x['trade_date'])
                print(f"📅 Sorted trades by date")

            # Import stats
            stats = {
                'total_rows': len(df),
                'success_rows': len(trades),
                'failed_rows': len(failed_rows),
                'skipped_rows': 0,
                'import_batch_id': self.import_batch_id,
                'broker': self.broker,
                'failed_records': failed_rows,
                'start_date': min([t['trade_date'] for t in trades]) if trades else None,
                'end_date': max([t['trade_date'] for t in trades]) if trades else None,
                'column_mapping': self.detected_columns if self.flexible_mode else self.column_mapping
            }

            print(f"✅ Parsed {stats['success_rows']} trades successfully")
            if stats['failed_rows'] > 0:
                print(f"⚠️  Failed to parse {stats['failed_rows']} rows")

            return trades, stats

        except Exception as e:
            raise Exception(f"CSV parsing failed: {str(e)}")

    def _detect_broker(self, df: pd.DataFrame) -> str:
        """
        Auto-detect broker from CSV columns

        Args:
            df: Pandas DataFrame

        Returns:
            Detected broker name
        """
        columns = set(df.columns)

        # Check for Zerodha columns
        if 'trade_date' in columns and 'order_id' in columns and 'trade_id' in columns:
            return 'zerodha'

        # Check for Upstox columns
        if 'Trade Date' in columns and 'Order No' in columns:
            return 'upstox'

        # Check for ICICI columns
        if 'Trade Date' in columns and 'Order Number' in columns:
            return 'icici'

        # Default to generic
        return 'generic'

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean dataframe by removing empty rows, trimming whitespace, etc.

        Args:
            df: Pandas DataFrame

        Returns:
            Cleaned DataFrame
        """
        # Remove completely empty rows
        df = df.dropna(how='all')

        # Remove rows where all values are empty strings
        df = df[~df.map(lambda x: str(x).strip() == '').all(axis=1)]

        # Strip whitespace from column names
        df.columns = df.columns.str.strip()

        # Strip whitespace from string columns
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(lambda x: str(x).strip() if pd.notna(x) else x)

        # Remove duplicate rows
        df = df.drop_duplicates()

        # Reset index
        df = df.reset_index(drop=True)

        return df

    def _fuzzy_match(self, text: str, keywords: List[str], threshold: float = 0.6) -> Optional[str]:
        """
        Fuzzy match text against a list of keywords

        Args:
            text: Text to match
            keywords: List of keywords to match against
            threshold: Similarity threshold (0-1)

        Returns:
            Best matching keyword or None
        """
        text_lower = text.lower().strip()

        # Exact match first
        for keyword in keywords:
            if text_lower == keyword.lower():
                return keyword

        # Fuzzy match
        best_match = None
        best_score = 0.0

        for keyword in keywords:
            # Calculate similarity ratio
            ratio = SequenceMatcher(None, text_lower, keyword.lower()).ratio()

            # Check if text contains keyword or vice versa
            contains_score = 0.0
            if keyword.lower() in text_lower:
                contains_score = 0.8
            elif text_lower in keyword.lower():
                contains_score = 0.7

            score = max(ratio, contains_score)

            if score > best_score and score >= threshold:
                best_score = score
                best_match = keyword

        return best_match

    def _detect_column_mapping(self, df: pd.DataFrame) -> None:
        """
        Intelligently detect column mapping using fuzzy matching

        Args:
            df: Pandas DataFrame

        Updates:
            self.detected_columns with detected mappings
        """
        self.detected_columns = {}

        for field, keywords in self.COLUMN_KEYWORDS.items():
            for col in df.columns:
                matched = self._fuzzy_match(col, keywords, threshold=0.6)
                if matched:
                    self.detected_columns[field] = col
                    print(f"   ✓ {field}: '{col}' (matched: '{matched}')")
                    break

        # Update column mapping with detected columns
        if self.detected_columns:
            self.column_mapping.update(self.detected_columns)

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """
        Validate that required columns exist in CSV
        Enhanced with flexible validation in flexible mode

        Args:
            df: Pandas DataFrame

        Raises:
            ValueError: If required columns are missing
        """
        required_fields = ['trade_date', 'symbol', 'action', 'quantity', 'price']
        missing_columns = []

        if self.flexible_mode:
            # In flexible mode, check detected columns
            for field in required_fields:
                if field not in self.column_mapping or self.column_mapping[field] not in df.columns:
                    missing_columns.append(field)
        else:
            # Strict validation
            for field in required_fields:
                broker_column = self.column_mapping.get(field)
                if broker_column is None or broker_column not in df.columns:
                    missing_columns.append(field)

        if missing_columns:
            # Provide helpful error message
            available_columns = list(df.columns)
            error_msg = f"Missing required columns: {missing_columns}\n"
            error_msg += f"Available columns in file: {available_columns}\n"
            error_msg += "\nRequired fields:\n"
            error_msg += "  - trade_date: Date of trade\n"
            error_msg += "  - symbol: Stock symbol/name\n"
            error_msg += "  - action: BUY or SELL\n"
            error_msg += "  - quantity: Number of shares\n"
            error_msg += "  - price: Price per share"
            raise ValueError(error_msg)

    def _parse_row(self, row: pd.Series, portfolio_id: int) -> Dict:
        """
        Parse a single CSV row into trade dictionary

        Args:
            row: Pandas Series (CSV row)
            portfolio_id: Portfolio ID

        Returns:
            Trade dictionary ready for database insertion
        """
        # Get column mapping
        cm = self.column_mapping

        # Parse trade date
        trade_date_str = str(row[cm['trade_date']])
        trade_date = self._parse_date(trade_date_str)

        # Parse action (normalize to BUY/SELL)
        action = str(row[cm['action']]).upper().strip()
        if action in ['B', 'BUY', 'BOUGHT']:
            action = 'BUY'
        elif action in ['S', 'SELL', 'SOLD']:
            action = 'SELL'
        else:
            raise ValueError(f"Invalid action: {action}. Must be BUY or SELL")

        # Parse numeric fields
        quantity = int(row[cm['quantity']])
        price = float(row[cm['price']])

        # Optional charges (default to 0 if not present)
        brokerage = self._safe_float(row, cm.get('brokerage'), 0.0)
        stt = self._safe_float(row, cm.get('stt'), 0.0)
        exchange_charges = self._safe_float(row, cm.get('exchange_charges'), 0.0)
        gst = self._safe_float(row, cm.get('gst'), 0.0)
        sebi_charges = self._safe_float(row, cm.get('sebi_charges'), 0.0)
        stamp_duty = self._safe_float(row, cm.get('stamp_duty'), 0.0)

        # Calculate total charges
        total_charges = brokerage + stt + exchange_charges + gst + sebi_charges + stamp_duty

        # Calculate trade values
        gross_value = quantity * price
        if action == 'BUY':
            net_value = gross_value + total_charges
        else:  # SELL
            net_value = gross_value - total_charges

        # Build trade dictionary
        trade = {
            'portfolio_id': portfolio_id,
            'symbol': str(row[cm['symbol']]).upper().strip(),
            'exchange': str(row[cm.get('exchange', '')]).upper().strip() if cm.get('exchange') else 'NSE',
            'trade_date': trade_date,
            'trade_time': None,  # Extract if available
            'action': action,
            'quantity': quantity,
            'price': price,
            'brokerage': brokerage,
            'stt': stt,
            'exchange_charges': exchange_charges,
            'gst': gst,
            'sebi_charges': sebi_charges,
            'stamp_duty': stamp_duty,
            'total_charges': total_charges,
            'gross_value': gross_value,
            'net_value': net_value,
            'import_source': f'{self.broker}_csv',
            'import_batch_id': self.import_batch_id,
            'order_id': self._safe_str(row, cm.get('order_id')),
            'trade_id': self._safe_str(row, cm.get('trade_id'))
        }

        return trade

    def _parse_date(self, date_str: str) -> str:
        """
        Parse date string to YYYY-MM-DD format

        Args:
            date_str: Date string in various formats

        Returns:
            Standardized date string (YYYY-MM-DD)
        """
        # Try multiple date formats
        formats = [
            '%Y-%m-%d',  # 2024-01-15
            '%d-%m-%Y',  # 15-01-2024
            '%d/%m/%Y',  # 15/01/2024
            '%m/%d/%Y',  # 01/15/2024
            '%Y/%m/%d',  # 2024/01/15
            '%d-%b-%Y',  # 15-Jan-2024
            '%d-%b-%y',  # 15-Jan-24
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue

        raise ValueError(f"Unable to parse date: {date_str}")

    def _safe_float(self, row: pd.Series, column: Optional[str], default: float = 0.0) -> float:
        """
        Safely extract float value from row

        Args:
            row: Pandas Series
            column: Column name (can be None)
            default: Default value if column missing

        Returns:
            Float value
        """
        if column is None or column not in row.index:
            return default

        value = row[column]
        if pd.isna(value) or value == '' or value is None:
            return default

        try:
            return float(value)
        except:
            return default

    def _safe_str(self, row: pd.Series, column: Optional[str]) -> Optional[str]:
        """
        Safely extract string value from row

        Args:
            row: Pandas Series
            column: Column name (can be None)

        Returns:
            String value or None
        """
        if column is None or column not in row.index:
            return None

        value = row[column]
        if pd.isna(value) or value == '' or value is None:
            return None

        return str(value).strip()


# ============ EXAMPLE USAGE ============

if __name__ == '__main__':
    # Example: Parse Zerodha CSV
    parser = CSVImportParser(broker='zerodha')

    # Parse CSV file
    trades, stats = parser.parse_csv(
        file_path='/path/to/zerodha_tradebook.csv',
        portfolio_id=1
    )

    print(f"\n📊 Import Statistics:")
    print(f"   Total rows: {stats['total_rows']}")
    print(f"   Success: {stats['success_rows']}")
    print(f"   Failed: {stats['failed_rows']}")
    print(f"   Batch ID: {stats['import_batch_id']}")
    print(f"   Date range: {stats['start_date']} to {stats['end_date']}")

    print(f"\n📝 Sample Trade:")
    if trades:
        sample = trades[0]
        print(f"   Symbol: {sample['symbol']}")
        print(f"   Date: {sample['trade_date']}")
        print(f"   Action: {sample['action']}")
        print(f"   Quantity: {sample['quantity']}")
        print(f"   Price: ₹{sample['price']}")
        print(f"   Total Charges: ₹{sample['total_charges']}")
        print(f"   Net Value: ₹{sample['net_value']:.2f}")
