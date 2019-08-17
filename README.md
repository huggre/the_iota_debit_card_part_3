# Integrating physical devices with IOTA — The IOTA debit card, Part 3

The 8th part in a series of beginner tutorials on integrating physical devices with the IOTA protocol.

![img](https://miro.medium.com/max/700/1*NNFNPMckJa2_pRxHSF49QQ.jpeg)

------

## Introduction

This is the 8th part in a series of beginner tutorials where we explore integrating physical devices with the IOTA protocol. This tutorial is the third part in a sequence of tutorials where we will try to replicate a traditional fiat based debit card payment solution with an IOTA based solution. In this third tutorial we will be implementing i PIN code protection mechanism for our IOTA debit card.

------

## The Use Case

If you followed the [previous tutorial](https://medium.com/coinmonks/integrating-physical-devices-with-iota-the-iota-debit-card-part-2-1f073060ae1d) in this series you probably noticed that you are not asked for any authorization or credentials when paying with your IOTA debit card. While this might be fine in some use cases, there may be other use cases where this is not acceptable. Imagine if you lost your IOTA debit card and it was picked up by a bad actor. Without any protection mechanism there would be nothing preventing him from using your card. In this tutorial we will be addressing this issue by implementing a PIN code protection mechanism for our IOTA debit card.

This tutorial will be a little shorter than the previous tutorials in this series as we will not be introducing any new hardware or PyOTA functions.

------

## The Python code — Part 1

The python code used in this tutorial will be split into two parts where the first part is the code used when assigning a new PIN code to your IOTA debit card. The second part is a modified version of the [iota_debit_card_pay.py](https://gist.github.com/huggre/71c6aadb4e4e3d37018dc3acee5a17a0) script from the [previous tutorial](https://medium.com/coinmonks/integrating-physical-devices-with-iota-the-iota-debit-card-part-2-1f073060ae1d). Only difference is that the new version will ask you for a PIN code before scanning your IOTA debit card.

So lets start with the first Python script that will allow you to assign your own four digit PIN code to your IOTA debit card. Notice that the new PIN code will be written to the first four bytes of both block 11 and 15. The reason we need to write the PIN code to two different blocks is that each block functions as an the authentication block for the two individual sectors where the IOTA seed is stored. Check out the [6th tutorial](https://medium.com/coinmonks/integrating-physical-devices-with-iota-the-iota-debit-card-part-1-42dc1a05f18) in this series for more information on reading and writing data from the Mifare RFID tag.

```python
# Imports some required libraries
import RPi.GPIO as GPIO
import MFRC522
import signal
import regex

continue_reading = True

# Capture SIGINT for cleanup when the script is aborted
def end_read(signal,frame):
    global continue_reading
    print "Ctrl+C captured, ending read."
    continue_reading = False
    GPIO.cleanup()

# Validate that PIN consist of 4 digit's
def validate_pin(pin):
    if pin == "" or regex.fullmatch("\d{4}", pin):
        return True
    else:
        return False

# Print Welcome message
print("\nWelcome to the IOTA debit card PIN tutorial")

# Ask for old PIN code
old_pin = raw_input("\nWrite old 4 digit PIN code here or press Enter for default PIN: ")
if validate_pin(old_pin) == False:
        print("Invalid old PIN syntax")
        exit()

# Ask for new PIN code
new_pin = raw_input("\nWrite new 4 digit PIN code here or press Enter for default PIN: ")
if validate_pin(new_pin) == False:
        print("Invalid new PIN syntax")
        exit()
        
        
# Create a 16 element list inkl. new PIN to be written to autorization block
def make_pin(pin):
    if pin == "":
        pin_data = [255, 255, 255, 255, 255, 255, 255, 7, 128, 105, 255, 255, 255, 255, 255, 255]
    else:
        pin_data=[]
        pin_letter_list = list(pin)
        for letter in pin_letter_list:
            pin_data.append(ord(letter))
        pin_data = pin_data + [255, 255, 255, 7, 128, 105, 255, 255, 255, 255, 255, 255]

    return pin_data

# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()

# Display scan IOTA debit card message
print("\nHold IOTA debit card close to reader...")
print("Press Ctrl+C to exit...")

# This loop keeps checking for near by RFID tag. If one is near it will get the UID and authenticate
while continue_reading:
    
    # Scan for cards    
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

    # If a card is found
    if status == MIFAREReader.MI_OK:
        print "Card detected"
    
    # Get the UID of the card
    (status,uid) = MIFAREReader.MFRC522_Anticoll()

    # If we have the UID, continue
    if status == MIFAREReader.MI_OK:

        # Print UID
        print "Card read UID: %s,%s,%s,%s" % (uid[0], uid[1], uid[2], uid[3])
           
        # Get old authentication key
        key = make_pin(old_pin)[0:6]
        
        # Select the scanned tag
        MIFAREReader.MFRC522_SelectTag(uid)

        # Authenticate
        status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 8, key, uid)

        print "\n"

        # Check if authenticated
        if status == MIFAREReader.MI_OK:
            
            # Get new athorization data
            new_pin_data = make_pin(new_pin) 

            print("\nWriting new PIN to IOTA debit card...")
            
            # Write new authorization data to block 11
            status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 8, key, uid)
            MIFAREReader.MFRC522_Write(11, new_pin_data)
            
            # Write new authorization data to block 15
            status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 12, key, uid)
            MIFAREReader.MFRC522_Write(15, new_pin_data)

            # Stop
            MIFAREReader.MFRC522_StopCrypto1()
            
            # Print confirmation message
            print("\nThe following PIN code is now the active PIN: " + new_pin)

            # Make sure to stop reading for cards
            continue_reading = False
        else:
            print "Authentication error"
```

You can download the source code from [here](https://gist.github.com/huggre/b22698a6f404d859463d4408ae2a1bbc)

------

## Running the project

To run the the project, you first need to save the code in the previous section as a text file in the same folder as where you installed the MFRC522-python library.

Notice that Python program files uses the .py extension, so let’s save the file as **iota_debit_card_pin.py** on the Raspberry PI.

To execute the program, simply start a new terminal window, navigate to the folder where you saved *iota_debit_card_pin.py* and type:

**python iota_debit_card_pin.py**

You should now see the Python code being executed in your terminal window asking you for the old PIN code. After providing the old PIN code you will be asked for a new four digit PIN code.

*Note!*
*If you are using a new RFID tag you can just press enter when asked for the old PIN code as the script then uses the default authentication key that was assigned to the tag during manufacturing.*

*Warning!*
*It is very important that you remember or make a note of any new PIN code you assign to your IOTA debit card as there is now way of resetting or changing the PIN code later on without first providing the old PIN code.*

------

## The Python code — Part 2

The second part is a modified version of the [iota_debit_card_pay.py](https://gist.github.com/huggre/71c6aadb4e4e3d37018dc3acee5a17a0) script from the [previous tutorial](https://medium.com/coinmonks/integrating-physical-devices-with-iota-the-iota-debit-card-part-2-1f073060ae1d). Only difference is that the new version will ask you for a PIN code before scanning your IOTA debit card.

```python
# Imports some required libraries
import iota
from iota import Address
import RPi.GPIO as GPIO
import MFRC522
import signal
import time
import regex

# Setup O/I PIN's
LEDPIN=12
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(LEDPIN,GPIO.OUT)
GPIO.output(LEDPIN,GPIO.LOW)

# URL to IOTA fullnode used when interacting with the Tangle
iotaNode = "https://nodes.thetangle.org:443"
api = iota.Iota(iotaNode, "")

# Hotel owner recieving address, replace with your own recieving address
hotel_address = b'GTZUHQSPRAQCTSQBZEEMLZPQUPAA9LPLGWCKFNEVKBINXEXZRACVKKKCYPWPKH9AWLGJHPLOZZOYTALAWOVSIJIYVZ'

# Some variables to control program flow 
continue_reading = True
transaction_confirmed = False
       
# Capture SIGINT for cleanup when the script is aborted
def end_read(signal,frame):
    global continue_reading
    print "Ctrl+C captured, ending read."
    continue_reading = False
    GPIO.cleanup()

# Function that reads the seed stored on the IOTA debit card
def read_seed():
    
    seed = ""
    seed = seed + read_block(8)
    seed = seed + read_block(9)
    seed = seed + read_block(10)
    seed = seed + read_block(12)
    seed = seed + read_block(13)
    seed = seed + read_block(14)
    
    # Return the first 81 characters of the retrieved seed
    return seed[0:81]

# Function to read single block from RFID tag
def read_block(blockID):

    status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, blockID, key, uid)
    
    if status == MIFAREReader.MI_OK:
        
        str_data = ""
        int_data=(MIFAREReader.MFRC522_Read(blockID))
        for number in int_data:
            str_data = str_data + chr(number)
        return str_data
        
    else:
        print "Authentication error"

# Function for checking address balance 
def checkbalance(hotel_address):
    
    address = Address(hotel_address)
    gb_result = api.get_balances([address])
    balance = gb_result['balances']
    return (balance[0])

# Function that blinks the LED
def blinkLED(blinks):
    for x in range(blinks):
        print("LED ON")
        GPIO.output(LEDPIN,GPIO.HIGH)
        time.sleep(1)
        print("LED OFF")
        GPIO.output(LEDPIN,GPIO.LOW)
        time.sleep(1)

# Get hotel owner address balance at startup
print("\n Getting startup balance... Please wait...")
currentbalance = checkbalance(hotel_address)
lastbalance = currentbalance

# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()

# Validate that PIN consist of 4 digit's
def validate_pin(pin):
    if pin == "" or regex.fullmatch("\d{4}", pin):
        return True
    else:
        return False
    
# Create a 16 element list inkl. new PIN to be written to autorization block
def make_pin(pin):
    if pin == "":
        pin_data = [255, 255, 255, 255, 255, 255, 255, 7, 128, 105, 255, 255, 255, 255, 255, 255]
    else:
        pin_data=[]
        pin_letter_list = list(pin)
        for letter in pin_letter_list:
            pin_data.append(ord(letter))
        pin_data = pin_data + [255, 255, 255, 7, 128, 105, 255, 255, 255, 255, 255, 255]

    return pin_data


# Show welcome message
print("\nWelcome to the LED blink service")
print("\nThe price of the service is 1 IOTA for 1 blink")
blinks=input("\nHow many blinks would you like to purchase? :")

# Ask for new PIN code
pincode = raw_input("\nWrite 4 digit PIN code here or press Enter for default PIN: ")
if validate_pin(pincode) == False:
    print("Invalid PIN syntax")
    exit()

print("\nHold your IOTA debit card close to ")
print("the reader to pay for the service...")
print("Press Ctrl+C to exit...")

# This loop keeps checking for near by RFID tags. If one is found it will get the UID and authenticate
while continue_reading:
           
    # Scan for cards    
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

    # If a card is found
    if status == MIFAREReader.MI_OK:
        print "Card detected"
    
    # Get the UID of the card
    (status,uid) = MIFAREReader.MFRC522_Anticoll()

    # If we have the UID, continue
    if status == MIFAREReader.MI_OK:

        # Print UID
        print "Card read UID: %s,%s,%s,%s" % (uid[0], uid[1], uid[2], uid[3])
    
        # Get key
        key = make_pin(pincode)[0:6]
        
        # Select the scanned tag
        MIFAREReader.MFRC522_SelectTag(uid)
        
        # Get seed from IOTA debit card
        SeedSender=read_seed()
        
        # Stop reading/writing to RFID tag
        MIFAREReader.MFRC522_StopCrypto1()
                      
        # Create PyOTA object using seed from IOTA debit card
        api = iota.Iota(iotaNode, seed=SeedSender)
        
        print("\nChecking for available funds... Please wait...")
               
        # Get available funds from IOTA debit card seed
        card_balance = api.get_account_data(start=0, stop=None)
            
        balance = card_balance['balance']
        
        # Check if enough funds to pay for service
        if balance < blinks:
            print("Not enough funds available on IOTA debit card")
            exit()
        
        # Create new transaction
        tx1 = iota.ProposedTransaction( address = iota.Address(hotel_address), message = None, tag = iota.Tag(b'HOTEL9IOTA'), value = blinks)

        # Send transaction to tangle
        print("\nSending transaction... Please wait...")
        SentBundle = api.send_transfer(depth=3,transfers=[tx1], inputs=None, change_address=None, min_weight_magnitude=14, security_level=2)
                       
        # Display transaction sent confirmation message
        print("\nTransaction sent... Please wait while transaction is confirmed...")
        
        # Loop executes every 10 seconds to checks if transaction is confirmed
        while transaction_confirmed == False:
            print("\nChecking balance to see if transaction is confirmed...")
            currentbalance = checkbalance(hotel_address)
            if currentbalance > lastbalance:
                print("\nTransaction is confirmed")
                blinkLED(blinks)
                transaction_confirmed = True
                continue_reading = False
            time.sleep(10)
```

You may download the source code from [here](https://gist.github.com/huggre/7f4938e189bfbe783004abdc349c12cc)

## Running the project

To run the the project, you first need to save the code in the previous section as a text file in the same folder as where you installed the MFRC522-python library.

Notice that Python program files uses the .py extension, so let’s save the file as **iota_debit_card_pay_pin.py** on the Raspberry PI.

To execute the program, simply start a new terminal window, navigate to the folder where you saved *iota_debit_card_pay_pin.py* and type:

**python iota_debit_card_pay_pin.py**

You should now see the Python code being executed in your terminal window, first asking you for the amount of “blinks” you would like to purchase, then asking for a PIN code. Type the PIN code you assigned to the tag using the previous Python script (or press Enter if you have not assigned a new PIN code). If you do not provide a valid PIN code the script will abort with an authentication error.

------

## What's next?

I was thinking it would be fun to build a Visa style IOTA based payment terminal using some off-the-shelf components such as a keypad, 2x16 digit display and an RFID reader. I just hope i have enough GIO pins on my Raspberry PI. Will see how it goes.., stay tuned.

------

## Donations

If you like this tutorial and want me to continue making others, feel free to make a small donation to the IOTA address shown below.

![img](https://miro.medium.com/max/400/1*kV_WUaltF4tbRRyqcz0DaA.png)

> GTZUHQSPRAQCTSQBZEEMLZPQUPAA9LPLGWCKFNEVKBINXEXZRACVKKKCYPWPKH9AWLGJHPLOZZOYTALAWOVSIJIYVZ
