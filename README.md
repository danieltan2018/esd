# esd
G4T4's Enterprise Solution Development Project

DE’LAUNDRO PROJECT README
Pre-requisites: Python, Docker, Docker Compose, RabbitMQ, WAMP Server, HTML 
Import libraries: Json, sys, os, pika, requests, telegram, Javascript, CORS, Flask, jsonify, SQL Alchemy, uuid
API: Mailgun API, Qr Server API, Stripe API, Google API
https://docs.docker.com/compose/gettingstarted/

How to use Docker Compose: 

Create directories for the project within your docker image
-Error_handling
-Monitoring
-Queue
-Status
-User
-Vendor

Create requirements.txt and docker-compose.yml files for the microservices

Build the APP with Compose by accessing the directories individually and execute 
docker-compose down
Git Pull 
Docker-compose up -d


How to use the Smart Washing Machine Simulator (script.py)

When running the script you will be prompted with a question “What do you want me to do?”. 

The script will be able to understand 3 inputs. Note that you would have to type in the words exactly or you would get the error “Invalid command. Please try again”.

These are the commands available:

-“turn on all”
This would populate the status database according to the parameters in our scenario and set them all to on 

-“use machine”
This would allow you to start the machine (set the status code of the machine to 1) only after you have been given a qr code 
You will have to mention your location “balestier”,”novena” or “bukit panjang”
You will have to mention your machine ID, which is only valid from 1 to 6 
You will have to use a QR code scanner to be able to input the QR code for this simulation. 

-“turn off one machine”
This will allow you to manipulate the backend database, as it was shown in the demonstration, to set one machine in your database to “available”.


All Docker Compose documents can be accessed via command prompt at:
ssh root@<URL>
Password: delaundro.me
