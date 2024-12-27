import hashlib, os

def hash(string):
    return str(hashlib.sha512(("CodeStone" + string + "14i!").encode()).hexdigest())

string = input("비밀번호를 입력하세요 : ")
print(hash(string))

os.system("pause")