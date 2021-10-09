# This code will send data collected by RFID sensor to remote database


#including packages
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import requests
import time
import os
import mysql.connector
from datetime import datetime

# setting up raspberry pi pins for leds
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
red = 37
green = 36
GPIO.setup(green, GPIO.OUT)
GPIO.setup(red, GPIO.OUT)

# Changing the connection from local sqlite3 database to remote mysql database
# connection = sqlite3.connect('datalogger.db')
connection = mysql.connector.connect(host='rfidcheckin.cljhbnnuplh1.ap-southeast-2.rds.amazonaws.com',database='rfidDB',user='admin',password='PASSWORD')

cursor = connection.cursor()

# location ID for raspberry Pi module, will differ by location/shop. Unique to each reader.
location_ID = 12345654

class Logger:
    
    def __init__(self):
        self.values = []
        self.reader= SimpleMFRC522()
    
    # read details of tag when tag is presented
    def read_card(self):
        card_id = None
        card_id, data = self.reader.read()
        now = datetime.now()
        latest_entry = (card_id, now, data)
        self.values.append(latest_entry)
    
    # This function was created during testing for confirmation on connection. It is not required now.
    def create_table(self):
        cursor.execute("CREATE TABLE IF NOT EXISTS sarah_testing (card_id VARCHAR(255), date_time VARCHAR(255), tag_info VARCHAR(255))")
    
    # This function will send out data to the database
    def store_data(self):

        latest_row = self.values[-1]
        
        card_id = latest_row[0]
        date_time = latest_row[1]
        tag_info = latest_row[2]
        
        # 12 characters for tag info total. trim excess.
        required_tag_info = tag_info[0:12]
         
        #inserting data in predefined table
        sql = "INSERT INTO rfidDB.taps (tag_id, time, user_id) VALUES (%s, %s, %s)"  
        val = (card_id, date_time, required_tag_info)
        
        # uploading recorded data
        cursor.execute(sql,val)
        
        # saving data onto database in respective table
        connection.commit()
        # ideally, location id will also be sent along with this data to the database to identify which reader has read this ID
    # controlling Green LED and Buzzer through green led code
    def green_led(self):
        GPIO.output(green, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(green, GPIO.LOW)
    
    # Controlling red led, buzzer will not ring at unsuccessful reading
    def red_led(self):
        GPIO.output(red, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(red, GPIO.LOW)
    
   # checking data before adding to database 
    def data_check(self):
        
        # reading data from the latest row
        latest_row = self.values[-1]
        
        card_id = latest_row[0]
        date_time = latest_row[1]
        tag_info = latest_row[2]
        
        # using first four digits of tag info to authenticate successful read
        if card_id != None and tag_info[0:4] == "1234":
            #print(len(str(card_id)))
            #print("type of time", type(date_time))
            return True
        
        # unsucessful read
        else:
            print("Data not read properly, entry not stored in file")
                
        return False
        


def main():
    try:
        logger = Logger()
        print("running....")
       # logger.create_table() // this table was created for testing purposes in db to check connection
       
       # continously reading data
        while True:
            
            # read data from card
            logger.read_card()
            
            # check data and see if it is a successful read
            if logger.data_check() == True:
                logger.store_data()
                logger.green_led()
            else:
                logger.red_led()
                continue
    
    # turn off connection
    except KeyboardInterrupt:
        print("Quit")
        cursor.close()
        connection.close()

        GPIO.cleanup()
  
main()

 
