import requests, random, json

from bin.log import logger

user_agent = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
]


# 从网站获取json数据
def get_data(adult, chirld, date, Destination, orgin):
    url0 = 'https://desktopapps.ryanair.com/v4/en-us/availability?' \
           'ADT={}&CHD={}&DateOut={}&Destination={}' \
           '&FlexDaysOut=4&INF=0&IncludeConnectingFlights=true' \
           '&Origin={}' \
           '&RoundTrip=false&TEEN=0&ToUs=AGREED&exists=false' \
           '&promoCode=' \
        .format(adult, chirld, date, Destination, orgin)

    data = requests.get(url0, headers={"User-Agent": random.choice(user_agent)},
                        verify=False, timeout=None)
    return [data.text, date]


# 解析函数,拿到仓位码
def parse_data(datas):
    # print(datas)
    dicts = {}
    # dicts["promoStatus"] = task_response["promoStatus"]
    if "No HTTP resource was found that matches the request URI." in datas:
        # if data["message"] == "No HTTP resource was found that matches the request URI.":
        msg = "出现  No HTTP resource was found that matches the request URI"
        routings = []
        dicts["routings"] = routings
        return dicts
    try:
        data = json.loads(datas[0])
    except:
        msg = "未能解析返回的数据，记录重试"
        routings = []
        dicts["routings"] = routings
        return dicts
    routings = []
    dates = data["trips"][0]["dates"]
    t = datas[1]
    for date in dates:
        dateOut = date["dateOut"]
        if t in dateOut:
            flights = date["flights"]
            if flights != []:
                for f in flights:
                    flightKey = f["flightKey"]
                    fromSegments = []
                    routingss = {}
                    try:
                        # 仓位信息
                        fareKey = f["regularFare"]["fareKey"]
                        if len(fareKey) < 4:
                            fareKey = fareKey[0]
                        # 价格信息
                    except:
                        routings = []
                        msg = "此日期航班已经售完"
                        # print(msg)
                        dicts["routings"] = routings
                        return dicts
                    for se in f["segments"]:
                        fromSegmentss = {}
                        fromSegmentss["cabin"] = fareKey
                        fromSegmentss["flightKey"] = flightKey
                        fromSegments.append(fromSegmentss)
                    routingss["fromSegments"] = fromSegments
                    routings.append(routingss)
                    dicts["routings"] = routings
                return dicts
            else:
                msg = "此日期没有航班,"
                routings = []
                dicts["routings"] = routings
                return dicts


def get_flight_data(data, flight_number, results):
    numbers = flight_number[2:]
    routings = data["routings"]
    for data in routings:
        number = data["fromSegments"][0]["flightKey"]
        if numbers not in number:
            pass
        else:
            fareKey = data["fromSegments"][0]["cabin"]
            flightKey = data["fromSegments"][0]["flightKey"]
            data = {"INF": 0, "CHD": 1, "ADT": 1, "TEEN": 0, "DISC": "",
                    "flights": [{"flightKey": flightKey,
                                 "fareKey": fareKey, "promoDiscount": False, "FareOption": ""}],
                    "promoCode": ""}

            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
                'Content-Type': 'application/json'
            }

            # 返回X-Session-Token
            urls = 'https://desktopapps.ryanair.com/v4/en-us/Flight'
            session_token = requests.post(urls, data=json.dumps(data), headers=headers)
            try:
                token = session_token.headers["X-Session-Token"]
                return token
            except Exception as e:
                status = 401
                errorMsg = '没有获取到token'
                results["status"] = status
                results["errorMessage"] = errorMsg
                logger.error('{},{}'.format(errorMsg, e))
                return results


# 获取所有可以点击的座位
def get_seat(token, results):
    # 获取已经被选过的座位
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
        'Content-Type': 'application/json',
        'x-session-token': token
    }
    uurl = 'https://desktopapps.ryanair.com/v4/en-us/seat'
    seats = requests.get(uurl, headers=headers)
    # print(seats.text)
    equipmentModel = json.loads(seats.text)[0]["equipmentModel"]
    unavailableSeats = json.loads(seats.text)[0]["unavailableSeats"]
    # 获取当前航班所有的座位信息
    all_seats_url = 'https://desktopapps.ryanair.com/v4/en-us/res/seatmap?aircraftModel={}&cache=true'.format(
        equipmentModel)
    all_seats = requests.get(all_seats_url)
    seatRows = json.loads(all_seats.text)[0]["seatRows"]

    # 获取所有可点的座位信息
    try:
        seat_list = []
        for seatRow in seatRows[16:]:
            for seat in seatRow:
                if len(seat["designator"]) < 4:
                    seat_list.append(seat["designator"])
                else:
                    pass
        # 剔除不可用的座位
        for s in unavailableSeats:
            if int(s[:2]) < 18:
                pass
            else:
                if s in seat_list:
                    seat_list.remove(s)
        for r in seat_list:
            if len(r) > 4:
                seat_list.remove(r)
        return seat_list
    except Exception as e:
        status = 401
        errorMsg = '没有获取到可点击的座位'
        results["status"] = status
        results["errorMessage"] = errorMsg
        logger.error('{},{}'.format(errorMsg, e))
        return results
