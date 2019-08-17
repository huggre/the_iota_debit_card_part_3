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
