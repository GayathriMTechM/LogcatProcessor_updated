import pymongo
import datetime 
import re
import iTMS
import sys 
import json
import pandas as pd
import os 
from urllib.error import HTTPError
import requests
from collections import defaultdict

first_value=''
# tcList = ['TC2971498']
# env = 'R&D'  # R&D or Production
# info = {'env': env}

def get_iTMS(tcList, info):
    if True:
        requiredTestCasesList = []
        project_path_tc_dict = defaultdict(list)
        # Get iTMS Test Cases List for TMO Project
        testCaseList = iTMS.TMO_TCs_List()

        # Logic for Test Cases which needs to be uploaded
        for iTestCase in testCaseList:
            if iTestCase['TechM Test ID'] in tcList:
                path = iTestCase['Path'].split('T-Mobile Field Performance/')[1]
                project_path_tc_dict[path].append(iTestCase['TechM Test ID'])
                requiredTestCasesList.append(iTestCase)

    # Get a list of TCs from Required TCs List which has correct Project folder structure
    project_path_tc_dict_details = {}
    tc_not_uploaded = []
    for i in range(len(requiredTestCasesList)):
        project_path = '/'.join(requiredTestCasesList[i]['Path'].split('/')[1:])
        if project_path in project_path_tc_dict.keys():
            requiredTestCasesList[i]['Project ID'] = project_path_tc_dict[project_path]
            if project_path in project_path_tc_dict_details.keys():
                project_path_tc_dict_details[project_path].append(requiredTestCasesList[i])
            else:
                project_path_tc_dict_details[project_path] = [requiredTestCasesList[i]]
        else:
            tc_not_uploaded.append(requiredTestCasesList[i]['TechM Test ID'])

    # print(project_path_tc_dict)
    # print(project_path_tc_dict_details)
    # quit()

    # Process TCs in all project paths
    for i_project_path in project_path_tc_dict.keys():
        # info['Project Path'] = i_project_path
        # info['Project ID'] = project_path_tc_dict[i_project_path]
        test_case_count = 0
        # Read, process and upload TCs
        for iTestCase in project_path_tc_dict_details[i_project_path]:
            test_case_count += 1

            # Get Uploaded File info from MongoDB for test case
            # if needed, add code
            uploadedFileIdList = []
            uploadedFileNameList = []
            print(iTestCase['KPI'])

            # Get test case file location
            attachmentMetaData = iTMS.get_attachment_metadata_list(iTestCase['iTMSId'])

            # Get download URL for excel/csv files
            # downloadUrlList = []
            file_path = []
            file_id = []
            df_list = []

            text_file_path = []
            text_file_id = []
            text_file_contents_list = []

            file_count = 0
            try:
                total_files_count = str(len(attachmentMetaData))
            except:
                total_files_count = '#'

            # for iFileData in attachmentMetaData:
            file_count = 0
            while file_count < len(attachmentMetaData):
                iFileData = attachmentMetaData[file_count]

                print("Reading file# {}/{} - {}".format(file_count, total_files_count, iFileData['Filename']))
                if iFileData['FileExtension'] in ['.xlsx', '.xlsm', '.xls', '.csv'] and iFileData['Id'] not in file_id:
                    if True:
                        try:
                            if iFileData['FileExtension'] == '.xlsx' or iFileData['FileExtension'] == '.xlsm':
                                df_list.append(pd.read_excel(iFileData['DownloadUrl'], engine='openpyxl'))
                                file_path.append(iFileData['Filename'])
                                file_id.append(iFileData['Id'])
                            elif iFileData['FileExtension'] == '.xls':
                                df_list.append(pd.read_excel(iFileData['DownloadUrl']))
                                file_path.append(iFileData['Filename'])
                                file_id.append(iFileData['Id'])
                            elif iFileData['FileExtension'] == '.csv':
                                df_temp_first_row = pd.read_csv(iFileData['DownloadUrl'], nrows=10, on_bad_lines='skip',
                                                                encoding='cp437',
                                                                encoding_errors='replace')  # encoding='cp1252'

                                rows_skip = 0
                                '''
                                if 'IDX' in '\t'.join(df_temp_first_row.columns.tolist()):
                                    rows_skip = 0
                                elif rows_skip == 0 and 'IMEI' in '\t'.join(df_temp_first_row.columns.tolist()):
                                    rows_skip = 5
                                else:
                                    for i in range(df_temp_first_row.shape[0]):
                                        if df_temp_first_row.iloc[i, 0] == 'IDX':
                                            rows_skip = i + 1
                                            break
                                '''
                                df_temp = pd.read_csv(iFileData['DownloadUrl'], header=rows_skip, low_memory=False,
                                                      encoding='cp437',
                                                      encoding_errors='replace')
                                for i, row in df_temp.iterrows():
                                    for j in df_temp.columns:
                                        if pd.api.types.is_string_dtype(df_temp[j][i]) and "e+" in df_temp[j][i]:
                                            df_temp[j][i] = int(df_temp[j][i])
                                df_list.append(df_temp)
                                file_path.append(iFileData['Filename'])
                                file_id.append(iFileData['Id'])
                                # df_temp_first_row = pd.read_csv(iFileData['DownloadUrl'], nrows=1)
                                # #logger.info(df_temp_first_row.columns.values.tolist())
                                # if 'IMEI' in '\t'.join(df_temp_first_row.columns.tolist()):
                                #     df_temp = pd.read_csv(iFileData['DownloadUrl'], header=5, low_memory=False)
                                #     for i, row in df_temp.iterrows():
                                #         for j in df_temp.columns:
                                #             if "e+" in str(df_temp[j][i]):
                                #                 df_temp[j][i] = int(df_temp[j][i])
                                #     df_list.append(df_temp)
                                #     file_path.append(iFileData['Filename'])
                                #     file_id.append(iFileData['Id'])
                                # else:
                                #     df_temp = pd.read_csv(iFileData['DownloadUrl'], header=0, low_memory=False)
                                #     for i, row in df_temp.iterrows():
                                #         for j in df_temp.columns:
                                #             if "e+" in df_temp[j][i]:
                                #                     df_temp[j][i] = int(df_temp[j][i])
                                #     df_list.append(df_temp)
                                #     file_path.append(iFileData['Filename'])
                                #     file_id.append(iFileData['Id'])
                            else:
                                print("Requested file '{}' will not be processed.".format(iFileData['Filename']))
                                raise Exception("File not supported")
                            file_count += 1
                        except HTTPError as e:
                            if e.code == 500:
                                attachmentMetaData = iTMS.get_attachment_metadata_list(iTestCase['iTMSId'])
                        except Exception as e:
                            print("Excel file read error. {}".format(e))
                            print("{}:{} - {}".format(info['TC ID'], iFileData['Id'], iFileData['Filename']))
                    # break
                elif iFileData['FileExtension'] in ['.txt']:
                    if True:
                        response = requests.get(iFileData['DownloadUrl'])
                        if response.status_code == 200:
                            text_file_contents_list.append(response.text)
                            text_file_path.append(iFileData['Filename'])
                            text_file_id.append(iFileData['Id'])
                        else:
                            print("Text file read error. {}".format(response.status_code))
                            print('{}:{} - {}'.format(info['TC ID'], iFileData['Id'], iFileData['Filename']))
                    file_count += 1
                else:
                    print("File '" + iFileData['Filename'] + "' will not be processed as file extension is not "
                                                                   ".xls, .xlsx., .xlsm, .csv., .txt or .json")
                    file_count += 1
            
            # for i in range(len(text_file_contents_list)):
            #     # print(text_file_path[i])
            #     #print(text_file_contents_list[i])
                #contents = text_file_contents_list[i]
                #print(contents)
                
                # x(contents)
                # for line in contents.split("\n"):
                #     print(line)
                # quit()
            # return contents, text_file_path
            return text_file_contents_list, text_file_path
