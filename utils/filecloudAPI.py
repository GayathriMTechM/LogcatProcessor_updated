import requests 
import os
from configparser import ConfigParser

# def read_config():
config = ConfigParser()
config.read("Config/config.ini")


def authentication_synology():
    # auth_url = f"https://Filecloud.techmahindra.com/webapi/auth.cgi"
    auth_url = f"{config["Filecloud"]["synology_url"]}/webapi/auth.cgi"
    otp = str(input("Enter Synology API otp here: "))
    params = {
        "api": "SYNO.API.Auth",
        "version": 6,
        "method": "login",
        "account": config["Filecloud"]["username"],
        "passwd": config["Filecloud"]["password"],
        "session": "FileStation",
        # "format": "sid",
        "otp_code": otp,
        "enable_device_token": "yes",
        "device_name": 'TAP-2WMKG63',
        # "device_id": "pBJBNBIZAFWSAejdGBmhSyfKgPScelIbMs0OR7m0I0jQeuBMsBCper8oaQZSvOzQa_u4nWIaIp08UjKjqrX50A"

    }
    response = requests.get(auth_url, params=params)
    response_data = response.json()
    # print(response_data)
    if "error" in response_data:
        print(f"Authentication failed: {response_data['error']['code']}")
        return None
    
    return response_data['data']['sid'] 
    # print(response_data)


#     return response_data

def list_files(sid, folder_path):
    list_url = f"{config['Filecloud']['synology_url']}/webapi/entry.cgi"
    params = {
        "api": "SYNO.FileStation.List",
        "version": 2,
        "method": "list",
        # "path": f'["{folder_path}"]',
        "folder_path": folder_path,
        "_sid" : sid
    }

    response = requests.get(list_url, params=params)
    print(response.request.url)
    response_data = response.json()
    print(response_data)

    if 'data' in response_data:
        if 'files' in response_data['data']:
            return response_data["data"]["files"]
        else:
            return []
    else:
        print(f"Failed to list files. Status Code {response.status_code}")
        return []

def download_file(sid, path):
    download_url = f"{config['Filecloud']['synology_url']}/webapi/entry.cgi"
    # print(download_url)
    
    params = {
        "api": "SYNO.FileStation.Download",
        "version": 2,
        "method": "download",
        "path": f'["{path}"]',
        # "path": path,
        "mode": "open",
        "_sid" : sid
    }
    # print(path)
    # headers = {
    #     # "session_id": sid
    #     "_sid" : sid
    # }
    # download_url = f"{synology_url}/webapi/entry.cgi?api={download_api}&version={download_version}&method={download_method}&path=%5B%22{path}%22%5D&mode=%22open%22&_sid={sid}"
    response = requests.get(download_url, params=params)
    # print(response.request.url)
    # response = requests.get(download_url, params=params, headers=headers)
    # print(response.status_code)
    # print(response.raise_for_status)

    if response.status_code == 200:
        # with open("test_download2.txt", "w", encoding='utf-8', errors='ignore') as f:
        #     f.write(response.text)
        return response.text
        # print(response.text)
        # return response.content
    else:
        print(f"Failed to download file. Status code: {response.status_code}")



# file_path = '/volume1/TMGMaps/11-16-2023/'

# file_path = '/TMGMaps/11-16-2023'
# sid = authentication_synology()
# print(sid)
# if sid:
#     download_file(sid, file_path)

#multiplefile 
if __name__ == "__main__":
    folder_path = '/TMGMaps/11-16-2023'
    sid = authentication_synology()
    if sid:
        files = list_files(sid, folder_path)

        for file_info in files:
            file_path = file_info['path']
            # print(file_path)
            # print(" ")
            download_file(sid, file_path)
            
