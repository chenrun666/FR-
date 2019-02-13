class MyException(Exception):
    def __init__(self, args):
        self.args = args


class BackException(MyException):
    def __init__(self, messages="购买失败，终止运行"):
        self.messages = messages


if __name__ == '__main__':
    try:
        raise BackException
    except BackException as e:
        print(e.messages)
