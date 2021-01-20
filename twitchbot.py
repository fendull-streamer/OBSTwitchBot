import socket
import threading
import time

SERVER = "irc.chat.twitch.tv"
PORT = 6667
BURST_CAPACITY = 20
REFRESH_RATE = 0.66

def DEFAULT_MESSAGE_PROCESSOR(message):
    print(message)

class TwitchBot:

    class Message:
        def __init__(self, text, channel=None):
            self.text = text
            self.channel = channel

        def encode(self):
            if self.channel is not None:
                return "PRIVMSG #{} :{} \n".format(self.channel, self.text).encode('utf-8')
            else: 
                return "{}\n".format(self.text).encode('utf-8')



    class MessageExecutor(threading.Thread):
        def __init__(self, queue, bot):
            threading.Thread.__init__(self)
            self.bot = bot
            self.queue = queue
        
        def run(self):
            self.queue.message_queue_lock.acquire()
            message = self.queue.message_queue.pop(0)

            data = message.encode()
            
            self.bot.sock_lock.acquire()
            print(data)
            self.bot.sock.send(data)
            self.bot.sock_lock.release()
            if len(self.queue.message_queue) > 0:
                new_executor = self.bot.MessageExecutor(self.queue, self.bot)
                new_executor.start()
            self.queue.message_queue_lock.release()


    class MessageQueue:
        def __init__(self, bot):
            self.bot = bot
            self.message_queue = []
            self.message_queue_lock = threading.Lock()

        def add_to_queue(self, message):
            self.message_queue_lock.acquire()
            self.message_queue.append(message)
            
            if len(self.message_queue) == 1:
                self.bot.MessageExecutor(self, self.bot).start()
            self.message_queue_lock.release()


    class MessageReader(threading.Thread):

        def __init__(self, socket, message_handler):
            threading.Thread.__init__(self)
            self.socket = socket
            self.is_running = False
            self.handle_message = message_handler
            pass
        

        def run(self):
            self.is_running = True

            def buffer_ready(buffer):
                if len(buffer) < 2:
                    return False
                if buffer[-2:] == b'\r\n':
                    return True

                return False

            buffer = b''
        
            while self.is_running is True:
                try:
                    while not buffer_ready(buffer) is True and self.is_running is True:
                        self.socket.settimeout(10) 
                        buffer += self.socket.recv(4096)
                        
                    if len(buffer) > 1:
                        self.handle_message(buffer[:-2])
                    buffer = b''
                except:
                    pass

    class TokenBucketManager(threading.Thread):

            def __init__(self, bot):
                threading.Thread.__init__(self)
                self.bot = bot
                self.is_running = False
                self.last_updated = time.time()

            def run(self):
                self.is_running = True
                while self.is_running is True:
                    if time.time() - self.last_updated < 1:
                        time.sleep(1 - (time.time() - self.last_updated))
                    self.update_tokens()

            def update_tokens(self):
                self.bot.token_lock.acquire()
                self.bot.tokens = min(REFRESH_RATE + self.bot.tokens, BURST_CAPACITY)
                self.bot.token_lock.release()        



    def __init__(self, oauth, name, message_handler=DEFAULT_MESSAGE_PROCESSOR):
        
        self.oauth = oauth
        self.name = name
        self.tokens = BURST_CAPACITY
        def parse_message(buffer):
            message = buffer.decode('utf-8')
            print(message)
            if message[0:4] == "PING":
                self.send("PONG")
                return
            else:
                try:
                    message_split = message.split(":")
                    message_info = message_split[1]
                    message_info = message_info.split(" ")
                    if (message_info[1] == 'PRIVMSG'):
                        message_channel = message_info[2][1:]
                        message_text = ":".join(message_split[2:])
                        message_sender = message_info[0].split("@")[1].split('.')[0]
                        message_texts = message_text.split(' ')
                        data = {
                            "original": message,
                            "message_info": message_info,
                            "channel": message_channel,
                            "text": message_text,
                            "sender": message_sender,
                            "twitch": self
                        }

                        resp = message_handler(data)
                        if not resp is None:
                            self.send_to_channel(resp['text'], resp['channel'])
                except Exception as e:
                    print("error parsing message")
                    print(e)
                    print(message)
        self.message_handler = parse_message


        

    def __enter__(self):

        self.begin()

        return self
    
    def begin(self):

        self.sock_lock = threading.Lock()
        self.sock = socket.socket()
        self.connect_to_twitch()

        self.token_lock = threading.Lock()
        self.token_bucket_manager = self.TokenBucketManager(self)
        self.token_bucket_manager.start()

        self.queue = self.MessageQueue(self)

        self.message_reader = self.MessageReader(self.sock, self.message_handler)
        self.message_reader.start()


    def join_channel(self, channelname):
        self.send("JOIN #{}\n".format(channelname))

    def send_to_channel(self, text, channel):
        self.queue.add_to_queue(self.Message(text, channel=channel))

    def send(self, text):
        self.queue.add_to_queue(self.Message(text))

    def stop(self):
        self.token_bucket_manager.is_running = False
        self.message_reader.is_running = False

    def __exit__(self, type, value, traceback):
        self.stop()

    def connect_to_twitch(self):
        
        self.sock_lock.acquire()
        self.sock.connect((SERVER, PORT))
        self.sock.send("PASS {}\n".format(self.oauth).encode('utf-8'))
        self.sock.send("NICK {}\n".format(self.name).encode('utf-8'))
        self.sock_lock.release()
        print("connected")

