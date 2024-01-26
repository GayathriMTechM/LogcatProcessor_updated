import requests
import configparser
import json
from datetime import datetime, timedelta

config = configparser.ConfigParser()
config.read('Config/config.ini')


def request_token():
    try:
        # print('Token Requested!')
        #config = configparser.ConfigParser()
        #config.read('Config/config.ini')
        token_expired_time = datetime.now() - datetime.strptime(config['iTMS_TOKEN']['token_expiry'], '%Y-%m-%d %H:%M:%S.%f')
        if config['iTMS_TOKEN']['access_token'] and token_expired_time.seconds < 3600 :
            refresh_token()
        else:
            credentials = config['CREDENTIALS']
            #url = "https://itms.techmahindra.com/aquawebng/api/token"
            payload = 'grant_type=password' + '&username=' + credentials['username'] \
                      + '&password=' + credentials['password']
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            token = json.loads(requests.request("POST", config['URL']['oauth2'], headers=headers, data=payload).text)
            #token = {'access_token': '4NCYWsKKdlzkN5WjhqBd14ai3R-vK8HwjMCDHVnLRTgxmjSUfpzasEQ2wnAewaLa1TQhRHBG2UyHKnbkOQKw3pw9qw-Au7S9TUOsgL_nZb2n0K46uAzUH4yjdNglO_ZRnbVBYnEALwwhIEvsLYSxoFPFwnq6gePDWM9dfTX6biQ_MNYDDArwZo1Z6KnbdpBJKT_nCj2rM7-J1Ql1GrMwtgL1w_xDaC4dDCqIdjqB85MxMcgfW5hvvSOGmHDIMMkbhz0LZzUb_Al4HY8B9wB0KfEFuPFIW_smfAE_7Gy0kGVIfORlnUBvd4nx7BTCtwtwxJxvOWVwST-r_z1uaNyKwyX-so0upJxf6cQb4mszQ6DAFsQ2pEN1flC8psfDBvD8lqpTohMwuQJ_NCtRilKxPPCGeEn7VcO4uUsVkXnZg9tVgXIIwSdbLvSC5HXWSP0l8f5xDe5TVpV2d9IZ9lVVaU1CLp2OQ2N-n_vbiB2C6geR2jJsgOLE8UIpgOu8jF1UDBj6FYjP6L1ayRLOGAFhwzaBnYVATTCOsdv2i2sH34_BHygcqQR6ojeWMIK6VKI147-P0y6TFSxoVxjedDPypDyapPfFy30fBjPfiChWgs7azCLRz7gTuMsM9qlEbmzm', 'token_type': 'bearer', 'expires_in': 599, 'refresh_token': 'fd98bb4bdf9d47c8af25bcbfc074f17a', '.issued': 'Mon, 15 Aug 2022 18:51:22 GMT', '.expires': 'Mon, 15 Aug 2022 19:01:22 GMT'}
            iTMSToken = config['iTMS_TOKEN']
            iTMSToken['access_token'] = token['access_token']
            iTMSToken['token_type'] = token['token_type']
            iTMSToken['expires_in'] = str(token['expires_in'])
            iTMSToken['refresh_token'] = token['refresh_token']
            iTMSToken['.issued'] = token['.issued']
            iTMSToken['.expires'] = token['.expires']
            iTMSToken['token_expiry'] = datetime.strftime(datetime.now() + timedelta(seconds=int(token['expires_in'])),'%Y-%m-%d %H:%M:%S.%f')
            with open('../Config/config.ini', 'w') as configfile:
                config.write(configfile)
            # print('Token received successfully!')
            return True
    except Exception as e:
        print(e)
        return False


