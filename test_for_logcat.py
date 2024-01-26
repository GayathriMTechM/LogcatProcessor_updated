import pymongo
import datetime 
import re
import sys 
import json
import os 

first_value=''

class kpi_adb_automation:
    def __init__(self):
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
    def __init__(self):
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


class SIPMSGDataProcessor:
    def __init__(self):
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

class SmsServiceModuleDataProcessor:
    def __init__(self):
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



class ResipSmsHandlerDataProcessor:
    def __init__(self):
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



class ImsSmsDispatcherDataProcessor:

    def __init__(self):
        self.filename = filename
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


class SmsMessageProcessor:
    def __init__(self):
        self.filename = filename
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

 
class STFServiceDataProcessor:

    def __init__(self):
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



class ImsPhoneCallProcessor:

    def __init__(self):
        self.filename = filename
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

def merge_and_store_data(filename, project_name, project_id, test_case_name, tc_id, test_exec_id, iteration_id, device_type, id, current_iteration_number, mongodb_url, collection_name, db_name):
    common_keys = [
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

    combined_data = []
    property_timestamp = os.path.getctime(filename)
    creation_date = datetime.datetime.fromtimestamp(property_timestamp)
    timestamp_year = creation_date.strftime("%Y-")

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

    modemservice_processor = kpi_adb_automation()
    telecom_processor = TelecomDataProcessor()
    sipmsg_processor = SIPMSGDataProcessor()
    sms_service_processor= SmsServiceModuleDataProcessor()
    resip_sms_processor = ResipSmsHandlerDataProcessor()
    ims_smsdispatcher_processor = ImsSmsDispatcherDataProcessor()
    sms_message_processor = SmsMessageProcessor()
    stf_service_processor = STFServiceDataProcessor()
    ims_phonecall_processor = ImsPhoneCallProcessor()
    gsm_processor = GsmConnectionProcessor()
    network_processor = MobileSignalControllerProcessor()


    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            if "ModemServiceMode" in line:
                modemservice_processor.ModemServiceMode(line)
            elif "Telecom" in line:
                # telecom_processor.extract_event_id(line)
                telecom_processor.extract_info(line)
            elif "SIPMSG" in line:
                sipmsg_processor.extract_info(line)
            elif "SmsServiceModule" in line:
                sms_service_processor.extract_info(line)
            elif "ResipSmsHandler" in line:
                resip_sms_processor.extract_info(line)
            elif "ImsSmsDispatcher" in line:
                ims_smsdispatcher_processor.extract_info(line)
            elif "SmsMessage: mno = " in line or "CS/SmsMessageSent:" in line:
                sms_message_processor.extract_info(line)
            elif "STFService" in line:
                stf_service_processor.extract_info(line)
            elif "ImsPhoneCall" in line:
                ims_phonecall_processor.extract_info(line)
            elif "Telephony: GsmConnection:" in line:
                gsm_processor.extract_info(line)
            elif "NetworkController.MobileSignalController(1): \tto:" in line:
                network_processor.extract_info(line)
            else:
                pass
            

    for records in [modemservice_processor.group_data(), telecom_processor.data, sipmsg_processor.data, sms_service_processor.data, resip_sms_processor.data, ims_smsdispatcher_processor.data, sms_message_processor.data, stf_service_processor.data,ims_phonecall_processor.data,gsm_processor.data, network_processor.data]:
        for record in records:
            for key, value in record.items():
                if key in common_keys:
                    if key == 'Timestamp':
                        # print(value)
                        timestamp = timestamp_year + str(value)
                        timestamp_obj = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                        record["Timestamp"] = timestamp_obj
                    elif value:
                        record[key] = value
                    else:
                        record[key] = ''
            additional_keys = [key for key in record if key not in ["Filename", "Timestamp", "Type"]]
            if additional_keys:
                combined_data.append(record)

    if '\\' in filename:
        final_filename = filename.split('\\')[-1]
    elif '/' in filename:
        final_filename = filename.split('/')[-1]
    else:
        final_filename = filename

    common_values["Filename"] = final_filename

    client = pymongo.MongoClient(mongodb_url)
    db = client[db_name]
    collection = db[collection_name]

    for record in combined_data:
        record = {key: value for key, value in record.items() if key in common_keys}
        record = {**common_values, **record}
        print(record)
        print("")
        # collection.insert_one(record)

if __name__ == "__main__":
    filename = "C:/Users/SS00997234/Desktop/MyProjects/Dish Project/Logcats/Logcat-Basic_Tests-VoiceCall_Basic-1-DUT-R5CT92WRW8D--10092023042528.txt"
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
    db_name = "ExecutionLogs_Dish_to_TMO"
    collection_name = "ModifiedCode__16_nov_3"


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


    merge_and_store_data(filename, project_name, project_id, test_case_name, tc_id, test_exec_id, iteration_id, device_type, id, current_iteration_number, mongodb_url, collection_name, db_name)
