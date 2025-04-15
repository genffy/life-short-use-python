import time

# cookie string from the browser
cookie_string = """"""

# Split the cookie string into individual cookies
cookies = cookie_string.split("; ")

# Define the domain and path for the cookies
domain = ".x.com"
path = "/"
secure = "FALSE"
expiration = str(int(time.time()) + 3600)  # 1 hour from now

# Convert each cookie to Netscape format
netscape_cookies = []
for cookie in cookies:
    name, value = cookie.split("=", 1)
    netscape_cookies.append(
        f"{domain}\tTRUE\t{path}\t{secure}\t{expiration}\t{name}\t{value}"
    )

# Print the Netscape formatted cookies
for netscape_cookie in netscape_cookies:
    print(netscape_cookie)