# get_iTMS(tcList, info)
# quit()


class kpi_adb_automation:
    def __init__(self):
        # self.filename = filename
        self.data = {}
        # self.keys_to_search = []
        self.keys_to_search = [
            "Filename",
            "Type",
            "Time",
            "DEBUG INFO",
            "HPLMN",
            "sim_state",
            "Serving PLMN",
            "Roaming",
            "NW sel mode",
            "Service",
            "MM5G",
            "NR5G_RSRP",
            "NR5G_SINR",
            "NR5G_RSRQ",
            "NR_RRC",
            "NR_SSB_Index",
            "NR_ARFCN",
            "NR_PCI",
            "NR_BAND",
            "NR_DL Scheduling",
            "NR_BLER",
            "NR_BW",
            "NR_SA_RLF Count",
            "NR_Tx Phy Channel Type",
            "NR_Tx Pwr",
            "NR_CDRX",
            "NETWORK",
            "FINAL IMEI Certi",
        ]

    def ModemServiceMode(self, line):
        response = {"Type": "ModemServiceMode"}

        timestamp_match = re.search(r'^(\d+-\d+ \d+:\d+:\d+\.\d+)', line)

        if timestamp_match:
            response["Timestamp"] = timestamp_match.group(1)

        pattern1 = r'Line (\d+) : ((?:\w+\s*[:\(]\s*[^)]+?\s*[)\:]\s*)+|[^:]+): ((?:[^_]+_)+|[^:]+)_'
        matches1 = re.findall(pattern1, line)
        serving_plmn_match = re.search(r'Serving PLMN\((.*?)\)', line)

        if not matches1:
            pattern2 = r'(\w+)\s*[:\(]\s*([^)]+?)\s*[)\:]'
            matches2 = re.findall(pattern2, line)
            for key, value in matches2:
                key = key.strip()
                value = value.strip()
                response[key] = value
        if serving_plmn_match:
            response["Serving PLMN"] = serving_plmn_match.group(1)
        else:
            for x, key, value in matches1:
                key = key.strip()
                value = value.strip()
                response[key] = value

        
        current_time = response.get("Timestamp")
        current_type = response.get("Type", "ModemServiceMode")
        self.data.setdefault((current_time, current_type), []).append(response)

        return response


    def group_data(self):
        records = []
        for (timestamp, data_type), data_list in self.data.items():
            record = {"Timestamp": timestamp, "Type": data_type}
            for key in self.keys_to_search:
                for data in data_list:
                    if key in data and data[key] is not None:
                        if key =="DEBUG INFO":
                            record["Value"] = data[key]
                        record[key] = data[key]


            records.append(record)
        # print(len(records))
        # print(records)
        return records


    def format_time(self, timestamp):
        formatted_time = datetime.datetime.strptime(timestamp, "%d-%m %H:%M:%S.%f").strftime("%d-%m %H:%M:%S.%f")[:-4]
        return formatted_time
    
    def clear(self):
        self.data.clear()
    
