#This file abstracts the secure connection to a central server
#Cryptography is handled in this file
from accounts import authenticate_account, find_account
from cryptograpy_functions import *


#Call this function to connect to a channel:
def connect(user_id, password, channel=None, receiver_id = None):
    #When connecting, you can connect to a channel / server OR a receiver Direct Message
    if not (authenticate_account(user_id, password)):
        print("Invalid Credentials")
        return False
    if (channel == None and receiver_id == None):
        print("No user specified")
        return False
    if (channel and receiver_id):
        print("Can only message either a channel or a user")
        return False
    
    if receiver_id:
        if not find_account(receiver_id):
            print("Invalid Receiver ID")
            return False
        else:
            sortedID = [user_id, receiver_id].sorted()
            join_DM(sortedID[0], sortedID[1]) #ensures recall of same chat even if receiver initializes
    
    if channel:
        join_channel(user_id, channel)

def join_DM(id_1, id_2):
    #TODO
    pass

def join_channel(user_id, channel_name):
    #TODO
    pass