# Py2MQL5
A wrapper of [MetaTrader5 official package](https://pypi.org/project/MetaTrader5/) that enables multiple terminal instances at the same time.

# Documentation

First copy your MetaTrader5 from its installation directory to a normal folder (don't put it in a system directory like Program Files, C:, root, etc).

Then you can use the following code to connect to the terminal:

```python
from py2mql5 import Client

client = Client(terminal_path="path/to/your/MetaTrader5", login=123456, password="password", server="server-demo")
```
All original functions will be `client.official.function_name(parameter)` now.

For example:

```python
# Original MetaTrader5 usage (only support one terminal):
import MetaTrader5 as Mt5
Mt5.initialize()
Mt5.terminal_info()

# Py2MQL5 usage:
from py2mql5 import Client

client = Client(terminal_path="path/to/your/MetaTrader5", login=123456, password="password", server="server-demo") # must provide login and password, and portable mode will be True
client.official.terminal_info() # Will work as Mt5.terminal_info()

# You can also create multiple clients:
client2 = Client(terminal_path="path/to/your/MetaTrader5", login=123457, password="password2", server="server-demo")
client2.official.terminal_info() 
```

Because this is a wrapper, you can refer to the [MetaTrader5 official docs](https://www.mql5.com/en/docs/python_metatrader5) for more details. 
