import cs50

print("0 hai! ", end="")
while True:
    print("How much change is owed?")
    n = cs50.get_float()
    if n > 0:
        n = round(n * 100)
        print("{}".format(n//25 + n%25//10 + n%25%10//5 + n%25%10%5))
        break