class A(object):
    def __init__(self):
        self.q = 123


class C(A):
    def __init__(self):
        self.r = "90"
        super(C, self).__init__()


class B(C):
    def __init__(self):
        super(B, self).__init__()

    def a(self):
        print(self.q)


a = A()
c = C()
b = B()
print(b.q)