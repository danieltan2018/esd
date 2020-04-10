# DE’LAUNDRO PROJECT README

Pre-requisites: Docker, Docker Compose (required libraries will be installed by docker)

## How to run microservices:
1. Start RabbitMQ server (Docker image) using “docker run -d --hostname my-rabbit --name some-rabbit rabbitmq:3”
2. Navigate into the respective folder for each microservice:
   * user
   * queue
   * status
   * monitoring
   * error_handling
   * vendor
3. For microservices with external API, create .env file following the .dummyenv format
   * User Microservice - Telegram Bot API & Stripe API token
   * Monitoring Microservice - Mailgun API key
4. Run “docker-compose up -d” to build and run the containers in the background (detached mode)
   * Note: queue, status, monitoring and vendor cannot be run on the same machine as they all bind to external port 80

## How to use the Smart Washing Machine Simulator (script.py):
This script simulates individual smart washing machines sending HTTP requests to the Status microservice.

When running the script you will be prompted with a question “What do you want me to do?”. 

The script will be able to understand 3 inputs. Note that you would have to type in the words exactly or you would get the error “Invalid command. Please try again”.

These are the commands available:
1. “turn on all”
   * This would populate the status database according to the parameters in our scenario and set them all to on 
2. “use machine”
   * This would allow you to start the machine (set the status code of the machine to 1) only after you have been given a qr code 
   * You will have to mention your location “balestier”,”novena” or “bukit panjang”
   * You will have to mention your machine ID, which is only valid from 1 to 6 
   * You will have to use a QR code scanner to be able to input the QR code for this simulation. 
3. “turn off one machine”
   * This will allow you to manipulate the backend database, as it was shown in the demonstration, to set one machine in your database to “available”.