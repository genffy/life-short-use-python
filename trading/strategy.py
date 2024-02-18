import requests
from datetime import datetime
import time
import pandas as pd
import requests

# blog https://blog.mathquant.com/2023/12/11/detailed-explanation-of-perpetual-contract-grid-strategy-parameter-optimization.html

# https://stackoverflow.com/questions/43027980/purpose-of-matplotlib-inline
# %matplotlib inline


def GetKlines(symbol="BTC", start="2020-8-10", end="2021-8-10", period="1h"):
    Klines = []
    start_time = (
        int(time.mktime(datetime.strptime(start, "%Y-%m-%d").timetuple())) * 1000
    )
    end_time = int(time.mktime(datetime.strptime(end, "%Y-%m-%d").timetuple())) * 1000
    while start_time < end_time:
        res = requests.get(
            "https://data-api.binance.vision/api/v3/klines?symbol=%sUSDT&interval=%s&startTime=%s&limit=1000"
            % (symbol, period, start_time)
        )
        res_list = res.json()
        Klines += res_list
        start_time = res_list[-1][0]
    return pd.DataFrame(
        Klines,
        columns=[
            "time",
            "open",
            "high",
            "low",
            "close",
            "amount",
            "end_time",
            "volume",
            "count",
            "buy_amount",
            "buy_volume",
            "null",
        ],
    ).astype("float")


df = GetKlines(symbol="DYDX", start="2022-1-1", end="2023-12-7", period="5m")
df = df.drop_duplicates()


class Exchange:
    def __init__(self, trade_symbols, fee=0.0004, initial_balance=10000):
        self.initial_balance = initial_balance  # Initial assets
        self.fee = fee
        self.trade_symbols = trade_symbols
        self.account = {
            "USDT": {
                "realised_profit": 0,
                "unrealised_profit": 0,
                "total": initial_balance,
                "fee": 0,
            }
        }
        for symbol in trade_symbols:
            self.account[symbol] = {
                "amount": 0,
                "hold_price": 0,
                "value": 0,
                "price": 0,
                "realised_profit": 0,
                "unrealised_profit": 0,
                "fee": 0,
            }

    def Trade(self, symbol, direction, price, amount):
        cover_amount = (
            0
            if direction * self.account[symbol]["amount"] >= 0
            else min(abs(self.account[symbol]["amount"]), amount)
        )
        open_amount = amount - cover_amount
        self.account["USDT"]["realised_profit"] -= (
            price * amount * self.fee
        )  # Deduction of handling fee
        self.account["USDT"]["fee"] += price * amount * self.fee
        self.account[symbol]["fee"] += price * amount * self.fee

        if cover_amount > 0:  # Close the position first.
            self.account["USDT"]["realised_profit"] += (
                -direction * (price - self.account[symbol]["hold_price"]) * cover_amount
            )  # Profits
            self.account[symbol]["realised_profit"] += (
                -direction * (price - self.account[symbol]["hold_price"]) * cover_amount
            )

            self.account[symbol]["amount"] -= -direction * cover_amount
            self.account[symbol]["hold_price"] = (
                0
                if self.account[symbol]["amount"] == 0
                else self.account[symbol]["hold_price"]
            )

        if open_amount > 0:
            total_cost = (
                self.account[symbol]["hold_price"]
                * direction
                * self.account[symbol]["amount"]
                + price * open_amount
            )
            total_amount = direction * self.account[symbol]["amount"] + open_amount

            self.account[symbol]["hold_price"] = total_cost / total_amount
            self.account[symbol]["amount"] += direction * open_amount

    def Buy(self, symbol, price, amount):
        self.Trade(symbol, 1, price, amount)

    def Sell(self, symbol, price, amount):
        self.Trade(symbol, -1, price, amount)

    def Update(self, close_price):  # Updating of assets
        self.account["USDT"]["unrealised_profit"] = 0
        for symbol in self.trade_symbols:
            self.account[symbol]["unrealised_profit"] = (
                close_price[symbol] - self.account[symbol]["hold_price"]
            ) * self.account[symbol]["amount"]
            self.account[symbol]["price"] = close_price[symbol]
            self.account[symbol]["value"] = (
                abs(self.account[symbol]["amount"]) * close_price[symbol]
            )
            self.account["USDT"]["unrealised_profit"] += self.account[symbol][
                "unrealised_profit"
            ]
        self.account["USDT"]["total"] = round(
            self.account["USDT"]["realised_profit"]
            + self.initial_balance
            + self.account["USDT"]["unrealised_profit"],
            6,
        )


symbol = "DYDX"
value = 100
pct = 0.01


def Grid(fee=0.0002, value=100, pct=0.01, init=df.close[0]):
    e = Exchange([symbol], fee=0.0002, initial_balance=10000)
    init_price = init
    res_list = []  # For storing intermediate results
    for row in df.iterrows():
        kline = row[
            1
        ]  # To backtest a K-line will only generate one buy order or one sell order, which is not particularly accurate.
        buy_price = (value / pct - value) / (
            (value / pct) / init_price + e.account[symbol]["amount"]
        )  # The buy order price, as it is a pending order transaction, is also the final aggregated price
        sell_price = (value / pct + value) / (
            (value / pct) / init_price + e.account[symbol]["amount"]
        )
        if (
            kline.low < buy_price
        ):  # The lowest price of the K-line is lower than the current pending order price, the buy order is filled
            e.Buy(symbol, buy_price, value / buy_price)
        if kline.high > sell_price:
            e.Sell(symbol, sell_price, value / sell_price)
        e.Update({symbol: kline.close})
        res_list.append(
            [
                kline.time,
                kline.close,
                e.account[symbol]["amount"],
                e.account["USDT"]["total"] - e.initial_balance,
                e.account["USDT"]["fee"],
            ]
        )
    print(
        "Final profit:",
        e.account["USDT"]["total"] - e.initial_balance,
        "Handling fee:",
        e.account["USDT"]["fee"],
    )
    res = pd.DataFrame(
        data=res_list, columns=["time", "price", "amount", "profit", "fee"]
    )
    res.index = pd.to_datetime(res.time, unit="ms")
    return res


if __name__ == "__main__":
    for p in [0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05]:
        res = Grid(fee=0.0002, value=value * p / 0.01, pct=p, init=3)
        print(
            p,
            round(min(res["profit"]), 0),
            round(res["profit"][-1], 0),
            round(res["fee"][-1], 0),
        )
