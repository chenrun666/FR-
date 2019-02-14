import math
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bin.log import logger
from bin.line_data import *
from conf.settings import *
from bin.myexception import BackException


class Base(object):
    def __init__(self, datas):
        self.now_time_year = int(time.strftime("%Y", time.localtime()))

        # 读取获取的任务信息，填写回填信息
        # 账号信息
        result["accountPassword"] = datas["pnrVO"]["accountPassword"]
        result["accountType"] = datas["pnrVO"]["accountType"]
        # 卡信息
        result["cardName"] = datas["pnrVO"]["cardName"]
        result["cardNumber"] = datas["pnrVO"]["cardNumber"]
        # 检查状态
        result["checkStatus"] = datas["pnrVO"]["checkStatus"]
        result["createTaskStatus"] = datas["pnrVO"]["createTaskStatus"]
        # 联系方式
        result["linkEmail"] = datas["pnrVO"]["linkEmail"]
        result["linkEmailPassword"] = datas["pnrVO"]["linkEmailPassword"]
        result["linkPhone"] = datas["pnrVO"]["linkPhone"]
        # 目标币种
        result["targetCur"] = datas["pnrVO"]["targetCur"]
        result["nameList"] = datas["pnrVO"]["nameList"]
        # 任务ID
        result["payTaskId"] = datas["pnrVO"]["payTaskId"]
        # 来源币种
        result["sourceCur"] = datas["pnrVO"]["sourceCur"]
        # 机器码标识
        result["machineCode"] = 'frbendi'
        result["clientType"] = 'FR_PAY_CLIENT'

        result["promo"] = None
        result["creditEmail"] = None
        result["creditEmailCost"] = None

        result["pnr"] = None
        result["price"] = None
        result["baggagePrice"] = None
        result["errorMessage"] = None
        result["status"] = None

        self.result = result

    def calculation_passenger_age(self, passengers):
        child = 0
        teen = 0
        adult = 0
        for passenger in passengers:
            birthdays_year = int(passenger["birthday"][:4])  # 获取出身年份
            years = self.now_time_year - birthdays_year  # 年龄大小
            if 2 < years <= 11:
                child += 1
            elif 12 <= years <= 15:
                teen += 1
            elif years < 2:
                print("出现婴儿票，请人工处理")
                errorMsg = "出现婴儿票，请人工处理"
                self.result["status"] = 250
                self.result["errorMessage"] = errorMsg
                logger.error('{},{}'.format(errorMsg, "婴儿票报错信息, 转人工出票"))
                # 抛出终止运行的异常
                raise BackException

            else:
                adult += 1

        return child, teen, adult


