# https://docs.backpack.exchange/#section/Authentication/Signing-requests

import requests
import time
import base64
from urllib.parse import urlencode
import ed25519
import json

# https://backpack.exchange/settings/api-keys
# Replace with your actual API key and secret
api_key = "<API_KEY>"
api_secret = "<API_SECRET>"
# API endpoint
api_url = "https://api.backpack.exchange/api/v1"


# Function to make a signed API request
def make_signed_request(
    api_key, endpoint, instruction, method="GET", params=None, data=None
):
    timestamp = int(time.time() * 1000)
    window = 5000

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-Timestamp": str(timestamp),
        "X-Window": str(window),
        "X-API-Key": api_key,
    }

    signing_string = ""
    if instruction:
        signing_string += f"instruction={instruction}&"

    if data:
        signing_string += (
            urlencode(
                sorted(
                    [
                        (k, str(v).lower() if isinstance(v, bool) else v)
                        for k, v in data.items()
                    ]
                )
            )
            + "&"
        )
    elif params:
        signing_string += urlencode(sorted(params.items())) + "&"

    signing_string += f"timestamp={timestamp}&window={window}"

    print("signing_string:", signing_string)

    private_key = base64.b64decode(api_secret)
    ed25519_private_key = ed25519.SigningKey(private_key)
    signature = base64.b64encode(ed25519_private_key.sign(signing_string.encode()))
    headers["X-Signature"] = signature

    print("headers:", headers, params, data, json.dumps(data))

    if method == "GET":
        response = requests.get(api_url + endpoint, headers=headers, params=params)
    elif method == "POST":
        response = requests.post(
            api_url + endpoint, headers=headers, params=params, json=data
        )
    elif method == "DELETE":
        response = requests.delete(
            api_url + endpoint, headers=headers, params=params, json=data
        )

    print(
        "response url:",
        response.url,
        response.status_code,
        response.text,
        response.reason,
    )

    return response.json()


# Example usage for canceling an order
endpoint = "/capital"
instruction = "balanceQuery"
request_method = "GET"
body = None

# endpoint = "/order"
# instruction = "orderCancel"
# body = {
#     "orderId": 111948065686028288,
#     "symbol": "SOL_USDC",
# }
# request_method = "DELETE"

# endpoint = "/order"
# instruction = "orderExecute"
# body = {
#     "symbol": "SOL_USDC",
#     "side": "Ask",
#     "orderType": "Limit",
#     "quantity": "1.00",
#     "price": "211.61",
#     "postOnly": False,
# }
# request_method = "POST"

response = make_signed_request(
    api_key, endpoint, instruction, method=request_method, data=body
)
print(response)
