# generated by ChatGPT
# 好的，以下是一个示例代码，用于连接币安的WebSocket API，并订阅K线数据：
# 在这个示例中，我们使用了Python的websocket库，并定义了四个回调函数，分别用于处理WebSocket连接建立、WebSocket错误、WebSocket关闭和接收到的消息。在on_open回调函数中，我们发送了一个订阅消息，以订阅btcusdt的1分钟K线数据。然后，我们使用WebSocketApp类创建了一个WebSocket连接，并使用run_forever方法启动WebSocket线程。

# 在这个示例中，我们只是简单地将接收到的K线数据打印到控制台上，您可以根据自己的需要修改on_message回调函数，以实现更复杂的逻辑。同时，还可以使用websocket库提供的其他方法，如send和close方法，来发送消息和关闭WebSocket连接。

# should install websocket-client
import websocket
import json
import threading


def on_message(ws, message):
    # 处理接收到的消息
    msg = json.loads(message)
    if msg["e"] == "kline":
        print(msg)


def on_error(ws, error):
    # 处理WebSocket错误
    print(error)


def on_close(ws, a, b):
    # 处理WebSocket关闭
    print("WebSocket closed")


def on_open(ws):
    # 处理WebSocket连接建立
    print("WebSocket opened")
    # 发送订阅消息
    subscribe_msg = {"method": "SUBSCRIBE", "params": ["btcusdt@kline_1m"], "id": 1}
    ws.send(json.dumps(subscribe_msg))


if __name__ == "__main__":
    # 创建WebSocket连接
    # ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws",
    # ref https://github.com/binance-us/binance-us-api-docs/blob/master/web-socket-streams.md#how-to-manage-a-local-order-book-correctly
    ws = websocket.WebSocketApp(
        "wss://stream.binance.us:9443/ws/bnbbtc@depth",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.on_open = on_open

    # 启动WebSocket线程
    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.start()

    # 等待WebSocket线程结束
    ws_thread.join()