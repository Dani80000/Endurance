#This file abstracts the secure connection to a central server
#Cryptography is handled in this file
from accounts import authenticate_account, find_account
from cryptography_functions import *
import json, os


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

    return True

#DMs are channels with a specific naming convention as listed above
def join_DM(user_id, receiver_id):
    dm_channel_name = f"{user_id}_{receiver_id}"
    return join_channel(None, dm_channel_name)

def join_channel(user_id, channel_name):
    if not os.path.exists("messages"):
        os.makedirs("messages")

    filename = f"messages/{channel_name}.json"

    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)

    return []

def save_message_to_json(payload):
    channel = payload.get("channel", "General")
    filename = f"messages/{channel}.json"
    
    if os.path.exists(filename):
        with open(filename, "r") as file:
            history = json.load(file)
    else:
        history = []

    history.append(payload)

    with open(filename, "w") as file:
        json.dump(history, file)
    
    print(f"Message archived in {filename}")