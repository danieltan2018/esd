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
locations = ["Novena","Balestier","Bukit Panjang"]

#Store the number of washers for looping. Each number represents one ID 
number_of_washers = 18 

user_command = input("What do you want me to do? ")

#Function to send message 
def send(payload):
        r = requests.put('https://reqres.in/api/users?page=2',json=payload)
        print(r.text)

#Function to simulate user 
def simulate_user():
    time = randrange(1,21)
    threading.Timer(time,simulate_user).start()
    random_machine_ID = randrange(1,19)
    payload = {
        "MachineID":random_machine_ID,
        "errcode":"none",
        "statuscode": "on"
    }
    send(payload)

#Function to simulate random errors 

def simulate_error():
    time = randrange(1,121)
    threading.Timer(time,simulate_user).start()
    random_machine_ID = randrange(1,19)
    payload = {
        "MachineID":random_machine_ID,
        "errcode":"simulated",
        "statuscode": "broken"
    }
    send(payload)

#Functionality 1: Be able to set all washers to work 
#The command is "turn on all"

if user_command == "turn on all":
    #Loop all locations to turn on all machines 
    for i in range(1,number_of_washers+1):
        
        #generate JSON message
        payload = {
            "MachineID":i,
            "errcode":"none",
            "statuscode": "on"
            }
        
        #Send JSON message 
        
        send(payload)

#Functionality 2: Be able to turn off all washers 

if user_command == "turn off all":
    #Loop all locations to turn on all machines 
    for i in range(1,number_of_washers+1):
        
        #generate JSON message
        payload = {
            "MachineID":i,
            "errcode":"none",
            "statuscode": "off"
            }
        
        #Send JSON message 
        
        send(payload)

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
            "MachineID":i,
            "errcode":"simulated",
            "statuscode": "broken"
    }
    
    send(payload)
    
#Functionality 4: Simulate multiple users and breakdowns 
#Command: simulate 
#Parameters : 
# - breakdowns only happen once every 2 minutes or less to any machine 
# - new request to use machine occurs once every 20 seconds or less 

if user_command == "simulate":
    simulate_user()
    simulate_error()

