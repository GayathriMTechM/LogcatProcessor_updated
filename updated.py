import pymongo
import datetime 
import re
import sys 
import json
import os 

first_value=''


class kpi_adb_automation:
    def __init__(self, filename):
        self.filename = filename
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
        response = {"Filename": self.filename, "Type": "ModemServiceMode"}

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
                # x=x.strip()
                key=key.strip()
                value=value.strip()
                response[key]= value

        return response


    def read_file(self):
        current_time = None
        current_type = None
        with open(self.filename, 'r',encoding='utf-8',errors='ignore') as file:
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
            record = {"Filename": self.filename, "Timestamp": timestamp, "Type": data_type}
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

class TelecomDataProcessor:
    def __init__(self, filename):
        self.filename = filename
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

                entry = {"Filename": self.filename,"Timestamp": timestamp, "Type": "Telecom", "Call ID": self.event_id, "Event": event, "Method": tag,"Sub-Event":subevent }


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

    def read_file(self):
        with open(self.filename, 'r',encoding='utf-8',errors='ignore') as file:
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
            "Filename": self.filename,
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

    def read_file(self):
        with open(self.filename, 'r',encoding='utf-8',errors='ignore') as file:
            for line in file:
                if "SIPMSG" in line:
                    self.extract_info(line)

class SmsServiceModuleDataProcessor:
    def __init__(self, filename):
        self.filename = filename
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

    def read_file(self):
        with open(self.filename, 'r',encoding='utf-8',errors='ignore') as file:
            for line in file:
                if "SmsServiceModule" in line:
                    self.extract_info(line)

class ResipSmsHandlerDataProcessor:
    def __init__(self, filename):
        self.filename = filename
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

    def read_file(self):
        with open(self.filename, 'r',encoding='utf-8',errors='ignore') as file:
            for line in file:
                if "ResipSmsHandler" in line:
                    self.extract_info(line)

class ImsSmsDispatcherDataProcessor:

    def __init__(self, filename):
        self.filename = filename
        self.data = []
        self.patterns = [
            (r'ImsSmsDispatcher: DomainSelector : domain = (?P<domain>[^\n ]+)', ['domain']),
            (r'ImsSmsDispatcher: onSendSmsResult: token =(?P<token>\d+) messageRef =(?P<messageRef>\d+) reason =(?P<Reason>\d+) PhoneId : \[(?P<PhoneId>\d+)\]', ['token', 'messageRef', 'Reason', 'PhoneId']),
            (r'ImsSmsDispatcher: IncomingSms: - IMS Deliver  format =(?P<format>[^ ]+) token =(?P<token>\d+) PhoneId : \[(?P<PhoneId>\d+)\]', ['format', 'token', 'PhoneId']),
            (r'ImsSmsDispatcher: message class = (?P<message_class>[^\n ]+)', ['message_class']),
        ]

    def extract_info(self, line):
        # print(line)
        timestamp_match = re.search(r'^(\d+-\d+ \d+:\d+:\d+\.\d+)', line)
        for pattern, keys in self.patterns:
            match = re.search(pattern, line)
            if match:
                print(line)
                if 'message class =' in line:
                    tag_match = re.search(r'ImsSmsDispatcher: (.*?)=', line)
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

    def read_file(self):
        with open(self.filename, 'r', encoding='utf-8') as file:
            for line in file:
                if "ImsSmsDispatcher:" in line:
                    self.extract_info(line)


class STFServiceDataProcessor:

    def __init__(self, filename):
        self.filename = filename
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

    def read_file(self):
        with open(self.filename, 'r',encoding='utf-8',errors='ignore') as file:
            for line in file:
                if "STFService" in line:
                    self.extract_info(line)


