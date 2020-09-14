#########################################################################
#  Manage PD Script                                                     #
#  Filename: manage_pd_v2.py                                            #
#  Script Version: 1.0.0                                                #
#########################################################################
#  Prerequisites:                                                       #
#  1. Access to CVM shell                                               #
#  2. REST API version 2.0                                              #
#  3. admin password to Prism Element                                   #
#########################################################################
#  Synopsis                                                             #
#  This script will assist in listing all the protection domains.       #
#  It will ask you for your input on selecting the PD.                  #
#  You may select the PDs based on the following formats:               #
#       1. Numbers:                                                     #
#               - List of numbers, for ex: 1,4,5                        #
#               - Group of numbers, for ex: 1-4, 7-10                   #
#  After selecting the Protection Domains, it will activate and destroy #
#  the selected PDs on the cluster where this script is being run       #
#########################################################################
# Disclaimer                                                            #
# This code is intended as a standalone example. Subject to licensing   #
# restrictions defined on nutanix.dev, this can be downloaded, copied   #
# and/or modified in any way you see fit.                               #
# Please be aware that all public code samples provided by Nutanix are  #
# unofficial in nature, are provided as examples only, are unsupported  #
# and will need to be heavily scrutinized and potentially modified      #
# before they can be used in a production environment. All such code    #
# samples are provided on an as-is basis, and Nutanix expressly         #
# disclaims all warranties, express or implied.                         #
# All code samples are © Nutanix, Inc., and are provided as-is under    #
# the MIT license. (https://opensource.org/licenses/MIT)                #
#########################################################################

import os
import requests
import base64
import pexpect
import json

activate_pd_list = []
list_data=[]
start=0
end=0
temp=0


# Get a Prism IP
stream = os.popen('svmips')
svm_ips = stream.read()
svm_ips = svm_ips.strip()
svm_ip = svm_ips.split(',')[0]

def validate_input(data):
    if(len(data)==0):
	print "Invalid input"
	exit()
    for i in range(0,len(data)):
        if((ord(data[i])<ord('0') or  ord(data[i])>ord('9')) and data[i]!='-'):
            print "Invalid input"
            exit()

    if(data[0]=='-' or data[len(data)-1]=='-'):
    	print "Invalid input"
    	exit()

    if('-' in data):
    	return False
    else:
    	return True

# List the PDs
passwd = raw_input("Enter admin password: ")
url = "https://"+svm_ip+":9440/PrismGateway/services/rest/v2.0/protection_domains/"
base64string = base64.encodestring('%s:%s' %('admin', passwd)).replace('\n', '')
headers = {'Authorization':'Basic %s' % base64string}
r = requests.get(url,verify=False,headers=headers)

if(r.status_code!=200):
    print "Invalid password"
    exit()

pd_list_json = r.json()

pd_list=[]

print "\n\nList of Protection Domains configured in this cluster:"
for each in pd_list_json['entities']:
    pd_list.append(each['name'])

pd_list.sort()

for each in pd_list:
    print "%s. %s" % (pd_list.index(each)+1,each)

print "\nProtection Domain selection using comma separated list:"
print "You can choose the protection domains by using one or more of the following selection methods"
print "a) List of numbers, ex: 1,4,5"
print "b) Range of numbers (low-high), ex: 1-4,7-10"
print "c) A mix of both, ex: 1,4,7-10"


data = raw_input("\n\nEnter the list/group of numbers seperated by comma: ")
# Parse the data obtained and collect the intended PD in another list
# - split by comma
list_data = data.split(',')

for each in list_data:
# - trim
    each.strip()
    flag_input = validate_input(each)
    
    if (flag_input and (int(each)-1 < len(pd_list))):
        activate_pd_list.append(pd_list[int(each)-1])
    elif(flag_input and int(each)-1 > len(pd_list)):
        print "Invalid input. Index out of range"
        exit()
    elif(not flag_input):
# - split by dash(-) if contained in the string
        each_list = each.split('-')
        if(len(each_list) >2):
            print "Invalid input"
            exit()
        flag_input=validate_input(each_list[0]) and validate_input(each_list[1])
        if flag_input:
            start = int(each_list[0])-1
            end = int(each_list[1])-1
        else:
            print "Invalid input"
            exit()
# - validate all the input - check if any going out of range
        if(start>end):
            temp=start
            start=end
            end=temp
        if(end>len(pd_list)):
            print "Invalid input"
            exit()
# - Fill the intended PD in another list -> activate_pd_list
        for i in range(start,end+1):
            activate_pd_list.append(pd_list[i])

print "\n\nChoose what you would like to do to the below PDs:\n"
activate_pd_list = list(set(activate_pd_list))
print activate_pd_list
print "\n\n1. Activate the PD(s) on this cluster"
print "2. Deactivate the PD(s) & Destroy VM(s) on this cluster"
print "3. Migrate to Remote cluster"
# Request -> Activate, Migrate, Deactivate & Destroy VMs

data = input("\n Your input: ")

if(type(data)!=type(1)):
	print "Invalid input"
	exit()

if(int(data)==1):
	for each in activate_pd_list:
		url = "https://"+svm_ip+":9440/PrismGateway/services/rest/v2.0/protection_domains/"+each+"/activate"
		r = requests.post(url,data=json.dumps({}),verify=False,headers=headers)
		print r.text

if(int(data)==2):
	for each in activate_pd_list:
		process = pexpect.spawn("ncli pd deactivate-and-destroy-vms name="+each)
		process.expect(".*(y/N)?: ",timeout=None)
		process.sendline("y\n")
		print process.after
		print process.read()
if(int(data)==3):
	for each in activate_pd_list:
		url = "https://"+svm_ip+":9440/PrismGateway/services/rest/v2.0/protection_domains/"+each+"/migrate"
		r = requests.post(url,data=json.dumps({}),verify=False,headers=headers)
		print r.text


exit()


