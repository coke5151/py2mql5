import importlib
import importlib.util
import shutil
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from py2mql5.account_properties import MarginMode, MarginSoMode, TradeMode

OFFICIAL_MODULE_NAME = "MetaTrader5"


class InitializeError(Exception):
    pass


class LoginError(Exception):
    pass


@dataclass(frozen=True)
class MT5LastError:
    error_code: int
    error_description: str


@dataclass(frozen=True)
class TerminalVersion:
    metatrader5_terminal_version: str
    build: int
    date: str


class AccountInfo:
    """Account infomation
    Attributes:
        login (int): Account number
        trade_mode (TradeMode): Account trade mode
        leverage (int): Account leverage
        limit_orders (int): Maximum allowed number of active pending orders
        margin_so_mode (MarginSoMode): Mode for setting the minimal allowed margin
        trade_allowed (bool): Allowed trade for the current account
        trade_expert (bool): Allowed trade for an Expert Advisor
        margin_mode (MarginMode): Margin calculation mode
        currency_digits (int): The number of decimal places in the account currency, which are
            required for an accurate display of trading results
        fifo_close (bool): An indication showing that positions can only be closed by FIFO rule.
            If the property value is set to true, then each symbol positions will be closed in
            the same order, in which they are opened, starting with the oldest one. In case of
            an attempt to close positions in a different order, the trader will receive an
            appropriate error. For accounts with the non-hedging position accounting mode
            (ACCOUNT_MARGIN_MODE!=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING), the property value is
            always false.
        balance (float): Account balance in the deposit currency
        credit (float): Account credit in the deposit currency
        profit (float): Current profit of an account in the deposit currency
        equity (float): Account equity in the deposit currency
        margin (float): Account margin used in the deposit currency
        margin_free (float): Free margin of an account in the deposit currency
        margin_level (float): Account margin level in percents
        margin_so_call (float): Margin call level. Depending on the set ACCOUNT_MARGIN_SO_MODE
            is expressed in percents or in the deposit currency
        margin_so_so (float): Margin stop out level. Depending on the set ACCOUNT_MARGIN_SO_MODE
            is expressed in percents or in the deposit currency
        margin_initial (float): Initial margin. The amount reserved on an account to cover the
            margin of all pending orders
        margin_maintenance (float): Maintenance margin. The minimum equity reserved on an account
            to cover the minimum amount of all open positions
        assets (float): The current assets of an account
        liabilities (float): The current liabilities on an account
        commission_blocked (float): The current blocked commission amount on an account
        name (str): Client name
        server (str): Trade server name
        currency (str): Account currency
        company (str): Name of a company that serves the account
    """

    def __init__(self, official_account_info: Any):
        self.login: int = official_account_info.login
        self.trade_mode: TradeMode = TradeMode(official_account_info.trade_mode)
        self.leverage: int = official_account_info.leverage
        self.limit_orders: int = official_account_info.limit_orders
        self.margin_so_mode: MarginSoMode = MarginSoMode(official_account_info.margin_so_mode)
        self.trade_allowed: bool = official_account_info.trade_allowed
        self.trade_expert: bool = official_account_info.trade_expert
        self.margin_mode: MarginMode = MarginMode(official_account_info.margin_mode)
        self.currency_digits: int = official_account_info.currency_digits
        self.fifo_close: bool = official_account_info.fifo_close
        self.balance: float = official_account_info.balance
        self.credit: float = official_account_info.credit
        self.profit: float = official_account_info.profit
        self.equity: float = official_account_info.equity
        self.margin: float = official_account_info.margin
        self.margin_free: float = official_account_info.margin_free
        self.margin_level: float = official_account_info.margin_level
        self.margin_so_call: float = official_account_info.margin_so_call
        self.margin_so_so: float = official_account_info.margin_so_so
        self.margin_initial: float = official_account_info.margin_initial
        self.margin_maintenance: float = official_account_info.margin_maintenance
        self.assets: float = official_account_info.assets
        self.liabilities: float = official_account_info.liabilities
        self.commission_blocked: float = official_account_info.commission_blocked
        self.name: str = official_account_info.name
        self.server: str = official_account_info.server
        self.currency: str = official_account_info.currency
        self.company: str = official_account_info.company

    def __repr__(self):
        return (
            f"AccountInfo(login={self.login}, trade_mode={self.trade_mode}, leverage={self.leverage}, "
            + f"limit_orders={self.limit_orders}, margin_so_mode={self.margin_so_mode}, "
            + f"trade_allowed={self.trade_allowed}, trade_expert={self.trade_expert}, margin_mode={self.margin_mode}, "
            + f"currency_digits={self.currency_digits}, fifo_close={self.fifo_close}, balance={self.balance}, "
            + f"credit={self.credit}, profit={self.profit}, equity={self.equity}, margin={self.margin}, "
            + f"margin_free={self.margin_free}, margin_level={self.margin_level}, "
            + f"margin_so_call={self.margin_so_call}, margin_so_so={self.margin_so_so}, "
            + f"margin_initial={self.margin_initial}, margin_maintenance={self.margin_maintenance}, "
            + f"assets={self.assets}, liabilities={self.liabilities}, commission_blocked={self.commission_blocked}, "
            + f'name="{self.name}", server="{self.server}", currency="{self.currency}", company="{self.company}")'
        )

    def __str__(self):
        return self.__repr__()