class ImsPhoneCallProcessor:

    def __init__(self, filename):
        self.filename = filename
        self.data = []

        self.patterns = [
            (r'ImsPhoneCallTracker: \[\d+] onCallTerminated reasonCode=(?P<Reason>\d+)', ['Reason']),
            (r'ImsPhoneCallTracker: \[\d+] maybeRemapReasonCode : fromCode = (?P<fromCode>\d+) ; (?: message = (?P<message>[^ ]+))?', ['fromCode', 'message']),
            # (r'ImsPhoneCallTracker: \[0\] onCallTerminated reasonCode=(?P<Reason>\d+)', ['Reason']),
            (r'ImsPhoneCallTracker: \[\d+] processCallStateChange state=(?P<State>[^ ]+) cause=(?P<cause>\d+) ignoreState=(?P<ignoreState>[^\n ]+)', ['State', 'cause', 'ignoreState']),
            (r'ImsPhoneCall: maybeChangeRingbackState: state=(?P<State>[^\n ]+)', ['State']),
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
                    # if ims_reasom and 'message' is None:
                    #     entry['Imsreason']=''.join(ims_reasom)
                    # elif ims_reasom and 'message' is not None:
                    #     entry['Imsreason']=', '.join(ims_reasom)
                self.data.append(entry)

    def read_file(self):
        with open(self.filename, 'r',encoding='utf-8',errors='ignore') as file:
            for line in file:
                # if "ImsPhoneCallTracker" in line:
                #     self.extract_info(line)
                if "ImsPhoneCall" in line:
                    self.extract_info(line)

class MobileSignalControllerProcessor:
    def __init__(self, filename):
        self.filename = filename
        self.data = []
        self.pattern= r'NetworkController\.MobileSignalController\(1\): \\tto: (.*)'

    def extract_info(self, line):
        timestamp_match = re.search(r'^(\d+-\d+ \d+:\d+:\d+\.\d+)', line)
        match = re.search(self.pattern, line)
        if match:
            tag="NetworkController.MobileSignalController(1): \tto:"
            content = match.group(1)
            parts =tag.split(':')
            content = content.replace(',', '').replace('}', '')
            key_value_pairs = re.findall(r'(\w+)=(\S+)',content)
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


    def read_file(self):
        with open(self.filename, 'r', encoding='utf-8',errors='ignore') as file:
            for line in file:
                if "NetworkController.MobileSignalController(1):" in line:
                    self.extract_info(line)


def merge_and_store_data(filename, project_name, project_id, test_case_name, tc_id, test_exec_id, iteration_id, device_type, id, current_iteration_number, mongodb_url, collection_name, db_name):
    common_keys = [
        "Timestamp", "Type", "Event", "Method", "Sub-Event", "Value", "State", "cause",
        "HPLMN", "sim_state", "Serving PLMN", "Roaming", "NW sel mode", "Service",
        "MM5G", "NR5G_RSRP", "NR5G_SINR", "NR5G_RSRQ", "NR_RRC", "NR_SSB_Index",
        "NR_ARFCN", "NR_PCI", "NR_BAND", "NR_DL Scheduling", "NR_BLER", "NR_BW",
        "NR_SA_RLF Count", "NR_Tx Phy Channel Type", "NR_Tx Pwr", "NR_CDRX", "NETWORK","FINAL IMEI Certi",
        "Call ID", "SIP_v", "CSEQ", "Reason", "Imsreason", "handle", "contentType",
        "domain", "format", "token", "PhoneId", "messageRef", "message_class"
        "Alpha Tag",  "asulevel", "csiCqiTableIndex", "parametersUseForLevel", "csiCqiReport", 
        "rsrp", "csiRsrp", "mAdditionalPlmns", "csiRsrq", "sinr", "nci", "rsrq", 
        "tac","latitude", "longitude" ,"network", "override"
    ]

    combined_data = []
    property_timestamp = os.path.getctime(filename)
    creation_date = datetime.datetime.fromtimestamp(property_timestamp)
    timestamp_year = creation_date.strftime("%Y-")
    # print(timestamp_year)

    kpi_processor = kpi_adb_automation(filename)
    kpi_processor.read_file()
    kpi_records = kpi_processor.group_data()

    telecom_processor = TelecomDataProcessor(filename)
    telecom_processor.read_file()
    telecom_records = telecom_processor.data

    sipmsg_processor = SIPMSGDataProcessor(filename)
    sipmsg_processor.read_file()
    sipmsg_records = sipmsg_processor.data

    smsservicemodule_processor = SmsServiceModuleDataProcessor(filename)
    smsservicemodule_processor.read_file()
    smsservicemodule_records = smsservicemodule_processor.data

    resipsms_processor = ResipSmsHandlerDataProcessor(filename)
    resipsms_processor.read_file()
    resipsms_records = resipsms_processor.data

    imssmsdispatcher_processor = ImsSmsDispatcherDataProcessor(filename)
    imssmsdispatcher_processor.read_file()
    imssmsdispatcher_records = imssmsdispatcher_processor.data

    stpservice_processor = STFServiceDataProcessor(filename)
    stpservice_processor.read_file()
    stpservice_records= stpservice_processor.data


    imsphonecall_processor = ImsPhoneCallProcessor(filename)
    imsphonecall_processor.read_file()
    imsphonecall_records= imsphonecall_processor.data

    networkcontroller_processor = MobileSignalControllerProcessor(filename)
    networkcontroller_processor.read_file()
    networkcontroller_records= networkcontroller_processor.data


    for records in [kpi_records, telecom_records, sipmsg_records, smsservicemodule_records, resipsms_records, imssmsdispatcher_records, stpservice_records, imsphonecall_records, networkcontroller_records]:
            for record in records:
                # combined_record = {key: "" for key in common_keys}
                # record = {key: "" for key in common_keys}
                for key, value in record.items():
                    if key in common_keys:
                        if key == 'Timestamp':
                            timestamp = timestamp_year + value
                            timestamp_obj = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                            # formatted_timestamp = timestamp_obj.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
                            # datetime_object = datetime.datetime.strptime(timestamp, '%m/%d/%y %H:%M:%S')
                            # print(datetime_object)
                            record["Timestamp"] = timestamp_obj
                            # print(record["Timestamp"])
                        elif value:
                            record[key] = value
                        else: 
                            record[key]=''
                additional_keys = [key for key in record if key not in ["Filename", "Timestamp", "Type"]]
                if additional_keys:
                    combined_data.append(record)
                    # print(combined_data)


    if '\\' in filename:
        final_filename = filename.split('\\')[-1]
    elif '/' in filename:
        final_filename= filename.split('/')[-1]
    else:
        final_filename = filename

    common_values = {
        "Filename": final_filename,
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
        record= {key: value for key, value in record.items() if key in common_keys}
        record={**common_values, **record}
        print(record)
        print("")
        #print("new code 11_06")
        # collection.insert_one(record)

if __name__ == "__main__":
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


    merge_and_store_data(filename, project_name, project_id, test_case_name, tc_id, test_exec_id, iteration_id, device_type, id, current_iteration_number, mongodb_url, collection_name,db_name)