class Action(Base):
    index_url = "https://www.ryanair.com/us/en/booking/home/{}/{}/{}//{}/{}/{}/0"

    def __init__(self, datas):
        """
        初始化浏览器
        """
        # 出发地和目的地，起飞时间
        self.orgin = datas["depAirport"]  # 起飞机场
        self.destination = datas["arrAirport"]  # 目的机场
        self.date = datas["depDate"]  # 起飞时间

        # 乘客总数
        self.passengerCount = datas["passengerCount"]
        self.passenger = datas["passengerVOList"]
        self.child_num = 0
        self.adult_num = 0
        self.teen_num = 0
        self.pack_age_bool = False
        for item in self.passenger:
            if item["baggageWeight"] > 0:
                self.pack_age_bool = True
            if 2 <= self.now_time_year - int(item["birthday"][:4]) <= 11:
                self.child_num += 1
            elif 12 <= self.now_time_year - int(item["birthday"][:4]) <= 15:
                self.teen_num += 1
            else:
                self.adult_num += 1

        # 当前运行状态，如果页面动作出现错误之后将终止运行
        self.run_status = True
        super(Action, self).__init__(datas)
        try:
            self.driver = webdriver.Chrome()
            # self.driver.set_page_load_timeout(60)
            self.wait = WebDriverWait(self.driver, 20, 0.5)
            child, teen, adult = Base(datas).calculation_passenger_age(self.passenger)
            self.driver.get(self.index_url.format(self.orgin, self.destination, self.date, adult, teen, child))

            logger.info("初始化webdriver对象")
        except TimeoutException:
            logger.error("初始化超时")
        except BackException as e:  # 终止运行的错误
            logger.error(e)
            self.run_status = False
        except Exception as e:
            logger.error("初始化webdriver对象失败" + str(e))
            self.run_status = False

    # 对input框输入内容
    def fill_input(self, content, xpath, single_input=False):
        """
        获取到xpath表达式，定位元素，输入内容
        :param args:
        :param kwargs:
        :return:
        """
        try:
            input_content = self.wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    xpath
                ))
            )
            if input_content.is_enabled():
                # 一个一个字母输入
                input_content.clear()
                if single_input:
                    for item in content:
                        input_content.send_keys(item)
                        time.sleep(0.7)
                else:
                    input_content.send_keys(content)
            else:
                logger.debug(f"fill_input:{xpath}该元素不可操作")
                self.run_status = False
                self.result["status"] = 401
                self.result["errorMessage"] = "获取的元素不可用"
        except Exception as e:
            logger.error(f"定位{xpath}时，填写{content}时出错，错误信息：{str(e)}")
            self.run_status = False
            self.result["status"] = 401
            self.result["errorMessage"] = "获取元素失败"

    def click_btn(self, xpath, el=None):
        try:
            if not el:
                btn = self.wait.until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        xpath
                    ))
                )
                if btn.is_enabled():
                    btn.click()
                else:
                    logger.debug(f"click_btn:{xpath}该元素不可操作")
                    self.run_status = False
                    self.result["status"] = 401
                    self.result["errorMessage"] = "获取的元素不可用"

            else:
                el.find_element_by_xpath(xpath=xpath).click()
            time.sleep(2)
        except TimeoutException:
            logger.error(f"点击{xpath}超时")
            self.run_status = False
            self.result["status"] = 401
            self.result["errorMessage"] = "获取的元素超时"
        except Exception as e:
            logger.error(f"定位{xpath}时，点击click时出错，错误信息：{str(e)}")
            self.run_status = False
            self.result["status"] = 401
            self.result["errorMessage"] = "获取的元素出现错误"

    def get_text(self, xpath):
        try:
            h1 = self.wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    xpath
                ))
            )
            return h1.text
        except Exception as e:
            logger.error(f"获取页面文本值出错，错误信息为{str(e)}")
            self.run_status = False
            self.result["status"] = 401
            self.result["errorMessage"] = "获取的元素出现错误"

    def scroll_screen(self, el=None):
        if not el:
            scroll_screen_js = 'window.scroll(0, document.body.scrollHeight)'
            self.driver.execute_script(scroll_screen_js)
        else:
            # 拖动至可见元素
            self.driver.execute_script("arguments[0].scrollIntoView();", el)

    def get_el_list(self, xpath):
        """
        :param xpath:
        :return: 返回元素列表
        """
        try:
            elements = self.wait.until(
                EC.presence_of_all_elements_located((
                    By.XPATH,
                    xpath
                ))
            )
            return elements
        except TimeoutException:
            logger.error(f"获取元素{xpath}超时")
            self.run_status = False
            self.result["status"] = 401
            self.result["errorMessage"] = "获取的元素超时"
        except Exception as e:
            logger.error(f"获取元素{xpath}时，获取元素发生错误，错误信息：{str(e)}")
            self.run_status = False
            self.result["status"] = 401
            self.result["errorMessage"] = "获取的元素出现错误"

    def selection(self, xpath, value=None, text=None):
        """
        选择下拉框
        :param xpath: selection的xpath
        :param value: 根据value值选择
        :param text: 根据text值选择
        :return:
        """
        try:
            select = self.wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    xpath
                ))
            )
            if value:
                Select(select).select_by_value(value)
            if text:
                Select(select).select_by_visible_text(text)
            time.sleep(1)
        except Exception as e:
            logger.error(f"获取元素{xpath}时，获取元素发生错误，错误信息：{str(e)}")
            self.run_status = False
            self.result["status"] = 401
            self.result["errorMessage"] = "选择元素出现错误"


