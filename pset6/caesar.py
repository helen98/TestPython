import cs50
import sys

# check proper usage
if len(sys.argv) != 2:
    print("Usage: python caesar.py k")
else:
    # convert string into an integer
    key = int(sys.argv[1])
    # get plaintext from a user
    print("plaintext: ", end="")
    plaintext = cs50.get_string()
    print("ciphertext: ", end="")
    # print ciphered text changing only alphabetical characters
    for i in plaintext:
        if i.isalpha():
            if ord(i) >= ord('A') and ord(i) <= ord('Z'):
                print(chr((ord(i) - ord('A') + key)%26 + ord('A')), end="")
            else:
                print(chr((ord(i) - ord('a') + key)%26 + ord('a')), end="")
        else:
            print(i, end="")
    print()

