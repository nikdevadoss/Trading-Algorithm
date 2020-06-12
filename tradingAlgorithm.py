#imports
import os
import alpaca_trade_api as tradeapi
import quandl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import time
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import keys
import requests, json


#Alpaca setup details
BASE_URL = "https://paper-api.alpaca.markets"
ORDERS_URL = "{}/v2/orders".format(BASE_URL)
HEADERS = {"APCA-API-KEY-ID": keys.alpacaKey['api_key'] , "APCA-API-SECRET-ID": keys.alpacaKey['secret_key']}


#personal info
senderAddress = keys.personalInfo['senderEmail']
senderPass = keys.personalInfo['senderPass']
receiverAddress = keys.personalInfo['recieverEmail']
phoneRecipient = keys.personalInfo['phoneNumber']

#twilio setup
from twilio.rest import Client
twilioNumber = keys.personalInfo['twilioNumber']

#trading vars
qty = 100

#main trading algorithm
while(clock.is_open):
    #specify trading enviromnent
    os.environ["APCA_API_BASE_URL"] = BASE_URL
    api = tradeapi.REST(keys.alpacaKey['api_key'], keys.alpacaKey['secret_key'])
    account = api.get_account()
    clock = api.get_clock()

    #pull data
    currAsset = api.get_asset(stock)
    bars = api.get_barset(stock, 'minute', 1)

    #get bars to find spread over each period
    currBar = bars[stock][0]
    open = currBar.o
    close = currBar.c

    try:
        position = api.get_position(stock)
    except:
        position = None

    
    if(clock.is_open):
        if(position == None and account.daytrade_count < 3):
            #buys if there is a doji star (spread is less than 1%)
            if(abs(open - closed) <= 0.01):
                api.submit_order(stock, qty, "buy", "market", "day")
                order(stock, qty, "buy", "market", "day")
                message = "Purchased " + qty + " shares of " + stock
                print(message)
                sendText(message)
            else:
                print("No position to buy")
        else:
            #sells if false indicator or realizes certain profit margins (4% growth)
            if(position.unrealized_pl < 0 or position.unrealized_plpc > 0.4):
                api.submit_order(stock, qty, "sell", "market", "day")
                message = "Sold " + qty + " shares of " + stock
                print(message)
                sendText(message)
            else:
                print("Holding stock")
    else:
        print("Market is currently closed, terminating program")
        exit()
    time.sleep(3)

        

def exponentialMovingAverage(values, window):
    weights = np.exp(np.linspace(-1., 0., window))
    weights /= weights.sum()
    a = np.convolve(values, weights)[:len(values)]
    a[:window] = a[window]
    return a

def order(symbol, qty, side, type, time_in_force):
    data = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": type,
        "time_in_force": time_in_force
    }
    r = requests.post(ORDERS_URL, json= data, headers= HEADERS)
    return json.loads(r.content)

#Send text message to given phone number
def sendText(message):
    client = Client(keys.twilioKey['sid'], keys.twilioKey['auth_token'])
    client.messages.create(to= phoneRecipient, from_= twilioNumber, body= message)

#takes message and sends email to receiverAddress
def sendMail(mailContent):
    message = MIMEMultipart()
    message['From'] = 'CryptoBot'
    message['To'] = receiverAddress
    message['Subject'] = 'Trade Executed'
    message.attach(MIMEText(mailContent, 'plain'))
    session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
    session.starttls() #enable security
    session.login(senderAddress, senderPass) #login with mail_id and password
    text = message.as_string()
    session.sendmail(senderAddress, receiverAddress, text)
    session.quit()
