import cs50

while True:
    print("Height: ", end="")
    n = cs50.get_int()
    if n > 0 and n < 23:
        for i in range(n):
            print(" " * (n - i - 1), end="")
            print("#" * (i + 1))
        break