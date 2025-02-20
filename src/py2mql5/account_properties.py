from enum import Enum


class TradeMode(Enum):
    """Account trade mode
    Attributes:
        DEMO (int): Demo account
        CONTEST (int): Contest account
        REAL (int): Real account
    """

    DEMO = 0
    CONTEST = 1
    REAL = 2


class MarginSoMode(Enum):
    """Mode for setting the minimal allowed margin
    Attributes:
        STOPOUT_MODE_PERCENT (int): Account stop out mode in percents
        STOPOUT_MODE_MONEY (int): Account stop out mode in money
    """

    STOPOUT_MODE_PERCENT = 0
    STOPOUT_MODE_MONEY = 1


class MarginMode(Enum):
    """Margin calculation mode
    Attributes:
        RETAIL_NETTING (int): Used for the OTC markets to interpret positions in the "netting" mode
            (only one position can exist for one symbol). The margin is calculated based on the
            symbol type (SYMBOL_TRADE_CALC_MODE).
        EXCHANGE (int): Used for the exchange markets. Margin is calculated based on the discounts
            specified in symbol settings. Discounts are set by the broker, but not less than the
            values set by the exchange.
        RETAIL_HEDGING (int): Used for the exchange markets where individual positions are possible
            (hedging, multiple positions can exist for one symbol). The margin is calculated based
            on the symbol type (SYMBOL_TRADE_CALC_MODE) taking into account the hedged margin
            (SYMBOL_MARGIN_HEDGED).
    """

    RETAIL_NETTING = 0
    EXCHANGE = 1
    RETAIL_HEDGING = 2