class TelecomDataProcessor:
    def __init__(self):
        # self.filename = filename
        self.data = []
        self.event_id = None

        self.patterns = [
            (r'InCallController: onCallAdded: \[Call id=TC@(?P<call_id>\d+), state=(?P<state>\w+).*?handle=(?P<tel>\S+), (?:.+)]', ['state', 'tel']),
            (r'InCallController: Sending updateCall \[Call id=TC@(?P<call_id>\d+), state=(?P<state>\w+), (?:handle=(?P<handle>\S+), )?(?P<other>.+)\]', ['state']),
            (r'Event: RecordEntry TC@(?P<call_id>\d+): CREATED, (?P<first_value>.+)',  ['first_value']),
            (r'Event: RecordEntry TC@(?P<call_id>\d+): SET_CONNECTING, (?P<isIncoming>.+), (?P<value>.+)',['isIncoming', 'value']),
            (r'Event: RecordEntry TC@(?P<call_id>\d+): START_CONNECTION, tel:(?P<tel>\S+)', ['tel']),
            (r'Event: RecordEntry TC@(?P<call_id>\d+): START_OUTGOING_CALL - state=(?P<state>.+)',  ['state']),
            (r'Event: RecordEntry TC@(?P<call_id>\d+): NEW_OUTGOING_CALL, tel:(?P<tel>\S+)', ['tel']),
            (r'Event: RecordEntry TC@(?P<call_id>\d+): SET_RINGING, (?P<value>.+)', ['value']),
            # (r'Event: RecordEntry TC@(?P<call_id>\d+): RINGER_INFO, (?P<isringeraudible>.+)',  ['isringeraudible']),
            (r'Event: RecordEntry TC@(?P<call_id>\d+): RINGER_INFO, isRingerAudible=(?P<value>true|false)', ['value']),
            (r'Event: RecordEntry TC@(?P<call_id>\d+): START_RINGER, (?P<value>.+)',  ['value']),
            (r'Event: RecordEntry TC@(?P<call_id>\d+): REQUEST_ACCEPT, videoState : (?P<videoState>.+)', ['videoState']),
            (r'Event: RecordEntry TC@(?P<call_id>\d+): STOP_RINGER, (?P<value>.+)',  ['value']),
            (r'Event: RecordEntry TC@(?P<call_id>\d+): SET_ANSWERED, (?P<answered>.+)', ['answered']),
            (r'Event: RecordEntry TC@(?P<call_id>\d+): SET_DIALING, (?P<value>.+)',  ['value']),
            (r'Event: RecordEntry TC@(?P<call_id>\d+): START_RINGBACK',  ['value']),
            # (r'Event: RecordEntry TC@(?P<call_id>\d+): SET_DISCONNECTED, disconnected set explicitly> DisconnectCause.*?Reason: \((?P<reason>\d+),.*?ImsReasonInfo: .*?: \{(?P<imsreason>\d+) :', ['reason', 'imsreason']),
            (r'Event: RecordEntry TC@(?P<call_id>\d+): SET_DISCONNECTED, disconnected set explicitly> DisconnectCause \[.*?Reason: \((?P<reason>[^)]+)\).*?ImsReasonInfo :: \{(?P<imsreason>[^}]+)\}', ['reason', 'imsreason']),
            (r'Event: RecordEntry TC@(?P<call_id>\d+): DESTROYED, (?P<value>.+)',  ['value'])
        ]

    def extract_event_id(self, line):
            event_id_match = re.search(r'TC@(\d+)', line)
            if event_id_match:
                self.event_id = event_id_match.group(1)

    def extract_info(self, line):
        timestamp_match = re.match(r'^\d+-\d+ \d+:\d+:\d+\.\d+', line)
        if timestamp_match:
            timestamp = timestamp_match.group(0)
            # formatted_time = datetime.datetime.strptime(timestamp, "%d-%m %H:%M:%S.%f").strftime("%d-%m %H:%M:%S.%f")[:-4]
            # print(formatted_time)
            line = line[len(timestamp):]
            # print(line)
        self.extract_event_id(line)

        for pattern, keys in self.patterns:
            match = re.search(pattern, line)
            if match:
                if 'TC@(?P<call_id>\d+)' in pattern:
                    updated_pattern = pattern.replace(r'TC@(?P<call_id>\d+)', rf'TC@{self.event_id}')
                else:
                    updated_pattern = pattern
                tag_match = re.match(r'(.*?)(,|\[)', updated_pattern)
                if tag_match:
                    tag = tag_match.group(1)
                    if tag.startswith("InCallController: Sending updateCall \\"):
                        tag = tag.replace("InCallController: Sending updateCall \\", "InCallController: Sending updateCall ")
                    if tag.startswith("InCallController: onCallAdded: \\"):
                        tag=tag.replace("InCallController: onCallAdded: \\", "InCallController: onCallAdded")                        
                else:
                    tag = updated_pattern

                tc_id=f"TC@{self.event_id}"
                # print(tc_id)
                if tc_id in tag:
                    parts=tag.split(f'{tc_id}:')
                    event=parts[0]
                    subevent=parts[1]
                else:
                    parts=tag.split(':')
                    event=parts[0]
                    subevent=parts[-1]

                entry = {"Timestamp": timestamp, "Type": "Telecom", "Call ID": self.event_id, "Event": event, "Method": tag,"Sub-Event":subevent }


                value = {key: match.group(key) if key in match.groupdict() else None for key in keys}

                if "first_value" in keys and 'first_value' in match.groupdict():
                    global first_value
                    first_value = match.group('first_value').split(', ')
                    if len(first_value)>=2:
                        first_value = first_value[-2]
                        entry["Value"] = {'state': first_value}
                    else:
                        first_value = first_value[0]
                        entry["Value"] = {'state': first_value}
                elif 'videoState' in keys and 'videoState' in match.groupdict():
                    video_state = match.group('videoState').split(' : ')[0]
                    # entry["Value"] = {'videoState': video_state}
                    entry["Value"] = video_state
                elif 'answered' in keys and 'answered' in match.groupdict():
                    answered = match.group('answered').split(': ')[1]
                    entry["Value"] = answered
                elif 'tel' in keys and 'tel' in match.groupdict():
                    tel = match.group('tel').split(': ')[0]
                    entry["Value"] = tel
                elif 'reason' and 'imsreason' in keys and 'reason' and 'imsreason'in match.groupdict():
                    reason = match.group('reason').split(': ')[0]
                    imsreason = match.group('imsreason').split(': ')[0] + match.group('imsreason').split(': ')[1]
                    entry["Reason"] = reason
                    entry["Imsreason"] = imsreason
                    entry["Value"]=''
                
                elif 'value' in keys and 'value' in match.groupdict():
                    value_part = match.group('value').split(': ')[0]
                    if "START_RINGER" in tag and value_part.lower() == 'null':
                        # entry["Value"] = {'state': 'Start Ringing','value': 'null', }
                        entry["State"] = "Start Ringing"
                        entry["Value"] = "Null"
                    elif "STOP_RINGER" in tag and value_part.lower()=='null':
                        entry["State"] = "Stop Ringing"
                        entry["Value"] = "Null"
                        # entry["Value"] = {'state': 'Stop Ringing','value': 'null', }
                    elif "SET_RINGING" in tag:
                        entry["Value"]={'state': value_part}
                    elif "SET_DIALING" in tag:
                        entry["Value"]={'state': value_part}  
                    elif "START_RINGBACK" in tag:
                        entry["Value"] = value_part
                        # print(value_part)              
                    else:
                        entry["Value"] = value_part
                        
                else:
                    entry["Value"] = value
                
                if 'state' in entry["Value"]:
                    entry["State"] =entry['Value']['state']
                    del entry["Value"]['state']
                    entry["Value"] =''
                elif 'value' in entry["Value"]:
                    del entry["Value"]["value"]

                self.data.append(entry)

    def clear(self):
        self.data.clear()

