import time, datetime, uuid, hmac, hashlib, requests, platform
import security as sec

# 아래 값은 필요시 수정
protocol = 'https'
domain = 'api.coolsms.co.kr'
prefix = ''


def unique_id():
    return str(uuid.uuid1().hex)


def get_iso_datetime():
    utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
    utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
    return datetime.datetime.now().replace(tzinfo=datetime.timezone(offset=utc_offset)).isoformat()


def get_signature(key, msg):
    return hmac.new(key.encode(), msg.encode(), hashlib.sha256).hexdigest()


def get_headers(api_key, api_secret):
    date = get_iso_datetime()
    salt = unique_id()
    combined_string = date + salt

    return {
        'Authorization': 'HMAC-SHA256 ApiKey=' + api_key + ', Date=' + date + ', salt=' + salt + ', signature=' +
                         get_signature(api_secret, combined_string),
        'Content-Type': 'application/json; charset=utf-8'
    }


def get_url(path):
    url = '%s://%s' % (protocol, domain)
    if prefix != '':
        url = url + prefix
    url = url + path
    return url


def send_many(parameter):
    api_key = sec.coolsms_api_key
    api_secret = sec.coolsms_api_secret
    parameter['agent'] = {
        'sdkVersion': 'python/4.2.0',
        'osPlatform': platform.platform() + " | " + platform.python_version()
    }

    return requests.post(get_url('/messages/v4/send-many'), headers=get_headers(api_key, api_secret), json=parameter)


def send_kakao(data):
    result = send_many(data)
    response = result.json()

    if response["status"] == "SENDING":
        print(f"[알림톡] {data['messages'][0]['to']}: {response['log'][-1]['message']}")
        return True
    else:
        print(f"[알림톡] {data['messages'][0]['to']}: {response['status']}")
        return False