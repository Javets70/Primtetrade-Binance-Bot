from binance import Client


class TradeService:
    def __init__(self, client: Client):
        self.client = client
