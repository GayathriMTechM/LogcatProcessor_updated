import requests
import configparser
import json
import utils.itmsAuthentication as Authentication
from collections import defaultdict

config = configparser.ConfigParser()
config.read('Config/config.ini')


def get_test_case(tcId):
    # print('TC' + str(tcId) + ' details requested!')
    url = config['URL']['testcase'] + '/' + str(tcId)
    payload = {}
    headers = {
        'Authorization': Authentication.get_token()
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    testcase_details = json.loads(response.text)
    return testcase_details


def get_all_test_cases_details(projectId, folderId=0, includeSubfolders='true', includeArchived='false', startAt=0,
                               maxResults=500):
    # print('All TCs details from Project ID ' + str(projectId) + ' and folder ID ' + str(folderId) + ' requested!')
    url = config['URL']['testcase'] + '/ItemList?projectId=' + str(projectId) + '&folderId=' + str(folderId) + \
          '&includeSubfolders=' + includeSubfolders + '&includeArchived=' + includeArchived + '&startAt=' + str(
        startAt) + \
          '&maxResults=' + str(maxResults)
    payload = {}
    headers = {
        'Authorization': Authentication.get_token()
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    testcase_details = json.loads(response.text)
    return testcase_details


def create_test_case(payload):
    print('Request to create TC is received!')
    url = config['URL']['testcase']
    payload = {}
    headers = {
        'Authorization': Authentication.get_token()
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    testcase_details = json.loads(response.text)
    return testcase_details


def get_attachment_metadata_list(tcId):
    print('TC {} Attachment Metadata List requested!'.format(str(tcId)))
    url = config['URL']['testcase'] + '/' + str(tcId) + '/Attachment'
    payload = {}
    headers = {
        'Authorization': Authentication.get_token()
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    testcase_details = json.loads(response.text)
    return testcase_details


def get_test_case_history(tcId):
    print('TC {} History requested!'.format(str(tcId)))
    url = config['URL']['testcase'] + '/' + str(tcId) + '/History'
    payload = {}
    headers = {
        'Authorization': Authentication.get_token()
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    testcase_details = json.loads(response.text)
    return testcase_details


def get_folder(projectId, folderId=0, includePermissions='true'):
    # print('All TCs details from Project ID ' + str(projectId) + ' and folder ID ' + str(folderId) + ' requested!')
    url = config['URL']['project'] + '/' + str(projectId) + '/Folder'
    payload = {}
    headers = {
        'Authorization': Authentication.get_token()
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    testcase_details = json.loads(response.text)
    # print(response.text)
    return testcase_details


def get_folder_data(projectId):
    # print('Folders data for ' + str(projectId) +' is requested!')
    url = config['URL']['project'] + str(projectId) + '/Folder'
    payload = {}
    headers = {
        'Authorization': Authentication.get_token()
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    project_meta_details = json.loads(response.text)
    return project_meta_details


# itemType = Defect, Requirement, TestCase, TestExecution, TestScenario
def search_items(projectId = 91, itemType = None, folderId = None, SearchTerm = None):
    # print('Folders data for ' + str(projectId) +' is requested!')
    url = config['URL']['project'] + str(projectId) + '/Item'
    additional_parameters = []
    if itemType:
        additional_parameters.append('itemType=' + itemType)
    if folderId:
        additional_parameters.append('folderId=' + folderId)
    if SearchTerm:
        additional_parameters.append('searchTerm=' + SearchTerm)
    if len(additional_parameters)>0:
        url = url + '?' + "&".join(additional_parameters)

    payload = {}
    headers = {
        'Authorization': Authentication.get_token()
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    project_meta_details = json.loads(response.text)
    return project_meta_details


# parentFolders : JSON array of requested parent folders to retrieve subfolder for. For example: ['5_0',
# '3_114'] where first number is a project id and second number is folder id (or zero for root).
# includeProjects: Indicate whether to return project list as well.
# includeArchived: Indicates whether archived items should be included.
def get_subfolders_navigation_tree(parentFolders, includeProjects='false', includeArchived='false'):
    url = config['URL']['navigation'] + "Tree?parentFolders=['" + "','".join(parentFolders) + "']&includeProjects="+ includeProjects + '&includeArchived=false'
    payload = {}
    headers = {
        'Authorization': Authentication.get_token()
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    project_meta_details = json.loads(response.text)
    return project_meta_details


def TMO_TCs_List():
    records = []
    project_list = ['91']

    for iProjectId in project_list:
        startAt = 0
        while True:
            testCaseList = get_all_test_cases_details(iProjectId, folderId=0, includeSubfolders='true',
                                                      includeArchived='false', startAt=startAt, maxResults=500)
            startAt += len(testCaseList['Items'])
            for i in range(len(testCaseList["Items"])):
                # test_case = get_test_case(testCaseList["Items"][i]["Id"])
                test_cases = testCaseList["Items"][i]
                clean_dict = {}

                for j in range(len(test_cases['Details'])):
                    # print(test_cases["Details"][j]["Title"])
                    if test_cases["Details"][j]["Title"] not in \
                            ['Automated', 'Comments', 'Creation date', 'Dependency', 'Execution trend',
                             'Is Archived', 'Last execution attached labels', 'Last execution attachments',
                             'Last execution date', 'Last execution finalized', 'Last execution status',
                             'Last execution tested version', 'Mindmap', 'Object type', 'Order', 'Test scenarios',
                             'Last execution Id']:
                        clean_dict['iTMSId'] = test_cases['Id']
                        clean_dict['ProjectId'] = test_cases['Location']['ProjectId']
                        clean_dict['ProjectName'] = test_cases['Location']['ProjectName']
                        clean_dict['FolderId'] = test_cases['Location']['FolderId']
                        # clean_dict['FolderName'] = test_cases['Location']['Text']

                        clean_dict['LastModified'] = test_cases['LastModified']['Text']

                        if 'Value' in test_cases["Details"][j].keys() and isinstance(test_cases["Details"][j]['Value'],
                                                                                     dict):
                            # print('if')
                            clean_dict[test_cases["Details"][j]["Title"]] = test_cases["Details"][j]['Value']['Text']
                        elif 'Value' in test_cases["Details"][j].keys() and isinstance(
                                test_cases["Details"][j]['Value'],
                                str):
                            clean_dict[test_cases["Details"][j]["Title"]] = test_cases["Details"][j]['Value']
                            # print('elif')
                        elif 'Value' in test_cases["Details"][j].keys() and test_cases["Details"][j]['Value'] is None:
                            clean_dict[test_cases["Details"][j]["Title"]] = ''
                            # print('elif')
                        else:
                            # print(i, " ", j)
                            print(test_cases["Details"][j][
                                      "Title"])  # + ": " + test_cases["Details"][j]["Value"]["Text"])

                if clean_dict:
                    records.append(clean_dict)

            if startAt >= testCaseList['Count']:
                break
        # print("Test cases count in this folder: ", len(records))

    # print(records)
    # client = pymongo.MongoClient("mongodb://AdminTechM:u018x5Cd976V3WNY@104.248.124.202:27017")
    # db = client["TMO_Field_Testing_Production"]
    # collection = db["iTMS"]
    # collection.delete_many({})
    # collection.insert_many(records)
    # client.close()
    # print("Total Test cases count: ", len(records))
    return records


def project_path_id(project_path_list=None):
    print('Project Path ID Calculations')
    # Get Dict for required project paths
    project_path_dict = defaultdict(list)
    if project_path_list:
        for k in project_path_list.keys():
            path_list = k.split('/')
            if len(path_list) >= 3:
                oem, device, software = path_list[0], path_list[1], path_list[2]
                if oem in project_path_dict:
                    if device in project_path_dict[oem]:
                        project_path_dict[oem][device].extend([software])
                    else:
                        project_path_dict[oem][device] = [software]
                else:
                    project_path_dict[oem] = {device: [software]}

    # Get Root Folders for T-Mobile Field Performance: Project ID 91
    oem_folder = get_subfolders_navigation_tree(['91_0'])
    oem_folder_id_list = []
    oem_folder_id_dict = {}

    # Filter folder IDs for all OEM Folders
    for i in oem_folder['Subfolders']:
        for j in i:
            if j['Name'] in project_path_dict.keys():
                oem_folder_id_list.append('91_' + str(j['Id']))
                oem_folder_id_dict[j['Id']] = j['Name']

    # Get Folders for each Device for each OEM in T-Mobile Field Performance: Project ID 91
    if len(oem_folder_id_list) > 0:
        device_folder = get_subfolders_navigation_tree(oem_folder_id_list)
        device_folder_id_list = []
        device_path_dict = {}
    else:
        return False

    # Filter folder IDs for all each device in OEM Folders
    if len(device_folder) > 0:
        for i in device_folder['Subfolders']:
            for j in i:
                if j['Name'] in project_path_dict[oem_folder_id_dict[j['ParentFolderId']]]:
                    device_folder_id_list.append('91_' + str(j['Id']))
                    device_path_dict[j['Id']] = oem_folder_id_dict[j['ParentFolderId']] + '/' + j['Name']

        # Get Folders for each software for each device in T-Mobile Field Performance: Project ID 91
        sw_folder = get_subfolders_navigation_tree(device_folder_id_list)
        sw_folder_id_list = []
        sw_path_dict = {}
    else:
        return False

    # Get folder IDs for all each device in OEM Folders
    if len(sw_folder) > 0:
        for i in sw_folder['Subfolders']:
            for j in i:
                oem_temp = device_path_dict[j['ParentFolderId']].split('/')[0]
                device_temp = device_path_dict[j['ParentFolderId']].split('/')[1]
                if j['Name'] in project_path_dict[oem_temp][device_temp]:
                    sw_folder_id_list.append(j['Id'])
                    sw_path_dict[device_path_dict[j['ParentFolderId']] + '/' + j['Name']] = j['Id']
        return sw_path_dict
    else:
        return False


# Incomplete
def test():
    records = []
    for i in [9267]:
        # print(i)
        # "T-Mobile Field Performance" Project Id 91
        testCaseList = get_all_test_cases_details(projectId=91, folderId=i)
        # print(testCaseList["Items"])
        # print(get_test_case(testCaseList["Items"][0]["Id"]))

        for i in range(len(testCaseList["Items"])):
            # test_case = get_test_case(testCaseList["Items"][i]["Id"])
            test_cases = testCaseList["Items"][i]
            clean_dict = {}
            print(get_test_case((test_cases['Id'])))

            quit()

            '''
            for j in range(len(test_cases['Details'])):

                # print(test_cases["Details"][j]["Title"])
                if test_cases["Details"][j]["Title"] not in \
                        ['Attachment', 'Automated', 'Comments', 'Creation date', 'Dependency', 'Execution trend',
                         'Is Archived', 'Last execution attached labels', 'Last execution attachments',
                         'Last execution date', 'Last execution finalized', 'Last execution status',
                         'Last execution tested version', 'Mindmap', 'Object type', 'Order', 'Test scenarios',
                         'Last execution Id']:
                    clean_dict['ProjectId'] = test_cases['Location']['ProjectId']
                    clean_dict['ProjectName'] = test_cases['Location']['ProjectName']
                    clean_dict['FolderId'] = test_cases['Location']['FolderId']
                    # clean_dict['FolderName'] = test_cases['Location']['Text']

                    clean_dict['LastModified'] = test_cases['LastModified']['Text']

                    if 'Value' in test_cases["Details"][j].keys() and isinstance(test_cases["Details"][j]['Value'],
                                                                                 dict):
                        # print('if')
                        clean_dict[test_cases["Details"][j]["Title"]] = test_cases["Details"][j]['Value']['Text']
                    elif 'Value' in test_cases["Details"][j].keys() and isinstance(test_cases["Details"][j]['Value'],
                                                                                   str):
                        clean_dict[test_cases["Details"][j]["Title"]] = test_cases["Details"][j]['Value']
                        # print('elif')
                    elif 'Value' in test_cases["Details"][j].keys() and test_cases["Details"][j]['Value'] is None:
                        clean_dict[test_cases["Details"][j]["Title"]] = ''
                        # print('elif')
                    else:
                        print(i, " ", j)
                        print(test_cases["Details"][j]["Title"])  # + ": " + test_cases["Details"][j]["Value"]["Text"])'''

            if clean_dict:
                records.append(clean_dict)
        print(len(records))

    # print(records)
    '''
    client = pymongo.MongoClient("mongodb://AdminTechM:u018x5Cd976V3WNY@104.248.124.202:27017")
    db = client["TMO_Field_Testing_Production"]
    collection = db["iTMS"]
    collection.delete_many({})
    collection.insert_many(records)
    client.close()
    print(len(records))
    '''


if __name__ == '__main__':
    print("Test Case")
    # test()
