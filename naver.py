import bcrypt
import pybase64
import time
import requests
import datetime


def get_timestamp():
    return int(time.time() * 1000)


def create_signature(client_id: str, client_secret: str, timestamp: int) -> str:
    # 밑줄로 연결하여 password 생성
    password = client_id + "_" + str(timestamp)

    # bcrypt 해싱
    hashed = bcrypt.hashpw(password.encode('utf-8'), client_secret.encode('utf-8'))

    # base64 인코딩
    return pybase64.standard_b64encode(hashed).decode('utf-8')


def get_token(client_id: str, client_secret: str) -> tuple[bool, str]:
    timestamp = get_timestamp()

    res = requests.post(
        "https://api.commerce.naver.com/external/v1/oauth2/token",
        data={
            "client_id": client_id,
            "timestamp": timestamp,
            "grant_type": "client_credentials",
            "client_secret_sign": create_signature(client_id, client_secret, timestamp),
            "type": "SELF"
        }
    )

    if res.status_code != 200:
        return False, "네이버 커머스API OAuth2 인증 토큰 발급에 실패하였습니다"

    return True, res.json()["access_token"]


def get_order_ids(token: str, order_id: str) -> tuple[bool, str, list[str]]:
    if not order_id.isnumeric():
        return False, "주문번호가 숫자가 아닙니다", []

    res = requests.get(
        f"https://api.commerce.naver.com/external/v1/pay-order/seller/orders/{order_id}/product-order-ids",
        headers={
            "authorization": f"Bearer {token}"
        }
    )

    if res.status_code != 200:
        return False, res.json()["message"], []

    return True, res.json()["traceId"], res.json()["data"]


def get_order_details(token: str, order_ids: list[str]) -> tuple[bool, str, list[dict]]:
    if not all(order_id.isnumeric() for order_id in order_ids):
        return False, "주문 ID가 숫자가 아닙니다", []

    res = requests.post(
        "https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders/query",
        headers={
            "authorization": f"Bearer {token}",
            "content-type": "application/json"
        },
        json={
            "productOrderIds": order_ids
        }
    )

    if res.status_code != 200:
        return False, res.json()["message"], []

    return True, res.json()["traceId"], res.json()["data"]


def deliver_order(token: str, order_id: str) -> tuple[bool, str]:
    if not order_id.isnumeric():
        return False, "주문 ID가 숫자가 아닙니다"

    # 현재 시간을 한국 시간(UTC+9)으로 설정
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    dispatch_date = now.isoformat(timespec='milliseconds')  # 밀리초까지 포함

    res = requests.post(
        "https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders/dispatch",
        headers={
            "authorization": f"Bearer {token}",
            "content-type": "application/json"
        },
        json={
            "dispatchProductOrders": [
                {
                    "productOrderId": order_id,
                    "deliveryMethod": "DIRECT_DELIVERY",
                    "dispatchDate": dispatch_date
                }
            ]
        }
    )

    print(res.json())  # 응답 JSON 출력

    if res.status_code != 200:
        return False, res.json().get("message", "알 수 없는 오류가 발생했습니다.")

    data = res.json().get("data", {})

    # 성공적인 처리
    if "successProductOrderIds" in data and len(data["successProductOrderIds"]) == 1:
        return True, data.get("traceId", "트레이스 ID를 찾을 수 없습니다.")

    # 실패한 주문 정보 처리
    if "failProductOrderInfos" in data and len(data["failProductOrderInfos"]) > 0:
        return False, data["failProductOrderInfos"][0].get("message", "오류 메시지를 찾을 수 없습니다.")

    return False, "알 수 없는 오류가 발생했습니다."