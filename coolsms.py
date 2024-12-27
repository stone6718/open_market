import security as sec
from sdk.api.message import Message
from sdk.exceptions import CoolsmsException

def send_sms(to, text):
    api_key = sec.coolsms_api_key # API KEY
    api_secret = sec.coolsms_api_secret # API 보안키
    from_ = sec.send_number # 보내는 번호
    type = select_message_type(text)  # 메시지 타입 선택

    params = {
        'type': type,  # 메시지 타입 (sms, lms, mms, ata)
        'to': to,  # 받는 사람 번호 (여러 번호로 보낼 경우 콤마로 구분)
        'from': from_,  # 보내는 사람 번호
        'text': text  # 메시지 내용
    }

    cool = Message(api_key, api_secret)
    try:
        response = cool.send(params)
        print("Success Count : %s" % response['success_count'])
        print("Error Count : %s" % response['error_count'])
        print("Group ID : %s" % response['group_id'])

        if "error_list" in response:
            print("Error List : %s" % response['error_list'])

    except CoolsmsException as e:
        print("Error Code : %s" % e.code)
        print("Error Message : %s" % e.msg)

def select_message_type(content):
    length = len(content)
    if length <= 90:
        return 'sms'
    elif length <= 2000:
        return 'lms'
    else:
        return 'mms'

# 예시 사용법
content = "여기에 메시지 내용을 입력하세요"
message_type = select_message_type(content)
print(f"선택된 메시지 유형: {message_type}")