def refresh_token():
    try:
        # print('Token refresh request received')
        url = "https://itms.techmahindra.com/aquawebng/api/token"
        payload = 'grant_type=refresh_token&refresh_token=' + config['iTMS_TOKEN']['refresh_token']
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        token = json.loads(requests.request("POST", config['URL']['oauth2'], headers=headers, data=payload).text)
        # token = {'access_token': '4NCYWsKKdlzkN5WjhqBd14ai3R-vK8HwjMCDHVnLRTgxmjSUfpzasEQ2wnAewaLa1TQhRHBG2UyHKnbkOQKw3pw9qw-Au7S9TUOsgL_nZb2n0K46uAzUH4yjdNglO_ZRnbVBYnEALwwhIEvsLYSxoFPFwnq6gePDWM9dfTX6biQ_MNYDDArwZo1Z6KnbdpBJKT_nCj2rM7-J1Ql1GrMwtgL1w_xDaC4dDCqIdjqB85MxMcgfW5hvvSOGmHDIMMkbhz0LZzUb_Al4HY8B9wB0KfEFuPFIW_smfAE_7Gy0kGVIfORlnUBvd4nx7BTCtwtwxJxvOWVwST-r_z1uaNyKwyX-so0upJxf6cQb4mszQ6DAFsQ2pEN1flC8psfDBvD8lqpTohMwuQJ_NCtRilKxPPCGeEn7VcO4uUsVkXnZg9tVgXIIwSdbLvSC5HXWSP0l8f5xDe5TVpV2d9IZ9lVVaU1CLp2OQ2N-n_vbiB2C6geR2jJsgOLE8UIpgOu8jF1UDBj6FYjP6L1ayRLOGAFhwzaBnYVATTCOsdv2i2sH34_BHygcqQR6ojeWMIK6VKI147-P0y6TFSxoVxjedDPypDyapPfFy30fBjPfiChWgs7azCLRz7gTuMsM9qlEbmzm','token_type': 'bearer', 'expires_in': 599, 'refresh_token': 'fd98bb4bdf9d47c8af25bcbfc074f17a','.issued': 'Mon, 15 Aug 2022 18:51:22 GMT', '.expires': 'Mon, 15 Aug 2022 19:01:22 GMT'}
        iTMSToken = config['iTMS_TOKEN']
        iTMSToken['access_token'] = token['access_token']
        iTMSToken['token_type'] = token['token_type']
        iTMSToken['expires_in'] = str(token['expires_in'])
        iTMSToken['refresh_token'] = token['refresh_token']
        iTMSToken['.issued'] = token['.issued']
        iTMSToken['.expires'] = token['.expires']
        iTMSToken['token_expiry'] = datetime.strftime(datetime.now() + timedelta(seconds=int(token['expires_in'])),
                                                      '%Y-%m-%d %H:%M:%S.%f')
        with open('../Config/config.ini', 'w') as configfile:
            config.write(configfile)
        # print('Token refreshed successfully')
        return True
    except Exception as e:
        print('Error: refresh_token - {}'.format(e))
        return False


def end_session():
    try:
        # print('End Session Requested!')
        iTMSToken = config['iTMS_TOKEN']
        if iTMSToken['access_token']:
            url = "https://itms.techmahindra.com/aquawebng/api/Session"
            payload = ''
            headers = {
                'Authorization': iTMSToken['token_type'] + ' ' + iTMSToken['access_token']
            }
            token = json.loads(requests.request("DELETE", config['URL']['session'], headers=headers, data=payload).text)

            if token == 'logout successful':
                print('Session Ended Successfully!')
                iTMSToken['access_token'] = ''
                iTMSToken['token_type'] = ''
                iTMSToken['expires_in'] = ''
                iTMSToken['refresh_token'] = ''
                iTMSToken['.issued'] = ''
                iTMSToken['.expires'] = ''
                iTMSToken['token_expiry'] = ''
                with open('../Config/config.ini', 'w') as configfile:
                    config.write(configfile)
            else:
                print(token)
        else:
            print('No active session available!')
        return True
    except Exception as e:
        print(e)
        return False


def is_token_valid():
    #print('Authentication - is_token_valid request received!')
    #config = configparser.ConfigParser()
    #config.read('Config/config.ini')
    token = config['iTMS_TOKEN']
    if datetime.now() < datetime.strptime(token['token_expiry'], '%Y-%m-%d %H:%M:%S.%f'):
        return True
    else:
        return False