class Purchase(Action):
    def __init__(self):
        if TEST:
            # 测试环境
            with open("../files/test.json", "r", encoding="utf-8") as f:
                task_response = json.load(f)
                # task_response = json.dumps(task_response)
        else:
            task_response = {}
        #
        # # 读取获取的任务信息，填写回填信息
        datas = task_response["data"]
        # 当前年份
        self.now_time_year = int(time.strftime("%Y", time.localtime()))

        self.flightNumber = datas["depFlightNumber"]
        # 登陆的账号信息
        self.usernames = datas["pnrVO"]["accountUsername"]
        self.passwords = datas["pnrVO"]["accountPassword"]
        # 乘客信息
        passengers = datas["passengerVOList"]
        self.passengers = sorted(passengers, key=lambda x: int(x["birthday"][:4]), reverse=False)
        # 对乘客以年龄大小进行排序

        # 手机号
        self.telephone = datas["pnrVO"]["linkPhone"]
        # 信用卡信息
        self.card_num = datas["payPaymentInfoVo"]["cardVO"]["cardNumber"]
        self.cvv = datas["payPaymentInfoVo"]["cardVO"]["cvv"]
        self.cardholder = datas["payPaymentInfoVo"]["cardVO"]["firstName"] + ' ' + datas["payPaymentInfoVo"]["cardVO"][
            "lastName"]
        self.cardexpired = datas["payPaymentInfoVo"]["cardVO"]["cardExpired"]
        self.targetPrice = float(datas["targetPrice"])

        super(Purchase, self).__init__(datas)

    def select_flight(self):
        """
                根据航班号找到对应的航班选项
                :return:
                """
        # 获取所有的航班
        all_flight_xpath = '//div[@class="flights-table__rows"]/div'
        all_flight = self.get_el_list(all_flight_xpath)
        if not all_flight:
            # 获取航班信息失败
            logger.info("网络不稳定，获取航班信息失败～<.>～")
            self.run_status = False
            # 回填信息
            self.result["status"] = 402
            self.result["errorMessage"] = "没后查找到航班"
            return

        for flight in all_flight:
            flight_num = "".join(
                flight.find_element_by_xpath(".//div[@class='flight-header__informations']/div[3]").text.split())
            if flight_num == self.flightNumber:
                price_btn_xpath = './/div[@class="flight-header__min-price hide-mobile"]//div[@class="core-btn-primary"]/span[2]'

                self.click_btn(xpath=price_btn_xpath, el=flight)
                # 点击选择标准
                time.sleep(2)
                standard_xpath = './/div[@class="flights-table-fares"]/div[1]/div[1]'
                self.click_btn(standard_xpath, flight)
                # 点击continue
                time.sleep(10)
                continue_xpath = '//div[@class="trips-basket trips-cnt"]/button'
                self.click_btn(continue_xpath)
                # 先点击一个free
                time.sleep(4)
                free_xpath = '//div[@class="pb-cb-cards-holder"]/priority-cabin-bag-card[1]'
                self.click_btn(free_xpath)
                if len(self.passengers) > 1:
                    same_xpath = '//div[@class="same-for-all-form__footer"]/button[2]'
                    self.click_btn(same_xpath)
                # 点击continue
                time.sleep(1)
                continue_2_xpath = '//div[@class="priority-boarding-view__footer"]/button'
                self.click_btn(continue_2_xpath)
                time.sleep(3)

                break
        else:
            logger.info("没有查询到匹配的航班信息")
            self.run_status = False
            # 回填错误信息
            self.result["status"] = 402  # 没有匹配到对应的航班
            self.result["errorMessage"] = "没有匹配到任务总对应的航班"

    def select_packages(self):
        """
        添加行李的xpath：//*[@id="dialog-body-slot"]/dialog-body/bag-selection/div/div/div[2]/div/bags-per-person[{}]/div/div[3]/div/single-bag-in-row/div[1]/bags-selector-icon[1]/div/div[1]/span
        根据每个乘客携带的行李重量分配行李
        :return:
        """
        if not self.pack_age_bool:
            choose_site_xpath = '//div[@class="footer-message-content__buttons"]/button[2]'
            self.click_btn(choose_site_xpath)
            return

        package_xpath = '//*[@id="dialog-body-slot"]/dialog-body/bag-selection/div/div/div[2]/div/bags-per-person[{}]/div/div[3]/div/single-bag-in-row/div[1]/bags-selector-icon[{}]/div/div[1]/span'

        if self.child_num > 0:
            extra_card_xpath = '//*[@id="RECOMMENDED"]/section/div[2]/extras-card[1]'
        else:
            # 不选择座位
            choose_site_xpath = '//div[@class="footer-message-content__buttons"]/button[2]'
            self.click_btn(choose_site_xpath)
            extra_card_xpath = '//div[@class="extras-section__body"]/extras-card[2]'

        self.click_btn(xpath=extra_card_xpath)
        for index, package in enumerate(self.passengers):
            if int(package["baggageWeight"]) == 0:
                continue
            for item in range(math.ceil(int(package["baggageWeight"]) / 20)):
                self.click_btn(xpath=package_xpath.format(index + 1, item + 1))

        # 确认选择的行李
        confirm_package_xpath = '//div[@class="dialog-overlay-footer__right-cell"]/disabled-tooltip'
        self.click_btn(confirm_package_xpath)

    def select_site(self):
        """
        遇到带有儿童的乘客。选择靠近的座位
        :return:
        """
        print("选择座位")
        close_pop_xpath = '//button[@class="core-btn-primary same-seats"]'
        self.click_btn(close_pop_xpath)
        try:
            task = get_data(self.adult_num, self.child_num, self.date, self.destination, self.orgin)
            data = parse_data(task)
            token = get_flight_data(data, self.flightNumber, self.result)
            can_click_seat = get_seat(token, self.result)
            # 从可选的座位中挑选出挨着的儿童数+1的位置
            seat_dic = {}
            select_seat_num = self.child_num + 1  # 选择的座位个数应该是儿童加一个成人
            for seat in can_click_seat:
                seat_num = seat[:2]
                if seat_num not in seat_dic:
                    seat_dic[seat_num] = [ord(seat[-1])]
                else:
                    seat_dic[seat_num[:2]].append(ord(seat[-1]))
            for k, v in seat_dic.items():
                for tmp in range(len(v) - select_seat_num + 1):
                    if sum(v[tmp:tmp + select_seat_num]) == v[tmp] * select_seat_num + select_seat_num * (
                            select_seat_num - 1) / 2:
                        return [k + chr(v[tmp + i]) for i in range(select_seat_num)]
        except Exception as e:
            self.run_status = False
            logger.error(f"获取可用座位失败, 错误信息：{str(e)}")

    def click_select_seat(self, click_seat_list):
        # 第18排的座位是从第2个div开始，其他的座位是从第一个div开始
        seat_js = "document.querySelector('#scrollable > div.seat-map > div > div.seat-map-rows > div:nth-child({}) > div:nth-child({}) > span > span').click()"
        seat_dic = {"18": {"A": "2", "B": "3", "C": "4", "D": "6", "E": "7", "F": "8"},
                    "other": {"A": "1", "B": "2", "C": "3", "D": "5", "E": "6", "F": "7"}}
        seat_start_div = 24
        for item in click_seat_list:
            f_div = seat_start_div + (int(item[:2]) - 18)
            if int(item[:2]) > 18:
                c_div = seat_dic["other"][item[-1]]
            else:
                c_div = seat_dic[item[:2]][item[-1]]
            try:
                self.driver.execute_script(seat_js.format(f_div, c_div))
            except Exception as e:
                self.run_status = False
                logger.error(f"点击座位错误，错误信息是：{str(e)}")
        else:
            # 点击概览和确认
            review_confirm_xpath = '//button[@class="core-btn-primary dialog-overlay-footer__ok-button"]'
            self.click_btn(review_confirm_xpath)
            time.sleep(2)
            self.click_btn(review_confirm_xpath)
            time.sleep(4)

    def loggin(self):
        logger.info("选择航班完成，进行登陆")
        # 首先先点击checkout，更换到登陆页面
        checkout_xpath = '//div[@class="cart cart-empty"]//button'
        self.click_btn(checkout_xpath)
        # 关掉提示窗口
        time.sleep(2)
        if self.child_num == 0:
            no_thanks_xpath = '//div[@class="popup-msg__button-wrapper"]/button[2]'
            self.click_btn(no_thanks_xpath)
            time.sleep(4)
        # 点击进行登陆操作
        login_btn = '//div[@class="login-register"]/button[2]'
        self.click_btn(login_btn)
        time.sleep(2)

        # 输入账号和密码
        username_xpath = '//div[@class="modal-form-container"]/form/div[1]/input'
        password_xpath = '//div[@class="modal-form-container"]/form/div[2]/password-input/input'
        self.fill_input(content=self.usernames, xpath=username_xpath)
        self.fill_input(content=self.passwords, xpath=password_xpath)
        login_btn_2_xpath = '//div[@class="modal-form-container"]/form/div[4]//button'
        self.click_btn(login_btn_2_xpath)
        time.sleep(2)

    def fill_payment_info(self):
        """
                填写支付信息
                :return:
                """
        logger.info("登陆成功，填写支付必要信息")
        for index, item in enumerate(self.passengers):
            if index < self.adult_num + self.teen_num:
                try:
                    gender = item["sex"]
                    selects = self.driver.find_element_by_xpath(
                        "//*[@name='passengersForm']/passenger-input-group[{}]/div/ng-form/div/div[1]/div/select".format(
                            index + 1)
                    )
                    if gender == "M":
                        Select(selects).select_by_value('string:MR')
                    else:
                        Select(selects).select_by_value('string:MS')
                except Exception as e:
                    status = bookStatus["PayFail"]
                    errorMsg = '选择乘客性别时候出现错误'
                    self.result["status"] = status
                    self.result["errorMessage"] = errorMsg
                    logger.error('{},{}'.format(errorMsg, e))
                    return
                # 填写姓名
                first_names = item["name"].split("/")[0]
                last_names = item["name"].split("/")[1]
                first_names_xpath = f"//*[@name='passengersForm']/passenger-input-group[{index+1}]/div/ng-form/div/div[2]/input"
                last_names_xpath = f"//*[@name='passengersForm']/passenger-input-group[{index+1}]/div/ng-form/div/div[3]/input"
                self.fill_input(content=first_names, xpath=first_names_xpath)
                self.fill_input(content=last_names, xpath=last_names_xpath)
            else:
                first_names = item["name"].split("/")[0]
                last_names = item["name"].split("/")[1]
                first_names_xpath = f"//*[@name='passengersForm']/passenger-input-group[{index+1}]/div/ng-form/div/div[1]/input"
                last_names_xpath = f"//*[@name='passengersForm']/passenger-input-group[{index+1}]/div/ng-form/div/div[2]/input"
                self.fill_input(content=first_names, xpath=first_names_xpath)
                self.fill_input(content=last_names, xpath=last_names_xpath)

        # 输入手机号
        # 选择国籍
        country_xpath = '//select[@name="phoneNumberCountry"]'
        self.selection(xpath=country_xpath, text="China")
        # 填写手机号
        phone_input_xpath = '//div[@class="phone-number"]/input'
        self.fill_input(content=self.telephone, xpath=phone_input_xpath)

        # 填写信用卡信息
        # 填写卡号
        card_num_xpath = '//payment-method-card/div[1]/input'
        self.fill_input(content=self.card_num, xpath=card_num_xpath)
        year, month, = self.cardexpired.split("-")
        month_xpath = '//*[@name="expiryMonth"]'
        year_xpath = '//*[@name="expiryYear"]'
        self.selection(xpath=month_xpath, value=f"number:{int(month)}")
        self.selection(xpath=year_xpath, value=f"number:{year}")
        # 填写ccv
        ccv_xpath = '//div[@class="card-security-code"]/input'
        self.fill_input(content=self.cvv, xpath=ccv_xpath)
        # 填写持卡人姓名
        holdname_xpath = '//input[@name="cardHolderName"]'
        self.fill_input(content=self.cardholder, xpath=holdname_xpath)

        # 填写账单地址
        address1_xpath = '//*[@id="billingAddressAddressLine1"]'
        address2_xpath = '//*[@id="billingAddressAddressLine2"]'
        city_xpath = '//*[@id="billingAddressCity"]'
        zip_code_xpath = '//*[@id="billingAddressPostcode"]'
        country_xpath2 = '//select[@id="billingAddressCountry"]'
        self.fill_input(content="丰台区大红门天世元", xpath=address1_xpath)
        self.fill_input(content="丰台区大红门天世元", xpath=address2_xpath)
        self.fill_input(content="BEIJING", xpath=city_xpath)
        self.fill_input(content="100000", xpath=zip_code_xpath)
        self.selection(text="China", xpath=country_xpath2)

        # 确认条款
        confirm_xpath = '//div[@class="terms"]/label'
        self.click_btn(xpath=confirm_xpath)

    def check_out_price(self):
        """
        校验价格是否可以购买
        :return:
        """
        # 总价格
        total_price_xpath = '//div[@class="overall-total"]/span[2]'
        total_price = self.get_text(xpath=total_price_xpath).split()[1]
        # 行李价格
        # 选择了行李，才获取行李价格。否则行李价格为0
        if self.pack_age_bool:
            bag_price_xpath = '//div[@ng-switch-when="bags"]/ul/li/strong'
            bag_price = self.get_text(xpath=bag_price_xpath).split()[1]
        else:
            bag_price = 0

        # 回填行李价格，总价格
        self.result["baggagePrice"] = float(bag_price)
        self.result["price"] = float(total_price) - float(bag_price)

        # 总价格减去行李价格, 使用该价格与任务价格做比较。大于任务价格。购买失败。小于继续购买
        target_price = float(total_price) - float(bag_price)
        if target_price > self.targetPrice:
            # 实际价格大于任务价格。取消购买
            self.run_status = False
            logger.info("实际购买价格大于任务价格，取消购买")
            # 回填信息
            self.result["errorMessage"] = "实际购买价格大于任务价格，取消购买"
            self.result["status"] = 403

    def payment(self):
        pass


def main():
    pur = Purchase()
    # 初始化浏览器，选择航班
    if pur.run_status:
        pur.select_flight()
    else:
        # 初始化失败
        logger.error("初始化失败")
        pur.result["status"] = 401
        pur.result["errorMessage"] = "因为网络波动，浏览器初始化失败"

    # 选择航班成功，选择行李，座位等
    if pur.run_status:
        if pur.child_num:
            # 需要选择座位
            click_seat = pur.select_site()
            if isinstance(click_seat, list):
                # 点击座位
                pur.click_select_seat(click_seat)
                # 选择行李
                pur.select_packages()
        else:
            pur.select_packages()
    else:
        logger.debug("选择航班错误")

    # 选择结束，点击继续, 进行登陆
    if pur.run_status:
        pur.loggin()
    else:
        logger.debug("选择行李或选择座位错误")

    # 登陆成功，进行支付
    if pur.run_status:
        pur.fill_payment_info()
    else:
        logger.debug("登陆失败")

    if pur.run_status:
        pur.check_out_price()
    # 进行支付
    if pur.run_status:
        pur.payment()
    else:
        logger.debug("填写支付信息出现错误")

    return pur.result


if __name__ == '__main__':
    back_result = main()
    print(back_result)