class Client:
    def __init__(self, terminal_path: str, account_number: int, password: str, server: str, timeout: int = 60_000):
        """Establish a connection with the MetaTrader 5 terminal.
        Will copy the official module to the terminal folder if it does not exist.

        **Only supports portable mode**

            Args:
                terminal_path (str): Path to the terminal64.exe.
                account_number (int): Trading account number.
                password (str): Trading account password.
                server (str): Trade server name.
                timeout (int, optional): Connection timeout in milliseconds. Defaults to 60_000 (60 seconds).

            Raises:
                InitializeError
        """
        # Check terminal path
        self.terminal_path = Path(terminal_path)
        if not self.terminal_path.exists():
            raise InitializeError(f"Terminal path {self.terminal_path} does not exist")

        self.official = self.__copy_and_import_official_module__()

        # Set other attributes
        self.timeout = timeout
        self.portable = True
        self.account_number = account_number
        self.server = server

        # Initialize
        if not self.official.initialize(
            str(self.terminal_path),
            login=self.account_number,
            password=password,
            server=self.server,
            timeout=self.timeout,
            portable=self.portable,
        ):
            raise InitializeError(
                self.last_error(), f"ensure you can login manually with portable mode: {self.portable}"
            )
        print(
            "Initialized successfully (hint: if you want multiple instances, make sure to use different terminal paths)"
        )

    def __del__(self):
        try:
            self.official.shutdown()
        except Exception as e:
            print(f"Error shutting down MetaTrader5: {e},\n{self.module_name} in {self.module_dir}")
        sys.path.remove(str(self.base_module_dir))
        sys.modules.pop(self.module_name, None)

    def __copy_and_import_official_module__(self):
        # Check write permissions
        try:
            test_file = self.terminal_path.parent / f"py2mql5_test_{uuid.uuid4().hex[:8]}"
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError):
            raise InitializeError(
                f"No write permission in {self.terminal_path}. "
                "Please copy MetaTrader to a directory with write permissions "
                "(avoid system directories like Program Files, C:, root, etc)"
            ) from None

        # Create module directory
        self.base_module_dir = self.terminal_path.parent / "py2mql5"
        self.base_module_dir.mkdir(exist_ok=True)

        # Find existing module
        existing_modules = [
            d for d in self.base_module_dir.iterdir() if d.is_dir() and d.name.startswith(f"{OFFICIAL_MODULE_NAME}_")
        ]

        if existing_modules:
            self.module_dir = existing_modules[0]
            self.module_name = self.module_dir.name
        else:
            # Generate unique new module name
            self.module_id = str(uuid.uuid4()).replace("-", "_")
            self.module_name = f"{OFFICIAL_MODULE_NAME}_{self.module_id}"
            self.module_dir = self.base_module_dir / self.module_name

            # Find official module
            official_module = importlib.util.find_spec(OFFICIAL_MODULE_NAME)
            if not official_module or not official_module.origin:
                raise InitializeError(f"Module {OFFICIAL_MODULE_NAME} not found")

            # Copy official module
            official_path = Path(official_module.origin).parent
            shutil.copytree(official_path, self.module_dir)

            # Add ignore directive to the module header
            self.__add_ignore_comments__(self.module_dir / "__init__.py")

        # Import module
        sys.path.append(str(self.base_module_dir))
        return __import__(self.module_name)

    def __add_ignore_comments__(self, file_path):
        ignore_comments = ["# type: ignore", "# pyright: ignore", "# ruff: noqa"]

        with open(file_path, "r+", encoding="utf-8") as f:
            lines = f.readlines()

            # Add ignore comments to the top of the file
            f.seek(0)
            f.write("\n".join(ignore_comments) + "\n\n" + "".join(lines))

    def login(self, account_number: int, password: str, server: str, timeout: int = 60_000):
        """Connect to a trading account using specified parameters.

        Args:
            account_number (int): Trading account number.
            password (str): Trading account password.
            server (str): Trade server name.
            timeout (int, optional):  Connection timeout in milliseconds. Defaults to 60_000 (60 seconds).

        Raises:
            LoginError: If the login fails.
        """

        if not self.official.login(account_number, password=password, server=server, timeout=timeout):
            raise LoginError(self.last_error())
        else:
            print("Login successful")

    def version(self) -> TerminalVersion:
        """Return the MetaTrader 5 terminal version.

        Returns:
            TerminalVersion: MetaTrader 5 terminal version, build number and date.
        """
        version = self.official.version()
        return TerminalVersion(
            metatrader5_terminal_version=version[0],
            build=version[1],
            date=version[2],
        )

    def last_error(self) -> MT5LastError:
        """Return the last error from the MetaTrader 5 terminal.

        Returns:
            MT5LastError: Last error code and description.
        """
        last_error = self.official.last_error()
        return MT5LastError(
            error_code=last_error[0],
            error_description=last_error[1],
        )

    def account_info(self) -> AccountInfo:
        """Return the account information.

        Returns:
            AccountInfo: Account information.
        """
        return AccountInfo(self.official.account_info())
