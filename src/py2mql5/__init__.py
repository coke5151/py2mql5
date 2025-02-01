import importlib
import importlib.util
import shutil
import sys
import uuid
from pathlib import Path

OFFICIAL_MODULE_NAME = "MetaTrader5"


class InitializeError(Exception):
    pass


class Client:
    def __init__(self, terminal_path: str, login: int, password: str, server: str, timeout: int = 60_000):
        """Establish a connection with the MetaTrader 5 terminal.
        Will copy the official module to the terminal folder if it does not exist.

        **Only supports portable mode**

            Args:
                terminal_path (str): Path to the terminal64.exe.
                login (int): Trading account number.
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
        self.login = login
        self.server = server

        # Initialize
        if not self.official.initialize(
            str(self.terminal_path),
            login=self.login,
            password=password,
            server=self.server,
            timeout=self.timeout,
            portable=self.portable,
        ):
            raise InitializeError(
                self.official.last_error(), f"ensure you can login manually with portable mode: {self.portable}"
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