class SIPMSGDataProcessor:
    def __init__(self):
        # self.filename = filename
        self.data = []
        self.pattern1 = re.compile(r'\[([<>\-]+)\] SIP/(\d+\.\d+)(.*?) \[CSeq: (\d+) (.*?)\]')
        self.pattern2 = re.compile(r'\[([<>\-]+)\] (.*?)(?: (.*?))SIP/(\d+\.\d+) \[CSeq: (\d+) (.*?)\]')

    def extract_info(self, line):
        match1 = self.pattern1.search(line)
        match2 = self.pattern2.search(line)
        if match1:
            arrow, sip_v, message, cseq, method = match1.groups()
            direction = "Network to UE" if arrow == "<--" else "UE to Network"
            info = "" 
        elif match2:
            arrow, message, info, sip_v, cseq, method = match2.groups()
            direction = "Network to UE" if arrow == "<--" else "UE to Network"

        else:
            return

        timestamp_match = re.search(r'^(\d+-\d+ \d+:\d+:\d+\.\d+)', line)


        entry = {
            # "Filename": self.filename,
            "Timestamp": timestamp_match.group(1),
            "Type": "SIPMSG",
            # "Direction": direction,
            "Event": direction,
            "State": first_value ,
            # "Message": message,
            "Sub-Event": message,
            # "Info": info,
            "Value": info,
            "SIP_v": sip_v,
            "CSEQ": int(cseq),
            "Method": method
        }

        self.data.append(entry)

    def clear(self):
        self.data.clear()

class SmsServiceModuleDataProcessor:
    def __init__(self):
        # self.filename = filename
        self.data = []

        self.patterns = [
            (r'SmsServiceModule: sendSMSOverIMS: \[OUTGOING\] state (?P<State>\w+) contentType \[(?P<contentType>[^\]]+)\] messageID \[(?P<messageID>\d+)\] rpRef \[(?P<rpRef>\d+)\] smscAddr \[(?P<smscAddr>[^\]]+)\] regId \[(?P<regId>\d+)\]', ['State', 'contentType', 'messageID', 'rpRef', 'smscAddr', 'regId']),
            (r'SmsServiceModule: onReceive3GPPSmsAck: \[OUTGOING\] state (?P<State>\w+) contentType \[(?P<contentType>[^\]]+)\] messageID \[(?P<messageID>\d+)\] rpRef \[(?P<rpRef>\d+)\] reasonCode \[(?P<reasonCode>\d+)\] callID \[(?P<callID>[^\]]+)\] smscAddr \[(?P<smscAddr>[^\]]+)\] regId \[(?P<regId>\d+)\]', ['State', 'contentType', 'messageID', 'rpRef', 'reasonCode', 'callID', 'smscAddr', 'regId']),
            (r'SmsServiceModule: onReceive3GPPIncomingSms: \[INCOMING\] state (?P<State>\w+) contentType \[(?P<contentType>[^\]]+)\] messageID \[(?P<messageID>\d+)\] rpRef \[(?P<rpRef>\d+)\] callID \[(?P<callID>[^\]]+)\] smscAddr \[(?P<smscAddr>[^\]]+)\]', ['State', 'contentType', 'messageID', 'rpRef', 'callID', 'smscAddr']),
        ]

    def extract_info(self, line):
        timestamp_match = re.search(r'^(\d+-\d+ \d+:\d+:\d+\.\d+)', line)
    
        for pattern, keys in self.patterns:
            # print(keys)
            match = re.search(pattern, line)
            if match:
                tag_match = re.search(r'SmsServiceModule: (.*?):', line)
                if tag_match:
                    tag = tag_match.group(0)
                    # print(tag)
                    event, subevent = tag.split(': ')

                entry={
            "Timestamp": timestamp_match.group(0),
            "Type": "SmsServiceModule",
            "Event": event,
            "Method": tag,
            "Sub-Event": subevent
            }
                for key in keys:
                    value=match.group(key)
                    if value is not None:
                        if key =="messageID":
                            entry["Call ID"] = value
                        elif key =="reasonCode":
                            entry["Imsreason"]= value
                        elif key=="callID":
                            entry["Value"]= value
                        else:
                            entry[key]=value
                    else:
                        entry[key]=''      
   
                # entry= {key: match.group(key) for key in keys}
                # entry["Timestamp"] = timestamp_match.group(0)
                # entry["Type"] = "SmsServiceModule"
                self.data.append(entry)

    def clear(self):
        self.data.clear()

class ResipSmsHandlerDataProcessor:
    def __init__(self):
        # self.filename = filename
        self.data = []
       
        self.patterns = [
            (r'ResipSmsHandler: onSendSmsResponse: statusCode (?P<statusCode>\d+) callId (?P<callId>[^ ]+)', ['statusCode', 'callId']),
            (r'ResipSmsHandler: onSmsRpAckReceived: callId (?P<callId>[^ ]+) \d contentType (?P<contentType>[^\n]+)', ['callId', 'contentType']),
            (r'ResipSmsHandler: onNewIncomingSms: handle (?P<handle>\d+) callId (?P<callId>[^ ]+) contentType (?P<contentType>[^\n]+)', ['handle','callId', 'contentType']),
            (r'ResipSmsHandler: sendSMSResponse\(\): \[Call-ID\] (?P<callId>[^ ]+) \[Status\] (?P<status>\d+)', ['callId', 'status']),
            # (r'ResipSmsHandler: onSendSmsResponse: statusCode (?P<statusCode>\d+) callId (?P<callId>[^ ]+)', ['statusCode', 'callId'])
        ]

    def extract_info(self, line):
        timestamp_match = re.search(r'^(\d+-\d+ \d+:\d+:\d+\.\d+)', line)
        for pattern, keys in self.patterns:
            # print(keys)
            match = re.search(pattern, line)
            if match:
                tag_match = re.search(r'ResipSmsHandler: (.*?):', line)
                if tag_match:
                    tag = tag_match.group(0)
                    event, subevent = tag.split(': ')

                entry={
            "Timestamp": timestamp_match.group(0),
            "Type": "ResipSmsHandler",
            "Event": event,
            "Method": tag,
            "Sub-Event": subevent

            }
                for key in keys:
                    value=match.group(key)
                    if value is not None:
                        if key=="callID":
                            entry["Value"]= value
                        elif key =="statusCode":
                            entry["State"]= value
                        elif key =="status":
                            entry["State"]= value 
                        else:
                            entry[key]=value
                    else:
                        entry[key]='' 
            # match = re.search(pattern, line)
            # if match:
            #     entry = {key: match.group(key) for key in keys}

                self.data.append(entry)

    def clear(self):
        self.data.clear()



