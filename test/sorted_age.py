import time

now_year = time.localtime().tm_year

li = [{"year": 1995}, {"year": 2008}, {"year": 1993}]

a = sorted(li, key=lambda x: x["year"], reverse=False)

print(a)
