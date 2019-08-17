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