def get_token():
    try:
        #print('Authentication - get_token request received!')
        if config['iTMS_TOKEN']['access_token'] == '' or not is_token_valid():
            request_token()
        #print('Authentication - Token provided!')
        return config['iTMS_TOKEN']['token_type'] + ' ' + config['iTMS_TOKEN']['access_token']
    except Exception as e:
        print('Error to get token: {}'.format(e))
        return False


if __name__ == '__main__':
    #print('Request Token: ', requestToken())
    #print('Is Token Valid', isTokenValid())
    #print(refresh_token())
    #print(get_token())
    print(end_session())

'''
config = configparser.ConfigParser()
config.read('config.ini')
#payload='grant_type=password&username=iTMSDeTrac&password=HVRSTEDWOYRKCNX'


url = "https://itms.techmahindra.com/aquawebng/api/token"

payload='grant_type='+ config['DEFAULT']['grant_type'] +'&username='+ config['DEFAULT']['username'] \
        +'&password='+ config['DEFAULT']['password']
headers = {
  'Content-Type': 'application/x-www-form-urlencoded',
  'Cookie': 'aquaSessionId=u4k1z0deevkyz2afsmorr01p'
}

token = requests.request("POST", url, headers=headers, data=payload)

print(token.text)

x = '{"access_token":"o48cGt0EgJlpZIHxhN5LlE8mjqMivzOqETlJag3_0sH6JnREj9IOlEd-M6d00s3hY6QlK3YqpZ2AAKHhqM4xv8PFN92iU8H9CFkobYgHCEqWsaE5neP5xx-DChu0Jnc5N3DkVf5IHYT6X153BFK8EYBX7nKSBAXEgGca2GFHiVHN6aa7tbw35Xny2wRd62lciMH99zwEVTVW0PEIaGFtOyST1Iygd2ciwbOuNuYLwBNPP1HClUWq0CGP8B944GjLM5flzaJHZVSs-qgdDSaZlAyOSPUO3xsUXLZcLLR3yqvKUQYmbojSXN7Y3inm5PefXUyg0a06EovSOS1apD61GhcS9AaHjkKO08ws8OUoi2ATmHPbvkv3DbwPopxexTakyEjnRwfVXWt9BZoWUgJ_0y4RN49Z764kGnJ_7RvQ4hbUcb_R-p9nnV4YQt51YBRaXoMd2qU5UkVHxb8thDeWfVb-OCky5Gjs8ek6Epb7YthEuCQs8nID6XJAUI6yyhkrLkic48BuVFG6h9l8Zm7mADaaAvwY3AmSIK23tx1WuJRxjBDyj38yVRR2JJtbYnw7OWGwRYJ8dRNiF60M3TN79gcin1IU17RE4d_riY9KdjBMWu_n9We2LUTAUG1r9g_9","token_type":"bearer","expires_in":599,"refresh_token":"c9d62b3e376e480e858c5b6a9888c359",".issued":"Mon, 08 Aug 2022 20:36:12 GMT",".expires":"Mon, 08 Aug 2022 20:46:12 GMT"}'
y = json.loads(x)
print(y["access_token"])


date_time_str = 'Mon, 08 Aug 2022 19:59:32 GMT'

date_time_obj = datetime.datetime.strptime(date_time_str, '%a, %d %b %Y %H:%M:%S %Z')


print("The type of the date is now",  type(date_time_obj))
print("The date is", date_time_obj)
print(datetime.datetime.now(datetime.timezone).strftime("%Y-%m-%dT%H:%M:%S.%f%Z"))

UTC_datetime_timestamp = float(date_time_obj.strftime("%s"))
local_datetime_converted = datetime.datetime.fromtimestamp(UTC_datetime_timestamp)

print("The date is", local_datetime_converted)

from dateutil import parser
#print(parser.parse(date_time_str))
'''