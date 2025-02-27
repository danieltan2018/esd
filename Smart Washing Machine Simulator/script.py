#Scenario: There are 6 washing machines in 3 different locations
#Creates random washer usage to simulate multiple users on the device 
#Each individual JSON message is referring to a change in one particular machine only 

#Backend 
#Import JSON and the request functionality 
import json 
import requests

#Store locations into an array
locations = ["Novena","Balestier","Bukit Panjang"]


# Choose which functionality you want to enable 
user_command = input("What do you want me to do? ")

#Functionality 1: Be able to populate washers and set all washers to on
#The command is "turn on all"

if user_command == "turn on all":

    # Loop all identifiers to involve all machines  

    for location in locations:
        for i in range(1,7):
        
            # sendURL = "http://127.0.0.1:8002/createMachine?machineid=" + str(i) + "&location=" + location
            sendURL = "http://status.delaundro.me/createMachine?machineid=" + str(i) + "&location=" + location
            print(sendURL)
            r = requests.post(sendURL)
            # print(r.text)
            # Update to in use 
            updateURL = "http://status.delaundro.me/updateMachineStatus?machineid=" + str(i) + "&location=" + location
            payload = {
                "statuscodeid": 1
            }
            print(updateURL)
            b = requests.put(updateURL,json=payload)
            # print(b.text)

# Functionality 4: Start a machine with a QR code.
if user_command == "use machine":
    
    # Getting necessary parameters
    location = input("Where are you now? ")
    machine_id = input("What is your Machine ID? ")
    qrcode = input("What is your QR Code? ")

    # Calling microservice to get QR code 

    # URL = "http://127.0.0.1:8002/getQRCode?machineid=" + machine_id +"&location=" + location 
    URL = "http://status.delaundro.me/getQRCode?machineid=" + machine_id +"&location=" + location
    # print(URL)
    r = requests.get(URL)
    # print(r.text)
    data = r.json()
    # print(data)
    unlockcode = data["unlockcode"]
    startcode = data["startcode"]
    
    if unlockcode == qrcode:
        print("Door open")

    elif startcode == qrcode:

        # Change status of machine to in use 
        change_status_url = "http://status.delaundro.me/updateMachineStatus?machineid=" + machine_id + "&location=" + location        
        payload = {
                "statuscodeid": 1
            }
        x = requests.put(change_status_url,json=payload)

        # print(change_status_url)
        # print(x.text)

        # Receive washtype to display 
        # Get User ID first
        # user_id_url = "http://127.0.0.1:8002/getStartCode?machineid=" + machine_id + "&location=" + location + "&startcode=" + startcode 
        user_id_url = "http://status.delaundro.me/getStartCode?machineid=" + machine_id + "&location=" + location + "&startcode=" + startcode
        z = requests.get(user_id_url)
        # print(change_status_url)
        # print(z.text)
        userid_object = z.json()
        userid = userid_object["userid"]
        # print(userid)

        # Get washtype from Queue
        # washtype_url = "http://127.0.0.1:5000/washtype?user_id=" + str(userid)
        washtype_url = "http://queue.delaundro.me/washtype?user_id=" + str(userid)  
        a = requests.get(washtype_url)
        # print(a.text)
        washtype_object = a.json()
        washtype = washtype_object["wash type"]

        print("Your machine has started. Your wash type is: " + washtype)
    
    else:
        print("Invalid QR code")


#Functionality 5: Turn off one machine 

if user_command == "turn off one machine":
    location = input("Where are you now? ")
    machine_id = input("What is your Machine ID? ")
    updateURL = "http://status.delaundro.me/updateMachineStatus?machineid=" + machine_id + "&location=" + location
    payload = {
        "statuscodeid": 0
    }
    print(updateURL)
    x = requests.put(updateURL,json=payload)

    # print(change_status_url)
    # print(x.text)

else:
    print("Invalid command. Please try again")
