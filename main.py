import eel
import threading
import client 
import queue

eel.init('web')
instance_queue = queue.Queue()

@eel.expose
def start_client_logic(username, password, action):
    threading.Thread(
        target=client.run_client, 
        args=(username, password, action, instance_queue), 
        daemon=True
    ).start()

@eel.expose
def send_chat_message(msg, channel):
    instance_queue.put({"msg": msg, "channel": channel})

if __name__ == '__main__':
    eel.start('index.html', size=(600, 500), port=0) # this is for testing multiple windows at a time