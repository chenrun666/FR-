"""
1, 获取航班的key和日期key
2, 携带以上的两个key，发送post请求，获取响应头的x-session-token
3，携带x-session-token,获取可用的座位
"""
import json
import random

import requests

user_agent = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
]

headers = {
    "User-Agent": random.choice(user_agent)
}

dates = "2019-03-15"


# 1
def get_key():
    url = "https://desktopapps.ryanair.com/v4/en-us/availability?ADT=1&CHD=1&DateOut=2019-03-15&Destination=LIS&FlexDaysOut=4&INF=0&IncludeConnectingFlights=true&Origin=DUB&RoundTrip=false&TEEN=0&ToUs=AGREED&exists=false"

    result = requests.get(url, headers=headers)
    result_dic = result.json()
    # 获取航班信息
    trips = result_dic["trips"][0]["dates"]
    for date in trips:
        if dates in date["dateOut"]:
            flightKey = date["flights"][0]["flightKey"]
            fareKey = date["flights"][0]["regularFare"]["fareKey"]

            return flightKey, fareKey


# 2
def get_token(flightKey, fareKey):
    """
    获取x-session-token
    :param flightKey:
    :param fareKey:
    :return:
    """
    url = "https://desktopapps.ryanair.com/v4/en-us/Flight"
    data = {
        "INF": 0,
        "CHD": 1,
        "ADT": 1,
        "TEEN": 0,
        "DISC": "",
        "flights": [
            {
                "flightKey": flightKey,
                "fareKey": fareKey,
                "promoDiscount": False,
                "FareOption": ""
            }
        ]
    }
    headers["content-type"] = "application/json"
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        return response.headers["x-session-token"]
    else:
        print("访问失败")


# 3
def get_available_seat(token):
    url = "https://desktopapps.ryanair.com/v4/en-us/seat"
    headers["x-session-token"] = token
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        seat_info = response.json()[0]
        unavailableSeats = seat_info["unavailableSeats"]
        print("不可提供的座位号: ", unavailableSeats)
    else:
        print("访问失败")


if __name__ == '__main__':
    flightKey, fareKey = get_key()
    token = get_token(flightKey, fareKey)
    get_available_seat(token)
