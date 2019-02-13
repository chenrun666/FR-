import itertools

a = itertools.accumulate([1, 2, 3, 4, 5])
# for item in a:
#     print(item)

b = itertools.chain("ABCD", "EFGH")

c = itertools.chain.from_iterable(["ABCD", "BCV"])

d = itertools.dropwhile(lambda x: x < 5, range(11))


