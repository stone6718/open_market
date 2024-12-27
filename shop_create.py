import sqlite3, os, datetime, randomstring, hashlib

from datetime import timedelta

def make_expiretime(days):
    ServerTime = datetime.datetime.now()
    ExpireTime = ServerTime + timedelta(days=days)
    ExpireTime_STR = (ServerTime + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
    return ExpireTime_STR

def hash(string):
    return str(hashlib.sha512(("CodeStone" + string + "14i!").encode()).hexdigest())

shop_name = str(input("생성할 샵 이름을 입력하시오!"))
adm_id = input("생성할 샵의 관리자 아이디를 입력하시오!")
adm_pw = input("생성할 샵의 관리자 비밀번호를 입력하시오!")

if not (os.path.isfile(f"./database/{shop_name}.db")):
    con = sqlite3.connect(f"./database/{shop_name}.db")
    cur = con.cursor()
    cur.execute("""CREATE TABLE "info" ("shop_name" INTEGER, "buy_log_webhook" TEXT, "cultureid" TEXT, "culturepw" TEXT, "culturecookie" TEXT, "charge_log" TEXT, "notice_img_link" TEXT, "culture_fees" INTEGER, "bankname" TEXT, "bank_acc_name" TEXT, "bankaddress" TEXT, "push_pins" TEXT, "music_url" TEXT, "channel_talk" TEXT);""")
    con.commit()
    cur.execute("CREATE TABLE users (id INTEGER, pw TEXT, token TEXT, role TEXT, money INTEGER, ip TEXT, buylog TEXT, isadmin INTEGER, warnings INTEGER, ban INTEGER, phone_number TEXT);")
    con.commit()
    cur.execute("""CREATE TABLE "products" ("name" TEXT, "description" TEXT, "name_1" TEXT, "name_2" TEXT, "name_3" TEXT, "price_1" INTEGER, "price_2" INTEGER, "price_3" INTEGER, "product_img_url" TEXT, "stock_1" TEXT, "stock_2" TEXT, "stock_3" TEXT, "product_detail" TEXT, "item_id" TEXT, "category" TEXT, reseller_price_1 INTEGER, reseller_price_2 INTEGER, reseller_price_3 INTEGER);""")
    con.commit()
    cur.execute("""CREATE TABLE "account_charge" ("id" TEXT, "name" TEXT, "amount" INTEGER, "charge_date" TEXT);""")
    con.commit()
    cur.execute("""CREATE TABLE "coupon" ("code" TEXT, "amount" INTEGER);""")
    con.commit()
    cur.execute("""CREATE TABLE "user_buy_log" ("id" TEXT, "product_name" TEXT, "buy_code" TEXT, "amount" INTEGER);""")
    con.commit()
    cur.execute("""CREATE TABLE "user_charge_log" ("id" TEXT, "amount" INTEGER, "payment_method" TEXT, "approve" TEXT);""")
    con.commit()
    cur.execute("""CREATE TABLE "admin_log" ("charge_amount" INTEGER, "id" TEXT);""")
    con.commit()
    cur.execute("""CREATE TABLE "category" ("name" TEXT, "id" TEXT);""")
    con.commit()
    cur.execute("INSERT INTO info VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", ("", "", "", "", "", "[]", "", 0, "", "", "", "", "", ""))
    con.commit()
    cur.execute("INSERT INTO admin_log VALUES(?, ?);", (0, "stone"))
    con.commit()
    cur.execute("INSERT INTO users Values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", (adm_id, hash(adm_pw), hash(randomstring.pick(15)), "관리자", 0, "관리자 아이피 비공개", "[]", 1, 0, 0, ""))
    con.commit()
    con.close()

    print(f"{shop_name}으로 생성이 완료되었습니다.")
else:
    print("이미 존재하는 샵이름입니다.")