class ImsSmsDispatcherDataProcessor:

    def __init__(self):
        # self.filename = filename
        self.data = []
        self.patterns = [
            (r'ImsSmsDispatcher: DomainSelector : domain = (?P<domain>[^\n ]+)', ['domain']),
            (r'ImsSmsDispatcher: onSendSmsResult: token =(?P<token>\d+) messageRef =(?P<messageRef>\d+) reason =(?P<Reason>\d+) PhoneId : \[(?P<PhoneId>\d+)\]', ['token', 'messageRef', 'Reason', 'PhoneId']),
            (r'ImsSmsDispatcher: IncomingSms: - IMS Deliver  format =(?P<format>[^ ]+) token =(?P<token>\d+) PhoneId : \[(?P<PhoneId>\d+)\]', ['format', 'token', 'PhoneId']),
            (r'ImsSmsDispatcher: message class = (?P<message_class>[^\n ]+)', ['message_class']),
            (r'ImsSmsDispatcher \[\d+]: onImsDisconnected imsReasonInfo=(?P<Imsreason>.+)', ['Imsreason']),

        ]

    def extract_info(self, line):
        # print(line)
        timestamp_match = re.search(r'^(\d+-\d+ \d+:\d+:\d+\.\d+)', line)
        for pattern, keys in self.patterns:
            match = re.search(pattern, line)
            if match:
                # print(line)
                if 'message class =' in line:
                    tag_match = re.search(r'ImsSmsDispatcher: (.*?) ', line)
                elif 'onImsDisconnected imsReasonInfo' in line:
                    tag_match = re.search(r'ImsSmsDispatcher \[\d+]: (.*?) ', line)
                else:
                    tag_match = re.search(r'ImsSmsDispatcher: (.*?):', line)
                # print(tag_match)
                if tag_match:
                    tag = tag_match.group(0)
                    # print(tag)
                    parts = tag.split(': ')
                    # event, subevent = tag.split(': ')
                entry={
            "Timestamp": timestamp_match.group(0),
            "Type": "ImsSmsDispatcher",
            "Event": parts[0],
            "Tag": tag,
            "Sub-Event": parts[1]

            }
                for key in keys:
                    value=match.group(key)
                    if value is not None:
                        entry[key]=value
                    else:
                        entry[key]='' 
 
                self.data.append(entry)

    def clear(self):
        self.data.clear()

class SmsMessageProcessor:
    def __init__(self):
        # self.filename = filename
        self.data = []

        self.patterns = [
            (r'SmsMessage: mno = (?P<mno>[^\n ]+)', ['mno']),
            (r'CS/SmsMessageSent: send result = (?P<sendResult>[^ ]+), errorClass = (?P<errorClass>\d+), errorCode = (?P<errorCode>\d+)', ['sendResult', 'errorClass', 'errorCode']),
        ]

    def extract_info(self, line):
        # print(line)
        timestamp_match = re.search(r'^(\d+-\d+ \d+:\d+:\d+\.\d+)', line)

        for pattern, keys in self.patterns:
            match = re.search(pattern, line)
            if match:
                if 'SmsMessage: mno = ' in line:
                    tag = 'SmsMessage'
                elif 'CS/SmsMessageSent: send result =' in line:
                    tag = 'CS/SmsMessageSent'
                # print(line)
                entry = {
                    "Timestamp": timestamp_match.group(0),
                    "Method": tag
 
                }

                for key in keys:
                    value=match.group(key)
                    if value is not None:
                        entry[key]=value
                    else:
                        entry[key]='' 
 
                self.data.append(entry)

    def clear(self):
        self.data.clear()
 
class STFServiceDataProcessor:

    def __init__(self):
        # self.filename = filename
        self.data = []

        self.patterns = [
            (r'STFService: sendNetworkClass:  CellSignalNr:(?P<content>.+)', []),
            (r'STFService: Location: provider fused;(?P<content>.+)', []),
        ]

    def extract_info(self, line):
        timestamp_match = re.search(r'^(\d+-\d+ \d+:\d+:\d+\.\d+)', line)
        for pattern, _ in self.patterns:
            match = re.search(pattern, line)
            if match:
                tag=pattern.split("(")[0]
                parts = tag.split(': ')
                if "CellSignalNr" in pattern:
                    # key_value_pairs = re.findall(r'(\w+)=(\S+)', line)
                    key_value_pairs = re.findall(r'(\w+)=(\S+),', line)
                elif "Location" in pattern:
                    key_value_pairs = re.findall(r';(\w+) ([^;\n]+)', line)

                entry = {
                    "Timestamp": timestamp_match.group(0),
                    "Type": "STFService",
                    "Event": parts[0],
                    "Method": tag,
                    "Sub-Event": parts[2]
                }
                # serving_plmn=[]
                for key, value in key_value_pairs:
                    # entry[key] = value
                    if value is not None:
                        if key =="level":
                            entry["sim_state"] = value
                        elif key =="nrArfcn":
                            entry["NR_ARFCN"]= value
                        elif key=="rsrp":
                            entry["NR5G_RSRP"]= value
                        elif key =="bands":
                            entry["NR_BAND"]= value
                        elif key=="sinr":
                            entry["NR5G_SINR"]= value
                        elif key =="pci":
                            entry["NR_PCI"]= value
                        elif key =="mcc":
                            entry["mcc"] = value
                        elif key == "mnc":
                            entry["mnc"] = value
                        elif key =="alphaLong":
                            entry["Alpha Tag"] = value
                        else:
                            entry[key]=value
                    else:
                        entry[key]=''   

                    if 'mcc' in entry and 'mnc' in entry:
                        entry['Serving PLMN'] = entry['mcc'] + '-' + entry['mnc']
                        # print(entry['Serving PLMN'])
                    
                self.data.append(entry)

    def clear(self):
        self.data.clear()



