import hashlib, os, random, time, requests, json, uuid, websocket, rel, ssl, certifi
from dotenv import load_dotenv

load_dotenv()

# 读取环境变量
grass_user_name = os.getenv("GRASS_USER_NAME")
grass_user_pwd = os.getenv("GRASS_USER_PWD")

# ssl._create_default_https_context = ssl._create_unverified_context
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.load_verify_locations(certifi.where())

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

USER_ID = ""
DEVICE_ID = ""


# fake https://github.com/jackspirou/clientjs/blob/master/src/client.base.js#L166
def generate_fingerprint():
    bar = "|"
    user_agent = USER_AGENT
    screen_print = "Current Resolution: 1440x900, Available Resolution: 1440x900, Color Depth: 24, Device XDPI: undefined, Device YDPI: undefined"
    plugins = "PDF Viewer, Chrome PDF Viewer, Chromium PDF Viewer, Microsoft Edge PDF Viewer, WebKit built-in PDF"
    fonts = "Arial Black, Arial, Bauhaus 93, Chalkduster, Comic Sans MS, Courier New, Georgia, GungSeo, Hiragino Sans GB, Impact, Menlo, Microsoft Sans Serif, Papyrus, Plantagenet Cherokee, Rockwell, Symbol, Tahoma, Times New Roman, Trebuchet MS, Verdana, Webdings, Wingdings"
    local_storage = True
    session_storage = True
    time_zone = "+08"
    language = "en-US"
    system_language = "en-US"
    cookies = True
    canvas_print = "data:image/png;base64,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"

    key = f"{user_agent}{bar}{screen_print}{bar}{plugins}{bar}{fonts}{bar}{local_storage}{bar}{session_storage}{bar}{time_zone}{bar}{language}{bar}{system_language}{bar}{cookies}{bar}{canvas_print}"
    # You can use hashlib library to hash the key
    hashed_key = hashlib.sha256(key.encode()).hexdigest()
    fingerprint = int(hashed_key, 16) % (10**10)
    return fingerprint


def get_device():
    fingerprint = generate_fingerprint()
    NAMESPACE_DNS = "bed9e870-4e94-4260-a1fa-815514adfce1"
    device_id = uuid.uuid5(uuid.UUID(NAMESPACE_DNS), str(fingerprint))
    DEVICE_ID = str(device_id)
    return device_id


def do_login():
    url = "https://api.getgrass.io/auth/login"

    payload = json.dumps({"user": grass_user_name, "password": grass_user_pwd})
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    token = response.cookies.get("token")
    body = response.text
    USER_ID = json.loads(body)["data"]["id"]
    return token, body


def get_device_info(token, device_id, user_id):
    url = "https://api.getgrass.io/extension/device?device_id={}&user_id={}".format(
        device_id, user_id
    )
    headers = {
        "Cookie": "token=" + token,
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    }

    response = requests.request("GET", url, headers=headers)
    return response.text


def ws_handler():
    WEBSOCKET_URLS = [
        "wss://proxy.wynd.network:4650",
        "wss://proxy.wynd.network:4444",
    ]

    def on_message(ws, message):
        print(message)
        parsed_message = json.loads(message)
        result = {}
        if parsed_message.action == "AUTH":
            result = {
                "browser_id": "",
                "user_id": "",
                "user_agent": USER_AGENT,
                "timestamp": int(time.time() * 1000),
                "device_type": "extension",
                "version": "",
            }

        ws.send(
            json.dumps(
                {
                    id: parsed_message.id,
                    "origin_action": parsed_message.action,
                    "result": result,
                }
            )
        )

    def on_error(ws, error):
        print(error)

    def on_close(ws, close_status_code, close_msg):
        print("### closed ###")

    def on_open(ws):
        print("### Opened connection ###")

    websocket.enableTrace(True)
    websocketUrl = random.choice(WEBSOCKET_URLS)
    print(websocketUrl)
    ws = websocket.WebSocketApp(
        websocketUrl,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever(
        ping_interval=20 * 1000,
        ping_timeout=10,
        ping_payload=json.dumps(
            {
                "id": str(uuid.uuid4()),
                "version": "1.0.0",
                "action": "PING",
                "data": {},
            }
        ),
        sslopt={
            # "cert_reqs": ssl.CERT_NONE,
            "context": SSL_CONTEXT
        },
    )
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()
    while True:
        ws.send(
            json.dumps(
                {
                    id: uuid.uuid4(),
                    "version": "1.0.0",
                    "action": "AUTH",
                    "data": {},
                }
            )
        )
        time.sleep(20 * 1000)


# token, user = do_login()
# print(user)
# user_id = json.loads(user)["data"]["id"]
# device_id = get_device()
# device_info = get_device_info(token, device_id, user_id)
# print(device_info)
ws_handler()
