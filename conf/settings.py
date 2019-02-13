# 测试环境
TEST = True

CHOOSESITE = False

# 回填结果
result = {
    "accountPassword":"",
    "accountType":"",
    "accountUsername":"",
    "cardName": "",
    "cardNumber": "",
    "checkStatus": True,
    "clientType": "",# 跑单的客户端码
    "createTaskStatus": True,
    "linkEmail": "",
    "linkEmailPassword": "",
    "linkPhone": "",
    "machineCode": "58.57.62.229:20181",# 跑单客户端ip
    "nameList": [],# 如果支持乘客分开出，nameList里放本次跑单成功的乘客姓名，单个也是集合
    "payTaskId": 0,
    "pnr": "ZTY2TG",# 跑单成功的pnr
    "price": 0.00, # 支付的机票含税总价
    "baggagePrice":0.00,# 支付行李总价
    "sourceCur": "CNY",
    "errorMessage":"",
    "status": 0, # 350 保留成功，301 保留失败， 450 支付成功 ，401 支付失败
    "targetCur": "MYR",
    "promo":"使用的优惠码",
    "creditEmail":"信用账号邮箱",
    "creditEmailCost":"信用账号花费",
}

bookStatus = {
    "BookingFail" : 301,  #301, "预定失败"
    "PriceVerifyFail" : 340,  #340, "跑单失败，执行下一条规则"
    "BookingSuccess" : 350,  #350, "预定成功"
    "PayFail" : 401,  #401, "支付失败"
    "PayFailAfterSubmitCard" : 440,  #440, "提交卡号后失败"
    "PaySuccess" : 450  #450, "支付成功"

}