class ImsPhoneCallProcessor:

    def __init__(self):
        # self.filename = filename
        self.data = []

        self.patterns = [
            (r'ImsPhoneCallTracker: \[\d+] onCallTerminated reasonCode=(?P<Reason>\d+)', ['Reason']),
            (r'ImsPhoneCallTracker: \[\d+] maybeRemapReasonCode : fromCode = (?P<fromCode>\d+) ; (?: message = (?P<message>[^ ]+))?', ['fromCode', 'message']),
            (r'ImsPhoneCallTracker: \[\d+] updatePhoneState pendingMo = (?P<pendingMo>[^,]+), rng= (?P<rng>[^,]+), fg= (?P<fg>[^,]+), bg= (?P<bg>[^\n ]+)', ['pendingMo', 'rng', 'fg', 'bg']),
            (r'ImsPhoneCallTracker: \[\d+] updatePhoneState oldState=(?P<oldState>[^,]+), newState=(?P<newState>[^\n ]+)', ['oldState', 'newState']),            
            (r'ImsPhoneCallTracker: shouldProcessCall: number: \[(?P<number>[^ ]+)\], result: (?P<result>\d+)', ['number', 'result']),
            # (r'ImsPhoneCallTracker: \[0\] onCallTerminated reasonCode=(?P<Reason>\d+)', ['Reason']),
            (r'ImsPhoneCallTracker: \[\d+] processCallStateChange state=(?P<State>[^ ]+) cause=(?P<cause>\d+) ignoreState=(?P<ignoreState>[^\n ]+)', ['State', 'cause', 'ignoreState']),
            (r'ImsPhoneCall: maybeChangeRingbackState: state=(?P<State>[^\n ]+)', ['State']),
            (r'ImsPhoneCall: isLocalTone: audioDirection=(?P<audioDirection>\d+), playRingback=(?P<playRingback>[^\n ]+)', ['audioDirection', 'playRingback']),

        ]

    def extract_info(self, line):
        # print(line)
        timestamp_match = re.search(r'^(\d+-\d+ \d+:\d+:\d+\.\d+)', line)

        for pattern, keys in self.patterns:
            match = re.search(pattern, line)
            if match:
                # print(line)
                if 'ImsPhoneCall:' in line:
                    tag_match = re.search(r'ImsPhoneCall: (.*?):', line)
                    if tag_match:
                        tag = tag_match.group(0)
                        event, subevent = tag.split(': ')
                        type = "ImsPhoneCall"

                elif "ImsPhoneCallTracker: shouldProcessCall:" in line:
                    tag_match = re.search(r'ImsPhoneCallTracker: (.*?):', line)
                    if tag_match:
                        tag = tag_match.group(0)
                        # print(tag)
                        event, subevent = tag.split(': ')
                        type = "ImsPhoneCallTracker"
                else:
                    tag_match = re.search(r'ImsPhoneCallTracker: \[\d+] (.*?) ', line)
                    if tag_match:
                        tag = tag_match.group(0)
                        event, subevent = tag.split('[0] ')
                        type = "ImsPhoneCallTracker"

                entry = {
                    "Timestamp": timestamp_match.group(0),
                    "Type": type,
                    "Event": event,
                    "Method": tag,
                    "Sub-Event": subevent
                }

                ims_reasom=[]
                for key in keys:
                    value = match.group(key)
                    if value is not None:
                        entry[key] = value
                        if key in ['fromCode', 'message']:
                            ims_reasom.append(value)
                    else:
                        entry[key] = ''
                    if ims_reasom:
                        if 'message' == None:
                            entry[ims_reasom]= ''.join(ims_reasom)
                        else:
                            entry['Imsreason']=', '.join(ims_reasom)
                self.data.append(entry)

    def clear(self):
        self.data.clear()

class MobileSignalControllerProcessor:
    def __init__(self):
        self.data = []
        self.pattern = r'NetworkController\.MobileSignalController\(1\): \\tto: (.*)'

    def extract_info(self, line):
        timestamp_match = re.search(r'^(\d+-\d+ \d+:\d+:\d+\.\d+)', line)
        match = re.search(self.pattern, line)
        if match:
            tag = "NetworkController.MobileSignalController(1): \tto:"
            content = match.group(1)
            parts = tag.split(':')
            content = content.replace(',', '').replace('}', '')
            key_value_pairs = re.findall(r'(\w+)=(\S+)', content)
            entry = {
                "Timestamp": timestamp_match.group(0),
                "Type": "NetworkController",
                "Event": parts[0],
                "Method": tag,
                "Sub-Event": parts[1]
            }
            for key, value in key_value_pairs:
                if key in ["network", "override"]:
                    entry[key] = value
            self.data.append(entry)

    def clear(self):
        self.data.clear()

class GsmConnectionProcessor:
    def __init__(self):
        self.data = []
        self.patterns = [
            (r'Telephony: GsmConnection: onStateChanged, state: (?P<State>\w+)', ['State']),
            (r'Telephony: GsmConnection: setCallRadioTech: (?P<setCallRadioTech>\w+)', ['setCallRadioTech']),
            (r'Telephony: GsmConnection: setAudioQuality, audioQuality : (?P<audioQuality>\d+)', ['audioQuality']),
            (r'Telephony: GsmConnection: refreshCodec: codec changed; (?P<codecChanged>.+)', ['codecChanged']),
            (r'Telephony: GsmConnection: updateState : state=(?P<State>\w+)', ['State']),
            (r'Telephony: GsmConnection: Update state (?P<State>.+)', ['State']),
        ]

    def extract_info(self, line):
        # print(line)
        timestamp_match = re.search(r'^(\d+-\d+ \d+:\d+:\d+\.\d+)', line)
        for pattern, keys in self.patterns:
            match = re.search(pattern, line)
            if match:
                if 'onStateChanged,' in line or 'setAudioQuality,' in line:
                    tag_match = re.search(r'Telephony: GsmConnection: (.*?),', line)
                elif 'updateState :' in line:
                    tag_match = re.search(r'Telephony: GsmConnection: (.*?) ', line)
                elif 'Update state' in line:
                    tag_match = re.search(r'Telephony: GsmConnection: (.*?) (.*?) ', line)
                else:
                    tag_match = re.search(r'Telephony: GsmConnection: (.*?):', line)
                if tag_match:
                    tag = tag_match.group(0)
                    parts = tag.split(':')
                    event = parts[1]
                    subevent = parts[2]
                entry = {
                    "Timestamp": timestamp_match.group(0),
                    "Type": "Telephony",
                    "Event": event,
                    "Method": tag,
                    "Sub-Event": subevent
                }
                for key in keys:
                    value = match.group(key)
                    if value is not None:
                        entry[key] = value
                    else:
                        entry[key] = ''
                self.data.append(entry)

    def clear(self):
        self.data.clear()


