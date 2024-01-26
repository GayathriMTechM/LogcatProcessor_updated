import re
import json
import pymongo

 
class LogParser:
    def __init__(self, file_path):
        self.combined_data = []
        self.file_path = file_path

 

    def read_lines(self):
        with open(self.file_path, 'r') as file:
            return file.readlines()

 

    def parse_event_location(self, line):
        pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":{"latitude":(?P<Latitude>[-+]?\d*\.\d+|\d+),"longitude":(?P<Longitude>[-+]?\d*\.\d+|\d+),"provider":"(?P<GPS>.*?)","distance":(?P<GPS_DISTANCE>[-+]?\d*\.\d+|\d+),"speed":(?P<GPS_SPEED>[-+]?\d*\.\d+|\d+),"accuracy":(?P<Accuracy>[-+]?\d*\.\d+|\d+)(?:,"bearing":(?P<Bearing>[-+]?\d*\.\d+|\d+))?}'
        match = re.search(pattern, line)
        if match:
            data = match.groupdict()
            if 'Bearing' in data and data['Bearing'] is None:
                del data['Bearing']
            self.combined_data.append(data)

 

    def parse_event_Cell_Info_CellSignalNR(self, line):
        # print(line)
        pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":{"class_name":"(?P<class_name>.*?)","alphaLong":"(?P<alphaLong>.*?)","mnc":"(?P<MNC>.*?)","nrArfcn":"(?P<NrArfcn>.*?)","level":"(?P<Level>.*?)","asulevel":"(?P<AsuLevel>.*?)","csiCqiTableIndex":"(?P<CsiCqiTableIndex>.*?)","parametersUseForLevel":"(?P<ParametersUseForLevel>.*?)","csiCqiReport":"(?P<CsiCqiReport>.*?)","rsrp":"(?P<Rsrp>.*?)","mcc":"(?P<MCC>.*?)","bands":"(?P<Bands>.*?)","csiRsrp":"(?P<CsiRsrp>.*?)","mAdditionalPlmns":"(?P<MAdditionalPlmns>.*?)","csiRsrq":"(?P<CsiRsrq>.*?)","sinr":"(?P<Sinr>.*?)","network type":"(?P<NetworkType>.*?)","nci":"(?P<Nci>.*?)","rsrq":"(?P<Rsrq>.*?)","tac":"(?P<Tac>.*?)","pci":"(?P<Pci>.*?)","alphaShort":"(?P<alphaShort>.*?)"}'

        # pattern = r'{"timestamp":"(?P<Time>.*?)","event":"Primary Cell Info CellSignalNR","data":{"class_name":"Primary Cell Info CellSignalNR","alphaLong":"","mnc":"(?P<MNC>.*?)","nrArfcn":"(?P<NrArfcn>.*?)","level":"(?P<Level>.*?)","asulevel":"(?P<AsuLevel>.*?)","csiCqiTableIndex":"(?P<CsiCqiTableIndex>.*?)","parametersUseForLevel":"(?P<ParametersUseForLevel>.*?)","csiCqiReport":"(?P<CsiCqiReport>.*?)","rsrp":"(?P<Rsrp>.*?)","mcc":"(?P<MCC>.*?)","bands":"(?P<Bands>.*?)","csiRsrp":"(?P<CsiRsrp>.*?)","mAdditionalPlmns":"(?P<MAdditionalPlmns>.*?)","csiRsrq":"(?P<CsiRsrq>.*?)","sinr":"(?P<Sinr>.*?)","network type":"(?P<NetworkType>.*?)","nci":"(?P<Nci>.*?)","rsrq":"(?P<Rsrq>.*?)","tac":"(?P<Tac>.*?)","pci":"(?P<Pci>.*?)","alphaShort":""}'

        match = re.search(pattern, line)
        if match:
            keys_to_include = ['Time', 'Event', 'alphaLong', 'MNC', 'NrArfcn', 'Level', 'AsuLevel', 'ParametersUseForLevel','CsiCqiReport', 'Rsrp', 'MCC', 'Bands', 'MAdditionalPlmns', 'Sinr', 'NetworkType', 'Nci', 'Rsrq', 'Tac', 'Pci']

            # print(line)
            data = match.groupdict()
            filtered_data = {key: data[key] for key in keys_to_include if key in data}
            self.combined_data.append(filtered_data)

    def parse_event_Cell_Info_CellSignalLTE(self, line):
        pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":{"class_name":"(?P<class_name>.*?)","alphaLong":"(?P<alphaLong>.*?)","rssi":"(?P<Rssi>.*?)","mnc":"(?P<MNC>.*?)","level":"(?P<Level>.*?)","bandwidth":"(?P<Bandwidth>.*?)","ci":"(?P<Ci>.*?)","asulevel":"(?P<AsuLevel>.*?)","parametersUseForLevel":"(?P<ParametersUseForLevel>.*?)","rsrp":"(?P<Rsrp>.*?)","rssnr":"(?P<Rssnr>.*?)","bands":"(?P<Bands>.*?)","mcc":"(?P<MCC>.*?)","ta":"(?P<Ta>.*?)","mAdditionalPlmns":"(?P<MAdditionalPlmns>.*?)","sinr":"(?P<Sinr>.*?)","csgInfo":"(?P<CsgInfo>.*?)","network type":"(?P<NetworkType>.*?)","rsrq":"(?P<Rsrq>.*?)","pci":"(?P<Pci>.*?)","tac":"(?P<Tac>.*?)","alphaShort":"(?P<alphaShort>.*?)","cqi":"(?P<Cqi>.*?)","earfcn":"(?P<Earfcn>.*?)"}'
        keys_to_include = ['Time', 'Event', 'alphaLong', 'MNC', 'Level', 'Bands', 'MCC', 'Tac', 'Pci', 'Rssi', 'Bandwidth', 'Ci', 'AsuLevel', 'ParametersUseForLevel', 'Rsrp', 'Rssnr', 'Sinr', 'CsgInfo', 'NetworkType', 'Rsrq', 'Earfcn', 'Cqi']
        match = re.search(pattern, line)

        if match:
            data = match.groupdict()
            filtered_data = {key: data[key] for key in keys_to_include if key in data}
            self.combined_data.append(filtered_data)

 

    def parse_event_GetNetworkBandwidth(self, line):
        pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":{"Down Stream Bandwidth":"(?P<DownStreamBandwidth>.*?)","Upload Stream Bandwidth":"(?P<UploadStreamBandwidth>.*?)"}'
        keys_to_include = ['Time', 'Event', 'DownStreamBandwidth', 'UploadStreamBandwidth']
        match = re.search(pattern, line)
        if match:
            data = match.groupdict()
            filtered_data = {key: data[key] for key in keys_to_include if key in data}
            self.combined_data.append(filtered_data)

 

    def parse_event_Call_State(self, line):
        pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":{"CALL_STATE":[file://nonCallStateChanged:%20(%3fP%3cCallState%3e[%5e,]+),%20incomingNumber:%20(%3fP%3cIncomingNumber%3e[%5e]\\nonCallStateChanged: (?P<CallState>[^,]+), incomingNumber: (?P<IncomingNumber>[^]*)"}'
        # pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":{"CALL_STATE":"(?P<CallState>.*?)","incomingNumber":"(?P<IncomingNumber>.*?)"}'
        match = re.search(pattern, line)

        if match:
            data = match.groupdict()
            self.combined_data.append(data)

 

    def parse_event_GSM_Cell_Location(self, line):
        pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":{"Cell ID":"(?P<CellID>.*?)","Location Area Code":"(?P<LocationAreaCode>.*?)","Class name":"(?P<ClassName>.*?)","Primary Scrambling Code":"(?P<PrimaryScramblingCode>.*?)"}'

        match = re.search(pattern, line)

        if match:
            # keys_to_include = ['Time', 'Event', 'CellID', 'LocationAreaCode', 'ClassName', 'PrimaryScramblingCode']

            data = match.groupdict()

            # filtered_data = {key: data[key] for key in keys_to_include if key in data}
            self.combined_data.append(data)

 

    def parse_event_GET_SERVICE_STATE(self, line):
        pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":{"serviceState ChannelNumber":"(?P<ChannelNumber>.*?)","current voice service state":"(?P<VoiceServiceState>.*?)","serviceState Roaming ":"(?P<Roaming>.*?)","serviceState NetworkRegistrationInfoList":"(?P<NetworkRegistrationInfoList>.*?)","serviceState IsManualSelection ":"(?P<IsManualSelection>.*?)","serviceState cell bandwidths":"(?P<CellBandwidths>.*?)","serviceState DuplexMode ":"(?P<DuplexMode>.*?)"}'

 

        match = re.search(pattern, line)
        if match:
            keys_to_include = ['Time', 'Event', 'ChannelNumber', 'VoiceServiceState', 'Roaming', 'NetworkRegistrationInfoList', 'IsManualSelection', 'CellBandwidths', 'DuplexMode']
            data = match.groupdict()

            filtered_data = {key: data[key] for key in keys_to_include if key in data}
            self.combined_data.append(filtered_data)

 

    def parse_event_GET_DATA_CONNECTION_STATUS(self, line):
        pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":{"Data State":"(?P<DataState>.*?)"}'

        match = re.search(pattern, line)
        if match:
            data = match.groupdict()
            self.combined_data.append(data)

 

    def parse_event_GET_NETWORK_OPERATOR(self, line):

        pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":{"mnc":"(?P<MNC>.*?)","mcc":"(?P<MCC>.*?)"}'

        match = re.search(pattern, line)

        if match:
            data = match.groupdict()
            self.combined_data.append(data)

 

    def parse_event_GET_TELEPHONY_DISPLAY_INFO(self, line):
        pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":{"TelephonyDisplayInfo OverrideNetworkType":"(?P<OverrideNetworkType>.*?)","TelephonyDisplayInfo roaming":"(?P<Roaming>.*?)","TelephonyDisplayInfo NW Type":"(?P<NWType>.*?)"}'

        match = re.search(pattern, line)

        if match:
            data = match.groupdict()
            self.combined_data.append(data)

 

    def parse_event_GET_CALL_LOG_MESSAGES(self, line):
        pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":\[(?P<data>.*?)\]\}'

 

        match = re.search(pattern, line)
        if match:

            keys_to_include = ['Time', 'Event', 'CallLogMessages']
            data = match.groupdict()
            filtered_data = {key: data[key] for key in keys_to_include if key in data}
            self.combined_data.append(filtered_data)

 

    def parse_event_wifi(self, line):

        pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":{"ssid":"(?P<SSID>.*?)","rssi":(?P<RSSI>[-+]?\d+),"wifi_standard":"(?P<WiFiStandard>.*?)","frequency":(?P<Frequency>[-+]?\d+)}'

        match = re.search(pattern, line)

        if match:
            data = match.groupdict()
            self.combined_data.append(data)

 

    def parse_event_detection_5g(self, line):

        pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":{"downstream_bandwidth":(?P<DownstreamBandwidth>[-+]?\d+),"upstream_bandwidth":(?P<UpstreamBandwidth>[-+]?\d+),"detect_5g":(?P<Detect5g>true|false)}}'
        match = re.search(pattern, line)

        if match:
            data = match.groupdict()
            self.combined_data.append(data)

 

    def parse_event_EPDGInfo(self, line):
        pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":{"class_name":"(?P<ClassName>.*?)","ip_address_1":"(?P<IPAddress1>.*?)","dns_server_2":"(?P<DNSServer2>.*?)","dns_server_1":"(?P<DNSServer1>.*?)","max_downstream_bandwidth":"(?P<MaxDownstreamBandwidth>.*?)","is_secure":"(?P<IsSecure>true|false)","tunneling_protocol":"(?P<TunnelingProtocol>.*?)","max_upstream_bandwidth":"(?P<MaxUpstreamBandwidth>.*?)"}}'

 

        match = re.search(pattern, line)
        if match:
            data = match.groupdict()
            self.combined_data.append(data)

 

    def parse_event_GET_CALL_FORWARD_INDICATOR(self, line):

        pattern = r'{"timestamp":"(?P<Time>.*?)","event":"(?P<Event>.*?)","data":{"onCallForwardingIndicatorChanged ":"(?P<OnCallForwardingIndicatorChanged>true|false)"}}'

        match = re.search(pattern, line)
        if match:
            data = match.groupdict()
            self.combined_data.append(data)






    def process_events(self):
        lines = self.read_lines()

        for line in lines:
            if '"event":"EVENT_LOCATION"' in line:
                self.parse_event_location(line)

            elif '"event":"GET_NETWORK_BANDWIDTH"' in line:
                self.parse_event_GetNetworkBandwidth(line)

            elif '"event":"GET_CALL_STATE"' in line:
                self.parse_event_Call_State(line)

            elif '"event":"GET_GSM_CELL_LOCATION"' in line:
                self.parse_event_GSM_Cell_Location(line)

            elif '"event":"GET_SERVICE_STATE"' in line:
                self.parse_event_GET_SERVICE_STATE(line)

            elif '"event":"GET_DATA_CONNECTION_STATUS"' in line:
                self.parse_event_GET_DATA_CONNECTION_STATUS(line)

            elif '"event":"GET_NETWORK_OPEARTOR"' in line:
                self.parse_event_GET_NETWORK_OPERATOR(line)

            elif '"event":"GET_TELEPHONY_DISPLAY_INFO"' in line:
                self.parse_event_GET_TELEPHONY_DISPLAY_INFO(line)

            elif '"event":"GET_CALL_LOG_MESSAGES"' in line:
                self.parse_event_GET_CALL_LOG_MESSAGES(line)

            elif '"event":"wifi"' in line:
                self.parse_event_wifi(line)

            elif 'event":"detection_5g"' in line:
                self.parse_event_detection_5g(line)

            elif '"event":"EPDGInfo"' in line:
                self.parse_event_EPDGInfo(line)

            elif '"event":"GET_CALL_FORWARD_INDICATOR"' in line:
                self.parse_event_GET_CALL_FORWARD_INDICATOR(line)





    def send_data_to_mongodb(self):

        # client = pymongo.MongoClient("mongodb://Shashwat:3GqogJWUX9GL3z@104.248.124.202:27017/")

        # db = client["TMO_Field_R&D"]

        # collection = db["shashwat_combined_event_data"]

 

        client = pymongo.MongoClient("mongodb://localhost:27017")
        db = client["NEW_EVENT"]
        collection = db["event3_test"]

        for record in self.combined_data:
            print(record)
            collection.insert_one(record)

 

if __name__ == "__main__":

    log_parser = LogParser('eventfile2.txt')
    log_parser.process_events()
    log_parser.send_data_to_mongodb()
