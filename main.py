import pymongo
import datetime
import re
import sys

first_value=''

class kpi_adb_automation:
    def __init__(self, filename):
        self.filename = filename
        self.data = {}
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

        if not matches1:
            pattern2 = r'(\w+)\s*[:\(]\s*([^)]+?)\s*[)\:]'
            matches2 = re.findall(pattern2, line)
            for key, value in matches2:
                key = key.strip()
                value = value.strip()
                response[key] = value

        else:
            for x, key, value in matches1:
                # x=x.strip()
                key=key.strip()
                value=value.strip()
                response[key]= value

        return response

    def log_data(self):
        current_time = None
        current_type = None
        with open(self.filename, 'r', encoding='utf-8') as file:
            for line in file:
                if "ModemServiceMode" in line:
                    response = self.ModemServiceMode(line)
                    # print(response)
                    current_time = response.get("Timestamp")
                    current_type = response.get("Type", "ModemServiceMode")
                    self.data.setdefault((current_time, current_type), []).append(response)
            # print(self.data)

    def group_data(self):
        records = []
        for (timestamp, data_type), data_list in self.data.items():
            record = {"Timestamp": timestamp, "Type": data_type}
            for key in self.keys_to_search:
                for data in data_list:
                    if key in data and data[key] is not None:
                        record[key] = data[key]
            records.append(record)
        print(len(records))
        return records


    def format_time(self, timestamp):
        formatted_time = datetime.datetime.strptime(timestamp, "%d-%m %H:%M:%S.%f").strftime("%d-%m %H:%M:%S.%f")[:-4]
        return formatted_time

class TelecomDataProcessor:
    def __init__(self, filename):
        # self.lines= lines
        self.filename=filename
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
            line = line[len(timestamp):]
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

                entry = {"Timestamp": timestamp, "Type": "Telecom", "Call ID": self.event_id, "Event": event, "Tag": tag,"Sub-Event":subevent }


                value = {key: match.group(key) if key in match.groupdict() else None for key in keys}
                if "first_value" in keys and 'first_value' in match.groupdict():
                    global first_value
                    first_value = match.group('first_value').split(', ')[-2]
                    entry["Value"] = {'state': first_value}
                elif 'videoState' in keys and 'videoState' in match.groupdict():
                    video_state = match.group('videoState').split(' : ')[0]
                    entry["Value"] = {'videoState': video_state}
                # elif 'value' in keys and 'value' in match.groupdict():
                #     value_part = match.group('value').split(': ')[0]
                #     entry["Value"] = {'value': value_part}

                elif 'value' in keys and 'value' in match.groupdict():
                    value_part = match.group('value').split(': ')[0]
                    if "START_RINGER" in tag and value_part.lower() == 'null':
                        entry["Value"] = {'state': 'Start Ringing','value': 'null', }
                    elif "STOP_RINGER" in tag and value_part.lower()=='null':
                        entry["Value"] = {'state': 'Stop Ringing','value': 'null', }
                    elif "SET_RINGING" in tag:
                        entry["Value"]={'state': value_part}
                    elif "SET_DIALING" in tag:
                        entry["Value"]={'state': value_part}
                    else:
                        entry["Value"] = {'value': value_part}
                        
                else:
                    entry["Value"] = value
                
                if 'state' in entry["Value"]:
                    entry["State"] =entry['Value']['state']
                    del entry["Value"]['state']

                self.data.append(entry)

    def log_data(self):
        with open(self.filename, 'r', encoding='utf-8') as file:
            for line in file:
                if "Telecom" in line:
                    self.extract_info(line)

class SIPMSGDataProcessor:
    def __init__(self, filename):
        self.filename = filename
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
            "Timestamp": timestamp_match.group(1),
            "Type": "SIPMSG",
            "Direction": direction,
            "Call Type": first_value,
            "Message": message,
            "Info": info,
            "SIP_v": sip_v,
            "CSEQ": int(cseq),
            "Method": method
        }

        self.data.append(entry)

    def read_file(self):
        with open(self.filename, 'r', encoding='utf-8') as file:
            for line in file:
                if "SIPMSG" in line:
                    self.extract_info(line)


def merge_and_store_data(filename, project_name, project_id, test_case_name, tc_id, test_exec_id, iteration_id, device_type, id, current_iteration_number, mongodb_url, collection_name,db_name):

    # lines=filename.splitlines()
    combined_data = []

    kpi_processor = kpi_adb_automation(filename)
    kpi_processor.log_data()
    kpi_records = kpi_processor.group_data()
   
    telecom_processor = TelecomDataProcessor(filename)
    telecom_processor.log_data()
    telecom_records = telecom_processor.data

    sipmsg_processor = SIPMSGDataProcessor(filename)
    sipmsg_processor.read_file()
    sipmsg_records=sipmsg_processor.data

    for record in kpi_records:
        additional_keys = [key for key in record if key not in ["Timestamp", "Type"]]
        if additional_keys:
            combined_data.append(record)
            # print(record)
   
    for record in telecom_records:
        combined_data.append(record)
        # print(record)
    
    for record in sipmsg_records:
        combined_data.append(record)


    common_values = {
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


    client = pymongo.MongoClient(mongodb_url)
  
    db = client[db_name]
    collection = db[collection_name]
    for record in combined_data:
        record={**common_values, **record}
        # print(record)
        collection.insert_one(record)

if __name__ == "__main__":
    # filename = "Logcat-NewDishTests-DISH_To_DISH_VoiceCall-1-DUT-R5CT92SP5VN--10112023012539.txt" 
    # processor=merge_and_store_data(filename)
    # processor.send_to_mongodb()

    filename = sys.argv[1]
    project_name = sys.argv[2]
    project_id = sys.argv[3]
    test_case_name = sys.argv[4]
    tc_id = sys.argv[5]
    test_exec_id = sys.argv[6]
    iteration_id = sys.argv[7]
    device_type = sys.argv[8]
    id = sys.argv[9]
    current_iteration_number = sys.argv[10]
    mongodb_url = sys.argv[11]    
    collection_name = sys.argv[12]
    db_name = sys.argv[13]
    
    if "Automation" in db_name:
       db_name = "Automation_Team_R&D"
   


    merge_and_store_data(filename, project_name, project_id, test_case_name, tc_id, test_exec_id, iteration_id, device_type, id, current_iteration_number, mongodb_url,collection_name,db_name)