class GeneralProcessor:
    def __init__(self,tcList= None,info=None, mongodb_url= None, db_name= None, collection_name= None):
        self.common_keys = [
            "Timestamp", "Type", "Event", "Method", "Sub-Event", "Value", "State", "cause",
            "audioDirection", "playRingback", "pendingMo", "rng", "fg", "bg", "oldState", "newState",
            "number", "result", "HPLMN", "sim_state", "Serving PLMN", "Roaming", "NW sel mode", "Service",
            "MM5G", "NR5G_RSRP", "NR5G_SINR", "NR5G_RSRQ", "NR_RRC", "NR_SSB_Index",
            "NR_ARFCN", "NR_PCI", "NR_BAND", "NR_DL Scheduling", "NR_BLER", "NR_BW",
            "NR_SA_RLF Count", "NR_Tx Phy Channel Type", "NR_Tx Pwr", "NR_CDRX", "NETWORK", "FINAL IMEI Certi",
            "Call ID", "SIP_v", "CSEQ", "Reason", "Imsreason", "handle", "contentType",
            "domain", "format", "token", "PhoneId", "messageRef", "message_class",
            "mno", "sendResult", "errorClass", "errorCode",
            "Alpha Tag", "asulevel", "csiCqiTableIndex", "parametersUseForLevel", "csiCqiReport",
            "rsrp", "csiRsrp", "mAdditionalPlmns", "csiRsrq", "sinr", "nci", "rsrq",
            "tac", "latitude", "longitude", "network", "override", "codecChanged", "setCallRadioTech", "audioQuality"
        ]

        self.modemservice_processor = kpi_adb_automation()
        self.telecom_processor = TelecomDataProcessor()
        self.sipmsg_processor = SIPMSGDataProcessor()
        self.sms_service_processor= SmsServiceModuleDataProcessor()
        self.resip_sms_processor = ResipSmsHandlerDataProcessor()
        self.ims_smsdispatcher_processor = ImsSmsDispatcherDataProcessor()
        self.sms_message_processor = SmsMessageProcessor()
        self.stf_service_processor = STFServiceDataProcessor()
        self.ims_phonecall_processor = ImsPhoneCallProcessor()
        self.gsm_processor = GsmConnectionProcessor()
        self.network_processor = MobileSignalControllerProcessor()
        self.mongodb_url = mongodb_url
        self.db_name = db_name
        self.collection_name = collection_name

        self.combined_data = []
        if tcList is not None:
            self.itms_content, self.itms_path = get_iTMS(tcList, info)

        # self.itms_content = get_iTMS(tcList, info)
        # for filecontent, filepath in self.itms_content:
        #     self.logcat_process_itms(filecontent)

        


    def aggregate_output_data(self, filename=None):
        if filename: 
            property_timestamp = os.path.getctime(filename)
            creation_date = datetime.datetime.fromtimestamp(property_timestamp)
            timestamp_year = creation_date.strftime("%Y-")
        else: 
            timestamp_year = str(datetime.date.today().year) + '-'
            # timestamp_date = datetime.date.today()
            # timestamp_year = timestamp_date.strftime("%Y-")

        for records in [self.modemservice_processor.group_data(), self.telecom_processor.data, self.sipmsg_processor.data, self.sms_service_processor.data, self.resip_sms_processor.data, self.ims_smsdispatcher_processor.data, self.sms_message_processor.data, self.stf_service_processor.data,self.ims_phonecall_processor.data,self.gsm_processor.data, self.network_processor.data]:
            for record in records:
                for key, value in record.items():
                    if key in self.common_keys:
                        if key == 'Timestamp':
                            # print(value)
                            # print(type(value))
                            timestamp = timestamp_year + str(value)
                            # print(timestamp)
                            # timestamp = timestamp_year
                            timestamp_obj = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                            # print(timestamp_obj)
                            record["Timestamp"] = timestamp_obj
                            # record["Timestamp"] = timestamp
                        elif value:
                            record[key] = value
                        else:
                            record[key] = ''
                additional_keys = [key for key in record if key not in ["Filename", "Timestamp", "Type"]]
                if additional_keys:
                    self.combined_data.append(record)
    
    def process_line(self, line):
        if "ModemServiceMode" in line:
            self.modemservice_processor.ModemServiceMode(line)
        elif "Telecom" in line:
            self.telecom_processor.extract_info(line)
        elif "SIPMSG" in line:
            self.sipmsg_processor.extract_info(line)
        elif "SmsServiceModule" in line:
            self.sms_service_processor.extract_info(line)
        elif "ResipSmsHandler" in line:
            self.resip_sms_processor.extract_info(line)
        elif "ImsSmsDispatcher" in line:
            self.ims_smsdispatcher_processor.extract_info(line)
        elif "SmsMessage: mno = " in line or "CS/SmsMessageSent:" in line:
            self.sms_message_processor.extract_info(line)
        elif "STFService" in line:
            self.stf_service_processor.extract_info(line)
        elif "ImsPhoneCall" in line:
            self.ims_phonecall_processor.extract_info(line)
        elif "Telephony: GsmConnection:" in line:
            self.gsm_processor.extract_info(line)
        elif "NetworkController.MobileSignalController(1): \tto:" in line:
            self.network_processor.extract_info(line)
        else:
            pass

    def logcat_process(self, logcat_line_arr: list[str]):
        for line in logcat_line_arr:
            self.process_line(line)

        self.aggregate_output_data()

        return self.combined_data
    
    def logcat_process_itms(self, contents, filename):
        for line in contents.split("\n"):
            line=line.rstrip()
            # print(line)
            self.process_line(line)

        self.aggregate_output_data()
        entry = {"Filename": filename}
        for record in self.combined_data:
            record = {key: value for key, value in record.items() if key in self.common_keys}
            record = {**entry, **record}
            self.send_data_to_mongodb(record)
        
        # return self.combined_data
    
    def filecloud_data_process(self, filedata, file_path):
        if '\\' in file_path:
            filename = file_path.split('\\')[-1]
        elif '/' in file_path:
            filename = file_path.split('/')[-1]
        else:
            filename = file_path
        # print(filename)
        for line in filedata.split("\n"):
            line = line.rstrip()
            # print(line)
            self.process_line(line)

        self.aggregate_output_data()
        entry = {"Filename": filename}
        for record in self.combined_data:
            record = {key: value for key, value in record.items() if key in self.common_keys}
            record = {**entry, **record}
            # print(record)
            self.send_data_to_mongodb(record)

        self.logcat_clear()
    
    def logcat_clear(self):
        self.modemservice_processor.clear()
        self.telecom_processor.clear()
        self.sipmsg_processor.clear()
        self.sms_service_processor.clear()
        self.resip_sms_processor.clear()
        self.ims_smsdispatcher_processor.clear()
        self.sms_message_processor.clear()
        self.stf_service_processor.clear()
        self.ims_phonecall_processor.clear()
        self.gsm_processor.clear()
        self.network_processor.clear()

        self.combined_data.clear()



    def merge_and_store_data(self, filename, project_name, project_id, test_case_name, tc_id, test_exec_id, iteration_id, device_type, id, current_iteration_number, mongodb_url, collection_name, db_name):
        self.common_values = {
            "PROJECT_NAME": project_name,
            "PROJECTID": project_id,
            "TEST_CASE_NAME": test_case_name,
            "TCID": tc_id,
            "TESTEXECID": test_exec_id,
            "ITERATIONID": iteration_id,
            "DeviceType": device_type,
            "ID": id,
            "CURRENT_ITERATION_NUMBER": current_iteration_number
        }

        with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                self.process_line(line)
        
        self.aggregate_output_data(filename)

        if '\\' in filename:
            final_filename = filename.split('\\')[-1]
        elif '/' in filename:
            final_filename = filename.split('/')[-1]
        else:
            final_filename = filename

        self.common_values["Filename"] = final_filename

        self.mongodb_url = mongodb_url
        self.db_name = db_name
        self.collection_name = collection_name
        
        # client = pymongo.MongoClient(mongodb_url)
        # db = client[db_name]
        # collection = db[collection_name]

        for record in self.combined_data:
            record = {key: value for key, value in record.items() if key in self.common_keys}
            record = {**self.common_values, **record}
            self.send_data_to_mongodb(record)
            # print(record)
            # print("")
            # collection.insert_one(record)

    def read_itms_content(self):
    # self.itms_content = get_iTMS(tcList, info)
        for i in range(len(self.itms_content)):
            filename = self.itms_path[i]
            self.logcat_process_itms(self.itms_content[i], filename)
            self.logcat_clear()
            # print(self.itms_content[i])
            # print(self.itms_path[i])
            # print(i)
            # filename = self.itms_path[i]
            # entry = {"Filename": filename}
            # self.final_record(entry)

    # def final_record(self,entry):
    #     for record in self.combined_data:
    #         record = {key: value for key, value in record.items() if key in self.common_keys}
    #         record = {**entry, **record}
    #         self.send_data_to_mongodb(record)
    #         print(record)
    #         print("")
    
    def send_data_to_mongodb(self, record):
        client = pymongo.MongoClient(self.mongodb_url)
        db = client[self.db_name]
        collection = db[self.collection_name]
        collection.insert_one(record)

        # client = pymongo.MongoClient("mongodb://localhost:27017")
        # db = client["FILECLOUD"]
        # collection = db["filecloud_test_new"]
        # collection.insert_one(record)


