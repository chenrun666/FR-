li = ['18A', '18P', '18D', '18E', '18F', '19A', '19B', '19C', '19D', '19E', '19F', '20A', '20B', '20C', '20D',
      '20E', '20F', '21A', '21B', '21C', '21D', '21E', '21F', '22A', '22B', '22C', '22D', '22E', '22F', '23A', '23B',
      '23C', '23D', '23E', '23F', '25C', '26C', '26D', '27C', '27D', '28A', '28B', '28C', '28D', '28E', '28F', '29A',
      '29B', '29C', '29D', '29E', '29F', '30A', '30B', '30C', '30D', '30E', '30F', '31A', '31B', '31C', '31D', '31E',
      '31F', '32A', '32B', '32C', '32D', '32E', '32F', '33A', '33B', '33C', '33D', '33E', '33F']

child_num = 1

dic = {}

for item in li:
    site_num = item[:2]
    if site_num not in dic:
        dic[site_num] = [ord(item[-1])]

    else:
        dic[item[:2]].append(ord(item[-1]))


# 返回座位相邻的座位号
def func(dic):
    for k, v in dic.items():
        for item in range(len(v) - child_num + 1):
            if sum(v[item:item+child_num]) == v[item] * child_num + (child_num * (child_num - 1)) / 2:
                return [k + chr(v[item + i]) for i in range(child_num)]

print(func(dic))


