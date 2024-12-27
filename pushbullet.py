import json
import threading
from websocket import WebSocketApp
import coolsms_kakao  # 카카오톡 API 모듈
import security as sec

def register(auth_token: str, name: str, amount: int, shop_name: str, account: str, admin_number: str, on_success):
    def on_message(ws, message):
        try:
            message = json.loads(message)

            if message["type"] == "nop":
                return
            elif message["type"] == "push":
                push = message["push"]

                notification_name = ""
                notification_amount = 0

                print("[푸시불렛] {} | {}: {}".format(push["package_name"], push["title"], push["body"].replace("\n", " ")))

                if push["package_name"] == "com.IBK.SmartPush.app":
                    sp = push["body"].split(" ")
                    notification_name = sp[2]
                    notification_amount = int(sp[1].replace("원", "").replace(",", ""))
                    print(f"BankAPI[SUCCESS]: com.IBK.SmartPush.app")
                elif push["package_name"] == "com.nh.mobilenoti":
                    notification_name = message[5]
                    notification_amount = message[1].replace("입금", "").replace("원", "").replace(",", "")
                    notification_amount = int(notification_amount)
                    print(f"BankAPI[SUCCESS]: com.nh.mobilenoti")
                elif push["package_name"] == "com.wooribank.smart.npib":
                    sp = push["body"].split(" ")
                    notification_name = sp[1]
                    notification_amount = int(sp[5].replace("원", "").replace(",", ""))
                    print(f"BankAPI[SUCCESS]: com.nh.mobilenoti")
                elif push["package_name"] == "com.kakaobank.channel":
                    if "입금 " in push["title"]:
                        notification_name = push["body"].split(" ")[0]
                        notification_amount = int(push["title"].replace("입금 ", "").replace(",", "").replace("원", ""))
                        print(f"[푸시불렛] 카카오뱅크 입금 | {notification_name}: {notification_amount}원")
                elif push["package_name"] == "viva.republica.toss":
                    if "원 입금" in push["title"]:
                        notification_name = push["body"].split(" ")[0]
                        notification_amount = int(push["title"].replace(",", "").replace("원 입금", ""))
                        print(f"[푸시불렛] 토스뱅크 입금 | {notification_name}: {notification_amount}원")
                elif push["package_name"] == "nh.smart.banking":
                    if "원 입금" in push["title"]:
                        notification_name = push["body"].split(" ")[0]
                        notification_amount = int(push["title"].replace("입출금 알림: 농협 입금", "").replace(",", "").replace("원", ""))
                        print(f"[푸시불렛] NH농협은행 입금 | {notification_name}: {notification_amount}원")
                else:
                    return False

                # 입금 확인
                if name == notification_name and amount == notification_amount:
                    print(f"[푸시불렛] 성공 | {notification_name}: {notification_amount}원")
                    text = f'''[케이넷소프트]
계좌로 돈이 입금되었습니다.
금액 : {notification_amount}
예금주 : {notification_name}'''

                    # 카카오 알림톡으로 메시지 전송
                    message = {
                        'messages': [{
                            'to': admin_number,  # 관리자 번호로 변경
                            'from': sec.send_number,
                            'text': text,
                            'kakaoOptions': {
                                'pfId': sec.kakao_pfid,
                                'templateId': sec.kakao_templateid_charge,
                                'variables': {
                                    '#{shop_name}': shop_name,  # 샵 이름 추가
                                    '#{account}': account,      # 충전한 아이디 추가
                                    '#{name}': notification_name,  # 예금주
                                    '#{money}': notification_amount  # 입금 금액
                                }
                            }
                        }]
                    }
                    coolsms_kakao.send_kakao(message)  # 카카오 알림톡 전송
                    on_success()  # 성공 콜백 호출

                    ws.close()  # WebSocket 연결 종료
        except Exception as e:
            print(f"[푸시불렛] 오류")
            print(e)

    ws = WebSocketApp("wss://stream.pushbullet.com/websocket/" + auth_token, on_message=on_message)

    wst = threading.Thread(target=ws.run_forever)
    wst.start()

    print(f"[푸시불렛] 입금 신청 | {name}: {amount}원")
    return True