def main(tcList, info):
    global env
    env = info['env'] 
    mongodb_url = 'mongodb://Shashwat:3GqogJWUX9GL3z@104.248.124.202:27017/'
    if env == 'Production':
        db_name = "TM_Google_Map"
        collection_name = "Telephony"
    elif env == "R&D":
        db_name = "Automation_Team_R&D"
        collection_name = "test_itms"

    general_processor = GeneralProcessor(tcList, info, mongodb_url, db_name, collection_name)
    general_processor.read_itms_content()


if __name__ == "__main__":
    filename = "C:/Users/SS00997234/Desktop/MyProjects/Dish Project/Logcats/Logcat-Basic_Tests-VoiceCall_Basic-1-DUT-R5CT92MKZEY--07262023032419.txt"
    project_name = 1
    project_id = 2
    test_case_name = 3
    tc_id = 4
    test_exec_id = 5
    iteration_id = 6
    device_type = 7
    id = 8
    current_iteration_number = 9
    mongodb_url = "mongodb://localhost:27017"
    db_name = "FILECLOUD"
    collection_name = "filecloud_DUT"

    
    # filename = sys.argv[1]
    # project_name = sys.argv[2]
    # project_id = sys.argv[3]
    # test_case_name = sys.argv[4]
    # tc_id = sys.argv[5]
    # test_exec_id = sys.argv[6]
    # iteration_id = sys.argv[7]
    # device_type = sys.argv[8]
    # id = sys.argv[9]
    # current_iteration_number = sys.argv[10]
    # mongodb_url = sys.argv[11]
    # collection_name = sys.argv[12]
    # db_name = sys.argv[13]

    # if "Automation" in db_name:
    #     db_name = "Automation_Team_R&D"
    general_processor = GeneralProcessor()
    # general_processor.read_itms_content()
    # get_iTMS(tcList, info)
    general_processor.merge_and_store_data(filename, project_name, project_id, test_case_name, tc_id, test_exec_id, iteration_id, device_type, id, current_iteration_number, mongodb_url, collection_name, db_name)
