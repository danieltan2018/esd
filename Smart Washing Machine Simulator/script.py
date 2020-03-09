#Scenario: There are 6 washing machines in 3 different locations
#Creates random washer usage to simulate multiple users on the device 
#Each individual JSON message is referring to a change in one particular machine only 

#Backend 
#Import JSON and the request functionality 
import json 
import requests

#Store locations into an array
locations = ["Novena","Balestier","Bukit Panjang"]

#Store the number of washers for looping. Each number represents one ID 
number_of_washers = 18 

user_command = input("What do you want me to do? ")

#Function to send message 
def send(payload):
        r = requests.post('https://reqres.in/api/users?page=2',json=payload)
        print(r.text)


#Functionality 1: Be able to set all washers to work 
#The command is "turn on all"

if user_command == "turn on all":
    #Loop all locations to turn on all machines 
    for i in range(1,number_of_washers+1):
        
        #generate JSON message
        payload = {
            "MachineID":i,
            "Status": "on"}
        
        #Send JSON message 
        
        send(payload)
        
        # Uncomment below when the you know where to send the details to 

#Functionality 2: Be able to set certain washers to turn on and off 
#Command : modify

if user_command == "modify":
    machine_id = int(input("Please specify the machine ID "))
    #Error validation

    while machine_id > 18 or machine_id<0:
        print("This is not a correct machine ID. Please try again")
        machine_id = int(input("Please specify the machine ID "))


    status = input("Please specify what modification you want to make (on,off or broken)? ")

    #Error validation
    states = ["on","off","broken"]
    while status not in states:
        print("This is not a correct modification. Please try again")
        status = input("Please specify what modification you want to make (on,off or broken)?")
    
    payload = {
            "MachineID": machine_id,
            "Status": status}
    
    send(payload)
    

