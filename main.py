import datetime, random, ast, traceback, smtplib, re
import randomstring, os, sqlite3, hashlib, requests, time
import coolsms_kakao
import naver
import pushbullet
from flask import Flask, render_template, request
from flask import redirect, session, abort, jsonify
from discord_webhook import DiscordWebhook, DiscordEmbed
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from datetime import timedelta, datetime
from flask_mail import Mail
import security as sec

app = Flask(__name__)
mail = Mail(app)

app.secret_key = randomstring.pick(20)

app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.template_filter('lenjago')
def lenjago(jago, txt):
    return len(jago.split(txt))

def db(name):
    return "./database/" + name + ".db"

def hash(string):
    return str(hashlib.sha512(("CodeStone" + string + "14i!").encode()).hexdigest())

def js_location_href(link):
    return f'<script> location.href = "{link}" </script>'

def getip():
    return request.headers.get("CF-Connecting-IP", request.remote_addr)

def nowstr():
    return datetime.now().strftime('%Y-%m-%d %H:%M')

def make_expiretime(days):
    ServerTime = datetime.now()
    ExpireTime = ServerTime + timedelta(days=days)
    ExpireTime_STR = (ServerTime + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
    return ExpireTime_STR

def get_expiretime(time):
    ServerTime = datetime.now()
    ExpireTime = datetime.strptime(time, '%Y-%m-%d %H:%M')
    if ((ExpireTime - ServerTime).total_seconds() > 0):
        how_long = (ExpireTime - ServerTime)
        days = how_long.days
        hours = how_long.seconds // 3600
        minutes = how_long.seconds // 60 - hours * 60
        return str(round(days)) + "일 " + str(round(hours)) + "시간"
    else:
        return False

def is_expired(time):
    ServerTime = datetime.now()
    ExpireTime = datetime.strptime(time, '%Y-%m-%d %H:%M')
    if ((ExpireTime - ServerTime).total_seconds() > 0):
        return False
    else:
        return True

def is_real_id(name, id, token):
    con = sqlite3.connect(db(name))
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE id == ?;", (id,))
    is_real_id = cur.fetchone()
    if is_real_id != None:
        if is_real_id[2] == token:
            return True
        else:
            return False
    else:
        return False

def login_check(name, id, pw):
    con = sqlite3.connect(db(name))
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE id == ?;", (id,))
    is_real_id = cur.fetchone()
    if is_real_id != None:
        if is_real_id[1] == hash(pw):
            return True
        else:
            return False
    else:
        return False

def get_token(name, id, pw):
    con = sqlite3.connect(db(name))
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE id == ?;", (id,))
    is_real_id = cur.fetchone()
    if is_real_id != None:
        if is_real_id[1] == hash(pw):
            return is_real_id[2]
        else:
            return False
    else:
        return False
        
def db_user_find(name, soe, soe2):
    con = sqlite3.connect(db(name))
    cur = con.cursor()
    cur.execute(f"SELECT * FROM users WHERE {soe} == ?;", (soe2,))
    db_user_find = cur.fetchone()
    if db_user_find != None:
        return True
    else:
        return False

def is_admin(name, id):
    con = sqlite3.connect(db(name))
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE id == ?;", (id,))
    is_real_id = cur.fetchone()
    if is_real_id != None:
        if is_real_id[7] == 1:
            return True
        else:
            return False
    else:
        return False
        
def user_info_get(name, id):
    con = sqlite3.connect(db(name))
    cur = con.cursor()
    cur.execute(f"SELECT * FROM users WHERE id == ?;", (id,))
    user_info = cur.fetchone()
    if user_info != None:
        return user_info
    else:
        return False

def server_info_get(name):
    con = sqlite3.connect(db(name))
    cur = con.cursor()
    cur.execute("SELECT * FROM info WHERE shop_name = ?;", (name,))
    server_info = cur.fetchone()
    if server_info != None:
        return server_info
    else:
        return False

def add_time(now_days, add_days):
    ExpireTime = datetime.strptime(now_days, '%Y-%m-%d %H:%M')
    ExpireTime_STR = (ExpireTime + timedelta(days=add_days)).strftime('%Y-%m-%d %H:%M')
    return ExpireTime_STR

@app.route("/", methods=["GET"])
def main_page():
    # 텍스트 파일에 기록하는 함수
    with open("http-log.txt", 'w', encoding='utf-8') as file:
        file.write(f"{getip()} - / GET")
    return render_template("./index.html")

@app.route("/discord", methods=["GET"])
def discord_link():
    return redirect(sec.discord_invite)

@app.route("/music", methods=["GET"])
def music_qwer():
    return render_template("./music.html")

@app.route("/이용약관", methods=["GET"])
def tos():
    return render_template("./tos.html")

@app.route("/support", methods=["GET"])
def support():
    return render_template("./support.html")

@app.route("/개인정보처리빙침", methods=["GET"])
def privacy():
    return render_template("./privacy_policy.html")

@app.route("/guide", methods=["GET"])
def guide():
    return render_template("./guide.html")

@app.route("/create", methods=["GET", "POST"])
def shop_create():
    if (request.method == "GET"):
        return render_template("./create.html")
    else:
        shop_name = request.form["shop_name"]
        adm_id = request.form["admin_id"]
        adm_pw = request.form["admin_pw"]
        phone_number = request.form["phone_number"]
        email = request.form["email"]
        key = request.form["key"]

        phone_number = f"{phone_number[:3]}-{phone_number[3:7]}-{phone_number[7:]}"

        if (shop_name == "" or
            shop_name is None or
            adm_id == "" or
            adm_id is None or
            adm_pw == "" or
            adm_pw is None or
            key == "" or
            key is None or
            email == "" or
            email is None
        ):
            return "모든 입력값을 입력해주세요!"

        if not (shop_name.isalpha()):
            return "샵 이름은 영어만 가능합니다!"

        if not is_code_valid(email, int(key)):
            return "인증번호를 다시 확인해주세요"

        if not shop_name.isalpha():
            return "스토어 이름은 영어만 가능합니다!"

        if os.path.isfile(f"./database/{shop_name}.db"):
            return "이미 존재하는 스토어 이름입니다!"

        con = sqlite3.connect(f"./database/{shop_name}.db")
        cur = con.cursor()
        cur.execute("""CREATE TABLE "info" ("shop_name" INTEGER, "buy_log_webhook" TEXT, "cultureid" TEXT, "culturepw" TEXT, "culturecookie" TEXT, "charge_log" TEXT, "notice_img_link" TEXT, "culture_fees" INTEGER, "bankname" TEXT, "bank_acc_name" TEXT, "bankaddress" TEXT, "push_pins" TEXT, "music_url" TEXT, "channel_talk" TEXT, "toss_id" TEXT, "naver_client_id" TEXT, "naver_client_secret" TEXT);""")
        con.commit()
        cur.execute("CREATE TABLE users (id INTEGER, pw TEXT, token TEXT, role TEXT, money INTEGER, ip TEXT, buylog TEXT, isadmin INTEGER, warnings INTEGER, ban INTEGER, phone_number TEXT);")
        con.commit()
        cur.execute("""CREATE TABLE "products" ("name" TEXT, "description" TEXT, "name_1" TEXT, "name_2" TEXT, "name_3" TEXT, "price_1" INTEGER, "price_2" INTEGER, "price_3" INTEGER, "product_img_url" TEXT, "stock_1" TEXT, "stock_2" TEXT, "stock_3" TEXT, "product_detail" TEXT, "item_id" TEXT, "category" TEXT, reseller_price_1 INTEGER, reseller_price_2 INTEGER, reseller_price_3 INTEGER, video TEXT);""")
        con.commit()
        cur.execute("""CREATE TABLE "account_charge" ("id" TEXT, "name" TEXT, "amount" INTEGER, "charge_date" TEXT);""")
        con.commit()
        cur.execute("""CREATE TABLE "toss_charge" ("id" TEXT, "name" TEXT, "amount" INTEGER, "charge_date" TEXT);""")
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
        cur.execute("""CREATE TABLE "link" ("name" TEXT, "link" TEXT);""")
        con.commit()
        cur.execute("INSERT INTO info VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", (shop_name, "", "", "", "", "[]", "", 3, "", "", "", "", "", "", "", "", "",))
        con.commit()
        cur.execute("INSERT INTO admin_log VALUES(?, ?);", (0, "soe"))
        con.commit()
        cur.execute("INSERT INTO users Values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", (adm_id, hash(adm_pw), hash(randomstring.pick(15)), "관리자", 0, "관리자 아이피 비공개", "[]", 1, 0, 0, phone_number,))
        con.commit()
        con.close()

        return "성공!"


@app.route("/adm_login", methods=["GET", "POST"])
def adm_login():
    if (request.method == "GET"):
        my_ip = getip()
        
        con = sqlite3.connect("./license.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM adm WHERE ip = ?;", (my_ip,))
        ip_info = cur.fetchone()

        if ip_info != None:
            if not ("adm_id" in session):
                return render_template("admin_login.html")
            else:
                return f"<script> location.href='/adm_shop_manage'; </script>"
        else:
            return f"<script> alert('등록되지 않은 아이피입니다. 접속 아이피 : {my_ip}'); location.href='/'; </script>"
    else:
        my_ip = getip()
        
        con = sqlite3.connect("./license.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM adm WHERE ip = ?;", (my_ip,))
        ip_info = cur.fetchone()

        if ip_info != None:
            if not ("adm_id" in session):
                if ip_info[1] == request.form['id']:
                    if ip_info[2] == request.form['pw']:
                        session['adm_id'] = request.form['id']

                        return "success"
                    else:
                        return "아이디 또는 비밀번호가 일치하지 않습니다!"
                else:
                    return "아이디 또는 비밀번호가 일치하지 않습니다!"
            else:
                return "오류가 발생되었습니다!"
        else:
            return "오류가 발생되었습니다!"


@app.route("/adm_shop_manage", methods=["GET", "POST"])
def adm_shop_manage():
    if (request.method == "GET"):
        my_ip = getip()
        
        con = sqlite3.connect("./license.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM adm WHERE ip = ?;", (my_ip,))
        ip_info = cur.fetchone()

        if ip_info != None:
            if ("adm_id" in session):
                if session['adm_id'] == ip_info[1]:
                    shops = []
                    for file in os.listdir("./database"):
                        if not file.endswith(".db"):
                            continue

                        shop = [ file.replace(".db", "") ]

                        con = sqlite3.connect("./database/" + file)
                        cur = con.cursor()
                        cur.execute("SELECT * FROM users WHERE role = '관리자';")
                        admin = cur.fetchone()

                        if admin == None:
                            shop.append("없음")
                            shop.append("010-0000-0000")
                            shops.append(shop)
                            continue

                        shop.append(admin[0]) # id
                        shop.append(admin[10]) # phone_number

                        shops.append(shop)

                    return render_template("admin_shop_manage.html", shops=shops)
                else:
                    return f"<script> alert('로그인이 필요합니다!'); location.href='/adm_login'; </script>"
            else:
                    return f"<script> alert('로그인이 필요합니다!'); location.href='/adm_login'; </script>"
        else:
            return f"<script> alert('등록되지 않은 아이피입니다. 접속 아이피 : {my_ip}'); location.href='/'; </script>"
    else:
        if request.form["type"] == None or request.form["type"] == "" or request.form["name"] == None or request.form["name"] == "":
            return "모든 값을 채워주세요!"

        my_ip = getip()

        con = sqlite3.connect("./license.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM adm WHERE ip = ?;", (my_ip,))
        ip_info = cur.fetchone()

        if ip_info == None:
            return f"<script> alert('등록되지 않은 아이피입니다. 접속 아이피 : {my_ip}'); location.href='/'; </script>"

        if ("adm_id" in session):
            if session['adm_id'] != ip_info[1]:
                return "오류가 발생되었습니다!"
        else:
            return "<script> alert('로그인이 필요합니다!'); location.href='/adm_login'; </script>"

        if not request.form["name"].isalpha():
            return "존재하지 않는 상점입니다."

        if not os.path.isfile(f"./database/{request.form['name']}.db"):
            return "존재하지 않는 상점입니다."

        os.rename(f"./database/{request.form['name']}.db", f"./deleted_database/{int(time.time())}_{request.form['name']}.db")

        return "success"

# 인증번호와 만료시간을 저장할 전역 변수
verification_codes = {}

# 인증번호와 만료시간을 확인하는 함수
def is_code_valid(email, user_code):
    if email in verification_codes:
        code_info = verification_codes[email]
        code, expiration = code_info['code'], code_info['expiration']
        if datetime.now() < expiration and user_code == code:
            return True
    return False

@app.route("/send_email", methods=["POST"])
def send_email():
    try:
        # 'email' 키가 없는 경우의 처리 추가
        if "email" not in request.form:
            return "이메일 주소가 제공되지 않았습니다.", 400
        receive_email = request.form["email"]  # 받는 사람의 이메일 주소
        
        if not receive_email:  # 빈 문자열인 경우의 처리
            return "이메일 주소가 비어있습니다.", 400

        subject = "케이넷소프트 이메일 인증"

        # 6자리 인증번호 생성
        verification_code = random.randint(100000, 999999)
        # 만료시간 설정 (현재 시간으로부터 5분 후)
        expiration_time = datetime.now() + timedelta(minutes=5)

        # 생성된 인증번호와 만료시간을 전역 변수에 저장
        verification_codes[receive_email] = {'code': verification_code, 'expiration': expiration_time}

        print(f"[메일인증] {verification_code} 전송 -> {receive_email}")

        html = f"""\
        <!DOCTYPE html>
        <html lang="ko">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>메일 인증</title>
                <script src="https://cdn.tailwindcss.com"></script>
                <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap" rel="stylesheet">
                <style>
                    body {{font-family: 'Noto Sans KR', sans-serif; background-color: #1a202c; display: flex; align-items: center; justify-content: center; min-height: 100vh;}}
                    .container {{background-color: #2d3748; padding: 1rem; border-radius: 1.5rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); margin-left: 35%; margin-right: 35%; height: auto; text-align: center;}}
                    .subtitle {{color: #81e6d9; font-size: 1.5rem; font-weight: bold; margin-bottom: 1.5rem;}}
                    .text {{color: #fff; margin-bottom: 1rem;}}
                    .button {{background-color: #38a169; color: white; padding: 0.5rem 1rem; border-radius: 0.25rem; margin-bottom: 1.5rem;}}
                    .footer {{color: rgb(150, 150, 150);}}
                </style>
            </head>
            <body>
                <div class="container">
                    <center><img src="https://i.ibb.co/J5dD23R/CLOUD1-nobg.png" alt="CLOUD1-nobg" width="230px" height="100px"></center>
                    <h2 class="subtitle">메일인증 안내</h2>
                    <p class="text">안녕하세요, 케이넷소프트입니다.<br>케이넷소프트를 이용해 주셔서 감사합니다.<br></p>
                    <button class="button">{verification_code}</button>
                    <p class="footer">요청하지 않으셨다면 무시해주세요.</p>
                    <p class="footer">고객지원 0507-1374-6680</p>
                </div>
            </body>
        </html>
        """
        
        sender_email = sec.email_address  # 보내는 사람의 이메일 주소
        sender_name = sec.email_name  # 보내는 사람의 이름
        password = sec.email_password  # 이메일 비밀번호

        # MIME 메시지 생성
        message = MIMEMultipart("alternative")
        message["From"] = f"{sender_name} <{sender_email}>"
        message["To"] = receive_email
        message["Subject"] = subject
        message["Date"] = formatdate(localtime=True)  # "Date" 헤더 추가

        # 이메일 본문 추가 (HTML)
        message.attach(MIMEText(html, "html", "utf-8"))

        # 이메일 SMTP 서버와 연결
        server = smtplib.SMTP_SSL(sec.email_smtp, sec.email_port)
        server.login(sender_email, password)

        # 이메일 발송
        server.sendmail(sender_email, receive_email, message.as_string().encode("utf-8"))  # 여기 수정됨
        server.quit()
        
        print(f'{receive_email} 으로 인증번호가 전송되었습니다.')
        return "이메일을 성공적으로 보냈습니다.", 200
    except Exception as e:
        print(f"이메일 전송 중 오류가 발생했습니다: {str(e)}")
        return f"이메일 전송 중 오류가 발생했습니다: {str(e)}", 500

@app.route("/<name>", methods=["GET"])
def main(name):
    if not name.isalpha():
        return abort(404)

    if not os.path.isfile(db(name)):
        return abort(404)

    if ("id" in session):
        if is_real_id(name, session['id'], session['token']):
            return js_location_href(f"/{name}/home")
        else:
            return js_location_href(f"/{name}/login")
    else:
        return js_location_href(f"/{name}/login")

@app.route("/<name>/home", methods=["GET"])
def home(name):
    if (name.isalpha()):
        if (os.path.isfile(db(name))):
            if ("id" in session):
                if is_real_id(name, session['id'], session['token']) == True:
                    user_id = session["id"]
                    logo = user_id[0:1]

                    con = sqlite3.connect(db(name))
                    cur = con.cursor()
                    cur.execute("SELECT * FROM category;")
                    categorys = cur.fetchall()
                    print(categorys)

                    con = sqlite3.connect(db(name))
                    cur = con.cursor()
                    cur.execute("SELECT * FROM link;")
                    link_info = cur.fetchall()
                    print(link_info)

                    return render_template(
                        "./home.html",
                        link_info=link_info,
                        shop_name=name,
                        categorys=categorys,
                        server_info=server_info_get(name),
                        user_info=user_info_get(name, session['id']),
                        logo=logo.upper()
                    )
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            abort(404)
    else:
        abort(404)

@app.route("/<name>/buylog", methods=["GET"])
def buylog(name):
    if (name.isalpha()):
        if (os.path.isfile(db(name))):
            if ("id" in session):
                if is_real_id(name, session['id'], session['token']) == True:
                    user_id = session["id"]
                    logo = user_id[0:1]

                    con = sqlite3.connect(db(name))
                    cur = con.cursor()
                    cur.execute(f"SELECT * FROM user_buy_log;")
                    buylogs_info = cur.fetchall()

                    return render_template("./buy_log.html", shop_name=name, server_info=server_info_get(name), user_info=user_info_get(name, session['id']), logo=logo.upper(), buylogs=buylogs_info)
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            abort(404)
    else:
        abort(404)

@app.route("/<name>/pw_change", methods=["GET"])
def pw_change(name):
    if (name.isalpha()):
        if (os.path.isfile(db(name))):
            if ("id" in session):
                if is_real_id(name, session['id'], session['token']) == True:
                    user_id = session["id"]
                    logo = user_id[0:1]

                    user_infos = user_info_get(name, session["id"])

                    buylogs = ast.literal_eval(user_infos[6])

                    con = sqlite3.connect(db(name))
                    cur = con.cursor()
                    cur.execute("SELECT * FROM category;")
                    categorys = cur.fetchall()

                    con = sqlite3.connect(db(name))
                    cur = con.cursor()
                    cur.execute("SELECT * FROM link;")
                    link_info = cur.fetchall()

                    return render_template("password_change.html",link_info=link_info, categorys=categorys, shop_name=name, server_info=server_info_get(name), user_info=user_info_get(name, session['id']), logo=logo.upper(), buylogs=reversed(sorted(buylogs)))
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            abort(404)
    else:
        abort(404)

@app.route("/<name>/my_buylog", methods=["GET"])
def my_buylog(name):
    if (name.isalpha()):
        if (os.path.isfile(db(name))):
            if ("id" in session):
                if is_real_id(name, session['id'], session['token']) == True:
                    user_id = session["id"]
                    logo = user_id[0:1]

                    user_infos = user_info_get(name, session["id"])

                    buylogs = ast.literal_eval(user_infos[6])
                    
                    con = sqlite3.connect(db(name))
                    cur = con.cursor()
                    cur.execute("SELECT * FROM category;")
                    categorys = cur.fetchall()

                    con = sqlite3.connect(db(name))
                    cur = con.cursor()
                    cur.execute("SELECT * FROM link;")
                    link_info = cur.fetchall()

                    return render_template("./buylog.html", link_info=link_info, categorys=categorys,shop_name=name, server_info=server_info_get(name), user_info=user_info_get(name, session['id']), logo=logo.upper(), buylogs=reversed(sorted(buylogs)))
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            abort(404)
    else:
        abort(404)

@app.route("/<name>/change_pw", methods=["POST"])
def change_pw(name):
    if (name.isalpha()):
        if (os.path.isfile(db(name))):
            if ("id" in session):
                if is_real_id(name, session['id'], session['token']) == True:
                    before_pw = request.form["before_pw"]
                    after_pw = request.form["after_pw"]
                    after_pw_re = request.form["after_pw_re"]

                    if before_pw == "" or after_pw == "" or after_pw_re == "":
                        return "입력값을 모두 입력해주세요!"

                    if after_pw == after_pw_re:
                        if login_check(name, session["id"], before_pw) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("UPDATE users SET pw = ? WHERE id == ?", (hash(after_pw), session['id']))
                            con.commit()
                            
                            return "성공!"
                        else:
                            return "기존 비밀번호가 맞지 않습니다."
                    else:
                        return "변경할 비밀번호가 일치하지 않습니다."
                else:
                    return "오류가 발생되었습니다!"
            else:
                return "오류가 발생되었습니다!"
        else:
            return "오류가 발생되었습니다!"
    else:
        return "오류가 발생되었습니다!"

@app.route("/<name>/charge", methods=["GET"])
def charge(name):
    if (name.isalpha()):
        if (os.path.isfile(db(name))):
            if ("id" in session):
                if is_real_id(name, session['id'], session['token']) == True:
                    user_id = session["id"]
                    logo = user_id[0:1]

                    return render_template("./charge.html", shop_name=name, server_info=server_info_get(name), user_info=user_info_get(name, session['id']), logo=logo.upper())
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            abort(404)
    else:
        abort(404)

@app.route("/<name>/buy", methods=["POST"])
def buy(name):
    if (name.isalpha()):
        if (os.path.isfile(db(name))):
            if ("id" in session):
                if is_real_id(name, session['id'], session['token']) == True:
                    amount = int(request.form["amount"])
                    option = request.form["option"]
                    product_id = request.form["product_id"]

                    if amount <= 0:
                        return "해킹시도가 감지되었습니다!"
                    
                    con = sqlite3.connect(db(name))
                    cur = con.cursor()
                    cur.execute("SELECT * FROM products WHERE item_id == ?;", (product_id,))
                    item_info = cur.fetchone()

                    user_info = user_info_get(name, session["id"])

                    if user_info[3] == "리셀러":
                        price = int(item_info[14 + int(option)]) * amount
                    else:
                        price = int(item_info[4 + int(option)]) * amount

                    if user_info[4] >= price:
                        if len(item_info[8 + int(option)].split("\n")) >= amount:
                            now_stock = item_info[8 + int(option)].split("\n")
                            bought_stock = []
                            for n in range(amount):
                                choiced_stock = random.choice(now_stock)
                                bought_stock.append(choiced_stock)
                                now_stock.remove(choiced_stock)

                            bought_stock = "\n".join(bought_stock)

                            now_buylog = ast.literal_eval(user_info[6])

                            option_b = item_info[int(option) + 1]

                            now_buylog.append([nowstr(), f"{item_info[0]} ( {option_b} )", bought_stock])

                            cur.execute(f"UPDATE products SET stock_{option} = ? WHERE item_id == ?", ("\n".join(now_stock), product_id))
                            con.commit()
                            cur.execute("UPDATE users SET money = ?, buylog = ? WHERE id == ?", (int(user_info[4]) - price, str(now_buylog), session['id']))
                            con.commit()
                            cur.execute("INSERT INTO user_buy_log VALUES(?, ?, ?, ?);", (session['id'], f"{item_info[0]} ( {option_b} )", bought_stock, amount))
                            con.commit()

                            server_info = server_info_get(name)

                            try:
                                webhook = DiscordWebhook(username="케이넷소프트", url=server_info[1], avatar_url="https://media.discordapp.net/attachments/1000637877153169531/1001458136340762685/unknown.png")
                                embed = DiscordEmbed(title='케이넷소프트', description=f'**`💸ㅣ구매로그`**\n\n`{session["id"][:2]}** 님이 {item_info[0]} ( {option_b} ) {amount}개 구매 감사합니다! 🎉`', color='03b2f8')
                                
                                if item_info[8] != "":
                                    embed.set_thumbnail(url=item_info[8])
                                    
                                embed.set_footer(text='케이넷소프트')
                                webhook.add_embed(embed)
                                webhook.execute()
                            except:
                                pass

                            if user_info[3] == "비구매자":
                                cur.execute("UPDATE users SET role = ? WHERE id == ?", ("구매자", session['id']))
                                con.commit()

                            return "ok"
                        else:
                            return "재고가 부족합니다!"
                    else:
                        return "포인트가 부족합니다!"
                else:
                    return "오류가 발생되었습니다!"
            else:
                return "오류가 발생되었습니다!"
        else:
            return "오류가 발생되었습니다!"
    else:
        return "오류가 발생되었습니다!"

@app.route("/<name>/bank_charge", methods=["GET", "POST"])
def bank_charge(name):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        user_id = session["id"]
                        logo = user_id[0:1]

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM category;")
                        categorys = cur.fetchall()

                        cur.execute("SELECT * FROM link;")
                        link_info = cur.fetchall()

                        return render_template("./account_charge.html", link_info=link_info, categorys=categorys, shop_name=name, server_info=server_info_get(name), user_info=user_info_get(name, session['id']), logo=logo.upper())
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                abort(404)
        else:
            abort(404)
    else:
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        bank_name = request.form["bank_name"]
                        amount = request.form["amount"]

                        if bank_name == "" or bank_name == None or amount == "" or amount == None:
                            return "입력값을 채워주세요!"

                        if int(amount) < 100:
                            return "100원 이상부터 충전이 가능합니다!"

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM account_charge WHERE id = ?;", (session['id'],))
                        account_charge_info = cur.fetchone()

                        cur.execute("SELECT * FROM account_charge WHERE name = ?;", (bank_name,))
                        account_charge_info2 = cur.fetchone()

                        if account_charge_info2 != None:
                            return "이름이 중복된 충전이 있습니다!"

                        if account_charge_info == None:
                            cur.execute("INSERT INTO account_charge Values(?, ?, ?, ?);", (session['id'], bank_name, amount, make_expiretime(1)))
                            con.commit()

                            # 관리자의 phone_number를 가져오기
                            cur.execute("SELECT phone_number FROM users WHERE role = '관리자';")
                            admin_number_info = cur.fetchone()
                            admin_number = admin_number_info[0] if admin_number_info else None

                            con.close()

                            name_id = session["id"]

                            server_info = server_info_get(name)
                            auth_token = server_info[11]

                            if auth_token == None or auth_token == "":
                                return "계좌이체가 등록되어있지 않은 상점입니다!"

                            def on_charge_success():
                                con = sqlite3.connect(db(name))
                                cur = con.cursor()
                                # 계정 차지 삭제
                                cur.execute("DELETE FROM account_charge WHERE id = ?;", (name_id,))
                                # 사용자 돈 증가
                                cur.execute("UPDATE users SET money = money + ? WHERE id = ?;", (int(amount), name_id,))
                                # 관리 로그 업데이트
                                cur.execute("UPDATE admin_log SET charge_amount = charge_amount + ?;", (int(amount),))
                                con.commit()
                                con.close()

                            # admin_number를 포함하여 register 호출
                            pushbullet.register(auth_token, bank_name, int(amount), name, name_id, admin_number, on_charge_success)

                            return "ok"
                        else:
                            return "이미 충전중입니다!"
                    else:
                        return "오류가 발생되었습니다!"
                else:
                    return "오류가 발생되었습니다!"
            else:
                abort(404)
        else:
            abort(404)

@app.route("/<name>/culture_charge", methods=["GET", "POST"])
def culture_charge(name):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        user_id = session["id"]
                        logo = user_id[0:1]

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM category;")
                        categorys = cur.fetchall()

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM link;")
                        link_info = cur.fetchall()

                        return render_template("./cultureland_charge.html", link_info=link_info, categorys=categorys, shop_name=name, server_info=server_info_get(name), user_info=user_info_get(name, session['id']), logo=logo.upper())
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                abort(404)
        else:
            abort(404)
    else:
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if request.form['pin'] == "" or request.form['pin'] == None:
                            return "핀번호를 입력해주세요!"

                        user_info = user_info_get(name, session["id"])
                        '''
                        if user_info[8] >= 3:
                            return "3회 이상 충전실패로 충전이 차단된 사용자입니다."
                        '''
                        if user_info[8] >= 0:
                            return "현제 문화상품권 충전은 지원하지않습니다."
                    
                        pin = request.form['pin']

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM info;")
                        server_info = cur.fetchone()
                        choi_res = requests.post("https://choiticket.com/skin/SKIN_ORDER/01/ajax.pin.chk.php", data={
                            "sort": "cul",
                            "pin": pin
                        }, headers={
                            "x-requested-with": "XMLHttpRequest"
                        }).json()
                        if( not choi_res["ERROR"] == "0000" ):
                            cur.execute("UPDATE users SET warnings = ? WHERE id == ?;", (user_info[8] + 1, session['id']))
                            con.commit()
                            return "충전실패 ( 상품권 번호 불일치 ) 경고 1회가 추가되었습니다."

                        try:
                            jsondata = {"token": sec.bank_api_token, "id": server_info[2], 'pw': server_info[3], "cookie": server_info[4], "pin": pin}
                            res = requests.post("http://127.0.0.1:123/api", json=jsondata)
                            if (res.status_code != 200):
                                raise TypeError
                            else:
                                res = res.json()
                        except:
                            return "서버 에러가 발생했습니다."

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()

                        if (res["success"] == True):
                            amount = int((int(res["amount"] )/ 100) * (100 - int(server_info[7])))

                            cur.execute("UPDATE users SET money = ? WHERE id == ?;", (user_info[4] + int(amount), session['id']))
                            con.commit()

                            cur.execute("UPDATE admin_log SET charge_amount = charge_amount + ? WHERE id == ?;", (int(amount), "soe"))
                            con.commit()

                            now_chargelog = ast.literal_eval(server_info[5])
                            now_chargelog.append([nowstr(), session['id'], "문화상품권", str(amount)])

                            cur.execute("UPDATE info SET charge_log = ? WHERE shop_name == ?;", (str(now_chargelog), ""))
                            con.commit()

                            return "charge_success|" + str(amount)

                        elif (res["success"] == False):
                            cur.execute("UPDATE users SET warnings = ? WHERE id == ?;", (user_info[8] + 1, session['id']))
                            con.commit()

                            return res["result"] + " 경고 1회가 추가되었습니다."
                    else:
                        return "오류가 발생되었습니다!"
                else:
                    return "오류가 발생되었습니다!"
            else:
                abort(404)
        else:
            abort(404)

@app.route("/<name>/naver_charge", methods=["GET", "POST"])
def naver_charge(name):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        user_id = session["id"]
                        logo = user_id[0:1]

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM category;")
                        categorys = cur.fetchall()

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM link;")
                        link_info = cur.fetchall()

                        return render_template("./naver_charge.html", link_info=link_info, categorys=categorys, shop_name=name, server_info=server_info_get(name), user_info=user_info_get(name, session['id']), logo=logo.upper())
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                abort(404)
        else:
            abort(404)
    else:
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        order_id = request.form["order_id"]

                        if order_id == None or order_id == "":
                            return "입력값을 채워주세요!"

                        server_info = server_info_get(name)
                        naver_client_id = server_info[15]
                        naver_client_secret = server_info[16]

                        if naver_client_id == None or naver_client_id == "" or naver_client_secret == None or naver_client_secret == "":
                            return "네이버 스마트스토어가 등록되어있지 않은 상점입니다!"

                        success, token = naver.get_token(naver_client_id, naver_client_secret)
                        if success == False:
                            return token # 실패 문구 (토큰 X)

                        success, trace_id, order_ids = naver.get_order_ids(token, order_id)
                        if success == False:
                            return "유효한 주문정보가 아닙니다"

                        success, trace_id, order_details = naver.get_order_details(token, order_ids)
                        if success == False:
                            return "조회 과정에서 오류가 발생하였습니다"

                        amount = 0
                        for order_detail in order_details:
                            if order_detail["productOrder"]["productOrderStatus"] != "PAYED":
                                return "결제가 완료되지 않았거나 이미 처리된 주문입니다"

                            if order_detail["productOrder"]["placeOrderStatus"] != "NOT_YET":
                                return "이미 처리된 주문입니다"

                            success, delivery = naver.deliver_order(token, order_detail["productOrder"]["productOrderId"])
                            if success == False:
                                return "주문 발송에 실패하였습니다. 상점 관리자에게 문의해주세요"

                            amount += order_detail["productOrder"]["totalPaymentAmount"]

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("UPDATE users SET money = money + ? WHERE id = ?;", (amount, session["id"],))
                        con.commit()
                        cur.execute("UPDATE admin_log SET charge_amount = ?;", (int(amount),))
                        con.commit()
                        # 관리 로그 업데이트
                        cur.execute("UPDATE admin_log SET charge_amount = charge_amount + ?;", (int(amount),))
                        con.commit()
                        con.close()

                        return f"success|{str(amount)}"
                    else:
                        return "오류가 발생되었습니다!"
                else:
                    return "오류가 발생되었습니다!"
            else:
                abort(404)
        else:
            abort(404)

@app.route("/<name>/item", methods=["GET"])
def item(name):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        user_id = session["id"]
                        logo = user_id[0:1]

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM products;")
                        products = cur.fetchall()

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM category;")
                        categorys = cur.fetchall()

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM link;")
                        link_info = cur.fetchall()

                        return render_template("./item.html", link_info=link_info, shop_name=name, server_info=server_info_get(name), user_info=user_info_get(name, session['id']), logo=logo.upper(), products=products, categorys=categorys)
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                abort(404)
        else:
            abort(404)

@app.route("/<name>/item/<category_id>", methods=["GET"])
def item_category_id(name, category_id):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        user_id = session["id"]
                        logo = user_id[0:1]

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM category;")
                        categorys = cur.fetchall()

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM category WHERE id == ?;", (category_id,))
                        category_i = cur.fetchone()

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM products WHERE category == ?;", (category_i[1],))
                        products = cur.fetchall()

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM link;")
                        link_info = cur.fetchall()

                        return render_template("./item.html", shop_name=name,link_info=link_info, server_info=server_info_get(name), user_info=user_info_get(name, session['id']), logo=logo.upper(), products=products, categorys=categorys)
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                abort(404)
        else:
            abort(404)

@app.route("/<name>/admin/admin_link_setting", methods=["GET"])
def admin_link_setting(name):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM link;")
                            link = cur.fetchall()

                            return render_template("./admin_link_setting.html", shop_name=name, link=link)
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/user_moonsang_zero/<user_id>", methods=["GET"])
def user_moonsang_zero(name, user_id):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("UPDATE users SET warnings = ? WHERE id == ?;", (0, user_id))
                            con.commit()

                            return js_location_href(f"/{name}/admin/admin_user_setting_detail/{user_id}")

@app.route("/<name>/admin/product_stock_edit/<item_id>", methods=["GET"])
def product_stock_edit(name, item_id):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM products WHERE item_id == ?;", (item_id,))
                            product_info = cur.fetchone()

                            return render_template("./admin_stock_setting.html", shop_name=name, product_info=product_info)
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")
            
@app.route("/<name>/admin/admin_user_buy_log", methods=["GET"])
def admin_user_buy_log(name):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM user_buy_log;")
                            user_buy_log = cur.fetchall()

                            return render_template("./admin_user_buy_log.html", shop_name=name, buy_log=user_buy_log)
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/buy_log_search/<user_id>", methods=["GET"])
def buy_log_search(name, user_id):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM user_buy_log WHERE id == ?;", (user_id,))
                            user_buy_log = cur.fetchall()

                            if user_buy_log == None:
                                is_exist == False
                            else:
                                is_exist = True

                            return render_template("./admin_user_buy_log_search.html", shop_name=name, buy_log=user_buy_log, is_exist=is_exist)
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/product_stock_edit_save/<item_id>", methods=["POST"])
def product_stock_edit_save(name, item_id):
    if (request.method == "POST"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM products WHERE item_id == ?;", (item_id,))
                            product_info = cur.fetchone()

                            cur.execute("UPDATE products SET stock_1 = ?, stock_2 = ?, stock_3 = ? WHERE item_id == ?;", (request.form["stock_1"], request.form["stock_2"], request.form["stock_3"], item_id))
                            con.commit()

                            return "ok"
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/create_link", methods=["POST"])
def create_link(name):
    if (request.method == "POST"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            link_name = request.form["link_name"]

                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("INSERT INTO link VALUES(?, ?);", (link_name, ""))
                            con.commit()
                            con.close()

                            return "ok"
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/link_edit/<link>", methods=["GET"])
def link_edit(name, link):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute(f"SELECT * FROM link WHERE name == ?;", (link,))
                            link_info = cur.fetchone()
                            con.close()

                            return render_template("./admin_link_edit.html", shop_name=name, link_info=link_info)
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/link_remove/<link>", methods=["GET"])
def link_remove(name, link):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("DELETE FROM link WHERE name == ?;", (link,))
                            con.commit()
                            con.close()

                            return js_location_href(f"/{name}/admin/admin_link_setting")
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/nobuyer_clear", methods=["GET"])
def nobuyer_clear(name):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM users WHERE role == ?;", ("비구매자",))
                            users = cur.fetchall()

                            for user in users:
                                cur.execute("DELETE FROM users WHERE id == ?;", (user[0],))
                                con.commit()

                            con.close()

                            return js_location_href(f"/{name}/admin/admin_user_setting")
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/link_edit_save", methods=["POST"])
def link_edit_save(name):
    if (request.method == "POST"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("UPDATE link SET link = ? WHERE name == ?;", (request.form["link"], request.form["link_name"],))
                            con.commit()
                            con.close()

                            return "ok"
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/product_option_abled/<item_id>/<option>", methods=["POST"])
def product_option_abled(name, item_id, option):
    if (request.method == "POST"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute(f"UPDATE products SET name_{option} = ? WHERE item_id == ?;", ("", item_id))
                            con.commit()

                            return "ok"
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/product_option_disabled/<item_id>/<option>", methods=["POST"])
def product_option_disabled(name, item_id, option):
    if (request.method == "POST"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute(f"UPDATE products SET name_{option} = ? WHERE item_id == ?;", (None, item_id))
                            con.commit()

                            return "ok"
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/admin_charge_setting", methods=["GET", "POST"])
def admin_charge_setting(name):
    if (request.method == "POST"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM account_charge WHERE id == ?;", (request.form["user_id"],))
                            account_charge_info = cur.fetchone()

                            if request.form["approve"] == "True":
                                cur.execute("DELETE FROM account_charge WHERE id == ?;", (request.form["user_id"],))
                                con.commit()
                                cur.execute("UPDATE users SET money = money + ? WHERE id == ?;",(account_charge_info[2], request.form["user_id"]))
                                con.commit()
                            else:
                                cur.execute("DELETE FROM account_charge WHERE id == ?;", (request.form["user_id"],))
                                con.commit()

                            return "ok"
                        else:
                            return "오류가 발생되었습니다!"
                    else:
                        return "오류가 발생되었습니다!"
                else:
                    return "오류가 발생되었습니다!"
            else:
                return "오류가 발생되었습니다!"
        else:
            return "오류가 발생되었습니다!"
    else:
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM account_charge;")
                            charge_infos = cur.fetchall()

                            return render_template("./admin_user_charge_setting.html", shop_name=name, charge_infos=charge_infos, is_search=False)
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")


@app.route("/<name>/admin/product_delete/<item_id>", methods=["POST"])
def product_delete(name, item_id):
    if (request.method == "POST"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM products WHERE item_id == ?;", (item_id,))
                            product_info = cur.fetchone()

                            cur.execute("DELETE FROM products WHERE item_id == ?;", (item_id,))
                            con.commit()

                            return "ok"
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/product_edit_save", methods=["POST"])
def product_edit_save(name):
    if (request.method == "POST"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM products WHERE name == ?;", (request.form["product_name"],))
                            product_info = cur.fetchone()

                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM category WHERE name == ?;", (request.form["product_setting_category"],))
                            product_setting_category_info = cur.fetchone()
                            
                            if product_setting_category_info == None:
                                return "존재하지 않는 카테고리!"

                            cur.execute("UPDATE products SET description = ?, product_detail = ? WHERE name == ?;", (request.form["product_description"], request.form["product_description_2"], request.form["product_name"]))
                            con.commit()
                            cur.execute("UPDATE products SET name_1 = ?, name_2 = ?, name_3 = ? WHERE name == ?;", (request.form["product_option_1_name"], request.form["product_option_2_name"], request.form["product_option_3_name"], request.form["product_name"]))
                            con.commit()
                            cur.execute("UPDATE products SET price_1 = ?, price_2 = ?, price_3 = ? WHERE name == ?;", (request.form["product_option_1_price"], request.form["product_option_2_price"], request.form["product_option_3_price"], request.form["product_name"]))
                            con.commit()
                            cur.execute("UPDATE products SET product_img_url = ? WHERE name == ?;", (request.form["product_image_url"], request.form["product_name"]))
                            con.commit()
                            cur.execute("UPDATE products SET category = ? WHERE name == ?;", (product_setting_category_info[1], request.form["product_name"]))
                            con.commit()

                            if request.form['product_option_1_name'] == "비활성화":
                                cur.execute("UPDATE products SET name_1 = ? WHERE name == ?;", (None, request.form["product_name"]))
                                con.commit()

                            if request.form['product_option_2_name'] == "비활성화":
                                cur.execute("UPDATE products SET name_2 = ? WHERE name == ?;", (None, request.form["product_name"]))
                                con.commit()

                            if request.form['product_option_3_name'] == "비활성화":
                                cur.execute("UPDATE products SET name_3 = ? WHERE name == ?;", (None, request.form["product_name"]))
                                con.commit()

                            product_setting_option_1_reseller_price = request.form["product_setting_option_1_reseller_price"]
                            product_setting_option_2_reseller_price = request.form["product_setting_option_2_reseller_price"]
                            product_setting_option_3_reseller_price = request.form["product_setting_option_3_reseller_price"]

                            cur.execute("UPDATE products SET reseller_price_1 = ? WHERE name == ?;", (product_setting_option_1_reseller_price, request.form["product_name"]))
                            con.commit()
                            cur.execute("UPDATE products SET reseller_price_2 = ? WHERE name == ?;", (product_setting_option_2_reseller_price, request.form["product_name"]))
                            con.commit()
                            cur.execute("UPDATE products SET reseller_price_3 = ? WHERE name == ?;", (product_setting_option_3_reseller_price, request.form["product_name"]))
                            con.commit()
                            cur.execute("UPDATE products SET video = ? WHERE name == ?;", (request.form["product_video_url"], request.form["product_name"]))
                            con.commit()
                            con.close()

                            return "ok"
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/category_setting", methods=["GET"])
def admin_category_setting(name):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM category;")
                            category = cur.fetchall()

                            return render_template("./admin_category_setting.html", shop_name=name, category=category)
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/create_category", methods=["POST"])
def create_category(name):
    if (request.method == "POST"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM category WHERE name == ?;", (request.form["category_name"],))
                            category = cur.fetchone()

                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT COUNT(*) FROM category;")
                            category_count = cur.fetchall()
                            if int(category_count[0][0]) >= 16:
                                return "카테고리는 15개까지만 생성이 가능합니다!"

                            if category == None:
                                cur.execute("INSERT INTO category VALUES(?, ?);", (request.form["category_name"], randomstring.pick(8)))
                                con.commit()
                                
                                return "ok"
                            else:
                                return "이미 존재하는 카테고리입니다."
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/category_remove/<category_name>", methods=["GET"])
def category_remove(name, category_name):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM category WHERE id == ?;", (category_name,))
                            category = cur.fetchone()

                            if category != None:
                                cur.execute("DELETE FROM category WHERE name == ?;", (category[0],))
                                con.commit()
                                
                                return js_location_href(f"/{name}/admin/category_setting")
                            else:
                                return "존재하지 않는 카테고리입니다."
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")
            
@app.route("/<name>/admin/admin_product_setting", methods=["GET"])
def admin_product_setting(name):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM products;")
                            product_info = cur.fetchall()

                            return render_template("./admin_product_setting.html", shop_name=name, product_info=product_info, is_search=False)
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/product_search/<prod_name>", methods=["GET"])
def product_search(name, prod_name):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM products WHERE name == ?;", (prod_name,))
                            product_info = cur.fetchone()

                            if product_info == None:
                                is_exist == False
                            else:
                                is_exist = True

                            return render_template("./admin_product_setting.html", shop_name=name, product_info=product_info, is_search=True, is_exist=is_exist)
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/create_product", methods=["POST"])
def create_product(name):
    if (request.method == "POST"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()

                            product_name = request.form["product_name"]

                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM products WHERE name == ?;", (product_name,))
                            is_already_product = cur.fetchone()

                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT COUNT(*) FROM products;")
                            product_counts = cur.fetchall()
                            if int(product_counts[0][0]) >= 101:
                                return "제품은 100개까지만 생성이 가능합니다!"

                            if is_already_product == None:
                                cur.execute("INSERT INTO products VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", (product_name, "설명", "옵션 1", "옵션 2", "옵션 3", 0, 0, 0, "", "", "", "", "", randomstring.pick(8), "", "", "", "", ""))
                                con.commit()

                                return "ok"
                            else:
                                return "이미 존재하는 제품명입니다."
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/product_edit/<prd_id>", methods=["GET"])
def product_edit(name, prd_id):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM products WHERE item_id == ?;", (prd_id,))
                            product_info = cur.fetchone()

                            if product_info == None:
                                is_exist = False
                            else:
                                is_exist = True

                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM category WHERE id == ?;", (product_info[14],))
                            product_setting_category_info = cur.fetchone()

                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM category;")
                            product_setting_category_infos = cur.fetchall()

                            if product_setting_category_info == None:
                                product_setting_category = ""
                            else:
                                product_setting_category = product_setting_category_info[0]

                            return render_template("./admin_product_setting_detail.html", product_setting_category_infos=product_setting_category_infos, shop_name=name, product_info=product_info, is_search=True, is_exist=is_exist, category_name=product_setting_category)
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                return js_location_href(f"/{name}/login")
        else:
            return js_location_href(f"/{name}/login")

@app.route("/<name>/admin/admin_home", methods=["GET"])
def admin_home(name):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM admin_log WHERE id = ?;", ("soe",))
                            user_charge_amount = cur.fetchone()

                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute('SELECT * FROM users WHERE role="구매자";')
                            buyer = cur.fetchall()

                            buyer_count = 0

                            for i in buyer:
                                buyer_count += 1

                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT COUNT(*) FROM users;")
                            user = cur.fetchall()

                            user_count = user[0][0]

                            buy_percent = round((buyer_count / user_count) * 100)

                            return render_template("./admin_home.html", shop_name=name, user_charge_amount=user_charge_amount[0], buyer_count=buyer_count, user_count=user_count, buy_percent=buy_percent)
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                abort(404)
        else:
            abort(404)

@app.route("/<name>/admin/admin_user_setting", methods=["GET"])
def admin_user_setting(name):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM users;")
                            users = cur.fetchall()

                            return render_template("./admin_user_setting.html", shop_name=name, shop_info=server_info_get(name), users=users, is_search=False)
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                abort(404)
        else:
            abort(404)

@app.route("/<name>/admin/admin_user_setting_serach/<user_id>", methods=["GET"])
def admin_user_setting_search(name, user_id):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM users WHERE id == ?;", (user_id,))
                            users = cur.fetchone()

                            if users == None:
                                is_exist = False
                            else:
                                is_exist = True

                            return render_template("./admin_user_setting.html", shop_name=name, shop_info=server_info_get(name), users=users, is_search=True, is_exist=is_exist)
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                abort(404)
        else:
            abort(404)

@app.route("/<name>/admin/admin_user_setting_detail/<user_id>", methods=["GET"])
def admin_user_setting_detail(name, user_id):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM users WHERE id == ?;", (user_id,))
                            users = cur.fetchone()

                            if users == None:
                                is_exist = False
                            else:
                                is_exist = True

                            return render_template("./admin_user_setting_detail.html", shop_name=name, shop_info=server_info_get(name), users=users, is_exist=is_exist)
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                abort(404)
        else:
            abort(404)

@app.route("/<name>/admin/admin_user_setting_detail_save", methods=["POST"])
def admin_user_setting_detail_save(name):
    if (name.isalpha()):
        if (os.path.isfile(db(name))):
            if ("id" in session):
                if is_real_id(name, session['id'], session['token']) == True:
                    if is_admin(name, session['id']) == True:
                        userid = request.form["user_id"]
                        user_money = request.form["user_money"]
                        is_ban = request.form["is_ban"]
                        is_reseller = request.form["is_reseller"]

                        if userid == None or userid == "" or user_money == None or user_money == "" or is_ban == None or is_ban == "":
                            return "모든 값을 채워주세요!"

                        if is_ban == "True" or is_ban == True:
                            is_ban = 1
                        elif is_ban == "False" or is_ban == False:
                            is_ban = 0

                        if is_reseller == "true":
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("UPDATE users SET role = ? WHERE id == ?;", ("리셀러", userid))
                            con.commit()
                        else:
                            con = sqlite3.connect(db(name))
                            cur = con.cursor()
                            cur.execute("SELECT * FROM users WHERE id == ?;", (userid,))
                            user_info = cur.fetchone()

                            if user_info[7] == 1:
                                con = sqlite3.connect(db(name))
                                cur = con.cursor()
                                cur.execute("UPDATE users SET role = ? WHERE id == ?;", ("관리자", userid))
                                con.commit()
                            else:
                                con = sqlite3.connect(db(name))
                                cur = con.cursor()
                                cur.execute("UPDATE users SET role = ? WHERE id == ?;", ("비구매자", userid))
                                con.commit()

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM users WHERE id == ?;", (userid,))
                        user_info = cur.fetchone()

                        cur.execute("UPDATE users SET money = ?, ban = ? WHERE id == ?;", (user_money, is_ban, userid))
                        con.commit()

                        return "ok"
                    else:
                        return "오류가 발생되었습니다!"
                else:
                    return "오류가 발생되었습니다!"
            else:
                return "오류가 발생되었습니다!"
        else:
            return "오류가 발생되었습니다!"
    else:
        return "오류가 발생되었습니다!"

@app.route("/<name>/admin/admin_general", methods=["GET", "POST"])
def admin_general(name):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        if is_admin(name, session['id']) == True:
                            return render_template("./admin_general.html", shop_name=name, server_info=server_info_get(name))
                        else:
                            return js_location_href(f"/{name}/login")
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                abort(404)
        else:
            abort(404)
    else:
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        buy_log_webhook_url = request.form["buy_log_webhook_url"]
                        store_music = request.form["store_music"]
                        ct_cookie = request.form["ct_cookie"]
                        ct_id = request.form["ct_id"]
                        ct_pw = request.form["ct_pw"]
                        ct_fees = request.form["ct_fees"]
                        bank_number = request.form["bank_number"]
                        bank_charge_key = request.form["bank_charge_key"]
                        notice_img_url =request.form["notice_img_url"]
                        channeltalk_plugin = request.form["channeltalk_plugin"]
                        toss_id = request.form["toss_id"]
                        naver_client_id = request.form["naver_client_id"]
                        naver_client_secret = request.form["naver_client_secret"]

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM info;")
                        shop_info = cur.fetchone()

                        cur.execute("UPDATE info SET cultureid = ?, culturepw = ?, culturecookie = ?, music_url = ?, culture_fees = ?", (ct_id, ct_pw, ct_cookie, store_music, int(ct_fees)))
                        con.commit()
                        cur.execute("UPDATE info SET bankaddress = ?, push_pins = ?, notice_img_link = ?, buy_log_webhook = ?", (bank_number, bank_charge_key, notice_img_url, buy_log_webhook_url))
                        con.commit()
                        cur.execute("UPDATE info SET channel_talk = ?", (channeltalk_plugin,))
                        con.commit()
                        cur.execute("UPDATE info SET toss_id = ?", (toss_id,))
                        con.commit()
                        cur.execute("UPDATE info SET naver_client_id = ?, naver_client_secret = ?", (naver_client_id, naver_client_secret))
                        con.commit()

                        return "ok"
                    else:
                        return "오류가 발생되었습니다!"
                else:
                    return "오류가 발생되었습니다!"
            else:
                return "오류가 발생되었습니다!"
        else:
            return "오류가 발생되었습니다!"


@app.route("/<name>/buy/<item_id>", methods=["GET"])
def item_buy(name, item_id):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        user_id = session["id"]
                        logo = user_id[0:1]

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM products WHERE item_id == ?;", (item_id,))
                        product = cur.fetchone()

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM category;")
                        categorys = cur.fetchall()

                        con = sqlite3.connect(db(name))
                        cur = con.cursor()
                        cur.execute("SELECT * FROM link;")
                        link_info = cur.fetchall()

                        return render_template("./item_detail.html", link_info=link_info, categorys=categorys, shop_name=name, server_info=server_info_get(name), user_info=user_info_get(name, session['id']), logo=logo.upper(), product=product)
                    else:
                        return js_location_href(f"/{name}/login")
                else:
                    return js_location_href(f"/{name}/login")
            else:
                abort(404)
        else:
            abort(404)

reset_pass_codes = {}
@app.route("/<name>/reset_password", methods=["GET", "POST"])
def reset_password(name):
    if request.method == "GET":
        return render_template("./reset_password.html", shop_name=name)
    else:
        if not name.isalpha():
            return "존재하지 않는 상점입니다", 400

        if not os.path.isfile(db(name)):
            return "존재하지 않는 상점입니다", 400

        con = sqlite3.connect(db(name))
        cur = con.cursor()

        phone_number = request.form.get('phone_number')
        phone_key = request.form.get('phone_key')
        new_password = request.form.get('new_password')

        if not all([phone_number, phone_key, new_password]):
            return "모든 값을 채워주세요!"

        phone_number = f"{phone_number[:3]}-{phone_number[3:7]}-{phone_number[7:]}"

        # 인증번호 검증
        if phone_number not in reset_pass_codes:
            return "잘못된 인증번호입니다!"

        code_info = reset_pass_codes[phone_number]
        if code_info["name"] != name:
            return "잘못된 인증번호입니다!"

        code, expiration = code_info['code'], code_info['expiration']
        if datetime.now() >= expiration or phone_key != code:
            return "잘못된 인증번호입니다!"

        # 인증정보 삭제
        del reset_pass_codes[phone_number]

        cur.execute("UPDATE users SET pw = ? WHERE phone_number = ?", (hash(new_password), phone_number))
        con.commit()
        con.close()

        return "reset_success"

@app.route("/<name>/request_password_reset", methods=["POST"])
def request_password_reset(name):
    try:
        phone_number = request.form["phone_number"]
        if phone_number == "" or phone_number is None:
            return "휴대폰 번호를 입력해 주세요!"

        phone_number = f"{phone_number[:3]}-{phone_number[3:7]}-{phone_number[7:]}"

        if not name.isalpha():
            return "존재하지 않는 상점입니다", 400

        if not os.path.isfile(db(name)):
            return "존재하지 않는 상점입니다", 400

        con = sqlite3.connect(db(name))
        cur = con.cursor()

        con = sqlite3.connect(db(name))
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE phone_number == ?;", (phone_number,))
        users = cur.fetchone()

        if users == None:
            return "해당 번호로 계정이 가입되어있지 않습니다."

        if users[9] == 1:
            return "ban_user"

        # 6자리 인증번호 생성
        verification_code = str(random.randint(100000, 999999))
        # 만료시간 설정 (현재 시간으로부터 5분 후)
        expiration_time = datetime.now() + timedelta(minutes=5)
        # 생성된 인증번호와 만료시간을 전역 변수에 저장
        reset_pass_codes[phone_number] = {'code': verification_code, 'expiration': expiration_time, 'name': name}
        # SMS 발송
        to = request.form['phone_number']
        text = f'''[코드스톤]
비밀번호 재설정을 위한 인증번호 : {verification_code}'''

        message = {
            'messages': [{
                'to': to,
                'from': sec.send_number,
                'text': text,
                'kakaoOptions': {
                    'pfId': sec.kakao_pfid,
                    'templateId': sec.kakao_templateid,
                    'variables': {
                        '#{verify_code}': verification_code,
                        '#{activity}': "비밀번호 재설정"
                    }
                }
            }]
        }

        # 카카오 알림톡 전송이 실패할 경우 자동으로 문자 메시지 전송
        coolsms_kakao.send_kakao(message)

        print(f"[알림톡] {verification_code} -> {phone_number}")
        return "send_success", 200
    except Exception as e:
        print(f"문자 전송 중 오류가 발생했습니다: {str(e)}")
        return f"문자 전송 중 오류가 발생했습니다: {str(e)}", 500


@app.route("/<name>/support_password", methods=["GET"])
def support_password():
    return render_template("./support_password.html")


@app.route("/<name>/login", methods=["GET", "POST"])
def login(name):
    if (request.method == "GET"):
        if (name.isalpha()):
            if (os.path.isfile(db(name))):
                if ("id" in session):
                    if is_real_id(name, session['id'], session['token']) == True:
                        return js_location_href(f"/{name}/")
                    else:
                        return render_template("./login.html", shop_name=name)
                else:
                    return render_template("./login.html", shop_name=name)
            else:
                abort(404)
        else:
            abort(404)
    else:
        if not ("id" in session):
            if (name.isalpha()):
                if (os.path.isfile(db(name))):
                    con = sqlite3.connect(db(name))
                    cur = con.cursor()

                    id = request.form['id']
                    pw = request.form['pw']

                    con = sqlite3.connect(db(name))
                    cur = con.cursor()
                    cur.execute("SELECT * FROM users WHERE id == ?;", (id,))
                    users = cur.fetchone()

                    if users == None:
                        return "login_fail"

                    if users[9] == 1:
                        return "ban_user"

                    if login_check(name, id, pw) == True:
                        session['id'] = id
                        session['token'] = get_token(name, id, pw)

                        return "login_success"

                    else:
                        return "login_fail"
        else:
            return "login_already"

@app.route("/<name>/register", methods=["GET", "POST"])
def register(name):
    if (request.method == "GET"):
        if (name.isalpha()):
            try:
                if (os.path.isfile(db(name))):
                    if ("id" in session):
                        if is_real_id(name, session['id'], session['token']) == True:
                            return js_location_href(f"/{name}/")
                        else:
                            return render_template("./register.html", shop_name=name)
                    else:
                        return render_template("./register.html", shop_name=name)
                else:
                    abort(404)
            except Exception as e:
                print(f"오류 발생: {e}")
        else:
            abort(404)
    else:
        try:
            if not ("id" in session):
                if (name.isalpha()):
                    if (os.path.isfile(db(name))):
                        con = sqlite3.connect(db(name))
                        cur = con.cursor()

                        id = request.form.get('id')
                        pw = request.form.get('pw')
                        re_pw = request.form.get('re_pw')
                        phone_number = request.form.get('phone_number')
                        phone_key = request.form.get('phone_key')

                        if not all([id, pw, re_pw, phone_number, phone_key]):
                            return "모든 값을 채워주세요!"

                        # 인증번호 검증
                        if not is_code_valid(phone_number, phone_key):
                            return "잘못된 인증번호입니다!"
                            
                        
                        if not db_user_find(name, "ip", getip()):
                            if not db_user_find(name, "id", id):
                                if pw == re_pw:
                                    token = hash(randomstring.pick(15))

                                    cur.execute("INSERT INTO users Values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", (id, hash(pw), token, "비구매자", 0, getip(), "[]", 0, 0, 0, f"{phone_number[:3]}-{phone_number[3:7]}-{phone_number[7:]}"))
                                    con.commit()
                                    con.close()
                                    
                                    session['id'] = id
                                    session['token'] = token

                                    return "register_success"
                                else:
                                    return "비밀번호가 일치하지 않습니다!"
                            else:
                                return "이미 존재하는 아이디입니다!"
                        else:
                            return "한 아이피당 한번만 가입이 가능합니다!"
            else:
                return "다른 자판기에 접속중이거나 이미 로그인된 상태입니다!"
        except Exception as e:
            print(f"오류 발생: {e}")
            traceback.print_exc()

# 인증번호와 만료시간을 저장할 전역 변수
verification_codes = {}

# 인증번호와 만료시간을 확인하는 함수
def is_code_valid(phone, user_code):
    if phone in verification_codes:
        code_info = verification_codes[phone]
        code, expiration = code_info['code'], code_info['expiration']
        if datetime.now() < expiration and user_code == code:
            return True
    return False

# 전역 변수 초기화
last_sent_times = {}
verification_codes = {}
# 전화번호 발송 횟수
send_counts = {}
# 차단할 전화번호 목록
blocked_numbers = ["01064996779"]

@app.route("/send_sms", methods=["POST"])
def send_sms():
    try:
        receive_phone = request.form["phone_number"]  # 받는 사람의 전화번호

        # 전화번호 형식 검증 (010[2-9]\d{7} 형식)
        if not re.match(r'^010[2-9]\d{7}$', receive_phone):
            return jsonify({"status": "error", "message": "0100x 형식이나 0101x 형식으로는 사용할 수 없습니다."}), 400

        # 차단된 번호 체크
        if receive_phone in blocked_numbers:
            return jsonify({"status": "error", "message": "해당 전화번호로는 인증번호를 전송할 수 없습니다."}), 403

        # 현재 시간
        current_time = datetime.now()

        # 하루 발송 횟수 체크
        if receive_phone not in send_counts:
            send_counts[receive_phone] = {'count': 0, 'last_reset': current_time}

        # 하루가 지났으면 카운트 초기화
        if current_time - send_counts[receive_phone]['last_reset'] > timedelta(days=1):
            send_counts[receive_phone]['count'] = 0
            send_counts[receive_phone]['last_reset'] = current_time

        # 발송 횟수 증가
        if send_counts[receive_phone]['count'] >= 10:
            return jsonify({"status": "error", "message": "하루에 10건의 인증번호만 전송할 수 있습니다."}), 429

        send_counts[receive_phone]['count'] += 1

        # 3분 쿨타임 체크
        if receive_phone in last_sent_times:
            last_sent_time = last_sent_times[receive_phone]
            if current_time < last_sent_time + timedelta(minutes=3):
                remaining_time = (last_sent_time + timedelta(minutes=3) - current_time).seconds
                return jsonify({"status": "error", "message": f"3분 후에 다시 시도해주세요. 남은 시간: {remaining_time // 60}분 {remaining_time % 60}초"}), 429

        # 6자리 인증번호 생성
        verification_code = str(random.randint(100000, 999999))
        # 만료시간 설정 (현재 시간으로부터 5분 후)
        expiration_time = current_time + timedelta(minutes=5)
        # 생성된 인증번호와 만료시간을 전역 변수에 저장
        verification_codes[receive_phone] = {'code': verification_code, 'expiration': expiration_time}
        
        # SMS 발송
        text = f'''[코드스톤]
가입을 위한 인증번호 : {verification_code}'''

        message = {
            'messages': [{
                'to': receive_phone,
                'from': sec.send_number,
                'text': text,
                'kakaoOptions': {
                    'pfId': sec.kakao_pfid,
                    'templateId': sec.kakao_templateid,
                    'variables': {
                        '#{verify_code}': verification_code,
                        '#{activity}': "가입인증"
                    }
                }
            }]
        }

        # 카카오 알림톡 전송
        coolsms_kakao.send_kakao(message)

        # 전송 시간 업데이트
        last_sent_times[receive_phone] = current_time

        print(f"[알림톡] {verification_code} -> {receive_phone}")
        return jsonify({"status": "success", "message": "인증번호가 전송되었습니다!"}), 200
    except Exception as e:
        print(f"문자 전송 중 오류가 발생했습니다: {str(e)}")
        return jsonify({"status": "error", "message": f"문자 전송 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route("/<name>/logout", methods=["GET"])
def logout(name):
    session.clear()
    return redirect("login")

@app.route("/logout", methods=["GET"])
def logout_2():
    session.clear()
    return js_location_href("/adm_login")

@app.errorhandler(404)
def not_found_error(error):
    return render_template("./404.html")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)