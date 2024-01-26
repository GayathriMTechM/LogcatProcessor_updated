from utils.filecloudAPI import authentication_synology, download_file, list_files
from data_processor_main import GeneralProcessor

def get_filecloud_data():
    sid = authentication_synology()
    if sid:
        folder_path = '/TMGMaps/11-16-2023'
        files = list_files(sid, folder_path)

        for file_info in files:
            file_path = file_info['path']
            # print(file_path)
            # break
            # print(" ")
            file_data = download_file(sid, file_path)
            genealprocessor = GeneralProcessor()
            genealprocessor.filecloud_data_process(file_data, file_path)
            
get_filecloud_data()