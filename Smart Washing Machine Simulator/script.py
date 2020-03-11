#Scenario: There are 6 washing machines in 3 different locations
#Creates random washer usage to simulate multiple users on the device 
#Each individual JSON message is referring to a change in one particular machine only 

#Backend 
#Import JSON and the request functionality 
import json 
import requests

#Import timed function execution functionality 
import threading 
from random import randrange

#Store locations into an array
locations = ["novena","balestier","bukit panjang"]

#Function to send message 
def send(payload,URL):
    sendURL = "http://127.0.0.1:5000/status/" + str(URL)
    print(payload)
    print(sendURL)
    r = requests.put(sendURL,json=payload)
    # print(r.text)

# Choose which functionality you want to enable 
user_command = input("What do you want me to do? ")

#Functionality 1: Be able to populate washers and set all washers to on
#The command is "turn on all"

if user_command == "turn on all":

    # Loop all identifiers to involve all machines  

    for location in locations:
        for i in range(1,7):
            #generate JSON message
            payload = {
                "errcode":"Initialisation",
                "statuscode": "on",
                "curuser": "Simulated",
                "startcode":"Simulated",
                "unlockcode":"Simulated",
                "washtype":"cold wash"
                }
            
            #Send JSON message 
            URL = i + "&" + location
            send(payload,URL)

#Functionality 2: Populate and turn off all washers 

if user_command == "turn off all":

    # Loop all identifiers to involve all machines 
    for location in locations:
        for i in range(1,7):
            #generate JSON message
            payload = {
                "errcode":"Initialisation",
                "statuscode": "off",
                "curuser": "Simulated",
                "startcode":"Simulated",
                "unlockcode":"Simulated",
                "washtype":"off"
                }
        
        # specify additional URL 
        URL = i + "&" + location
        #Send JSON message 
        send(payload,URL)

#Functionality 3: Be able to set certain washers to turn on and off 
#Command : modify

if user_command == "modify":
    machine_id = int(input("Please specify the machine ID "))
    
    #Error validation: ID cannot be more than 6 
    while machine_id> 6 and machine_id<0:
        print("This is not a correct machine ID. We only have machine IDs to 6 in each location. Please try again")
        machine_id = int(input("Please specify the machine ID "))

    user_location = input("Please specify which location you want to make the change in (no caps)")
    #Error validation. Make sure that the location is specified to one of our branches 

    while user_location not in locations:
        print("We do not have a washing branch in that location. We only have it in novena, balestier or bukit panjang. Please try again")
        user_location = input("Please specify which location you want to make the change in (no caps)")

    status = input("Please specify what modification you want to make (on,off or broken)? ")

    #Error validation
    states = ["on","off","broken"]
    while status not in states:
        print("This is not a correct modification. Please try again")
        status = input("Please specify what modification you want to make (on,off or broken)?")
    
    payload = {
        "errcode":"Initialisation",
        "statuscode": status,
        "curuser": "Simulated",
        "startcode":"Simulated",
        "unlockcode":"Simulated",
        "washtype":"off"
        }
        
    URL = str(machine_id) + "&" + user_location
    
    send(payload,URL)
    
#Functionality 4: Simulate multiple users and breakdowns 
#Command: simulate 
#Parameters : 
# - breakdowns only happen once every 2 minutes or less to any machine 
# - new request to use machine occurs once every 20 seconds or less 

if user_command == "simulate":
    simulate_user()
    simulate_error()

