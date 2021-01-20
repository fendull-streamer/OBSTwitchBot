import dbm
import json
import threading
from twitchbot import *
import time
import importlib.util
import os

COMMAND_DB = 'COMMANDS'
DEFAULT_COMMAND_FILE = 'command_config.json'
COMMAND_DUMP = 'command_dump.json'
CONFIG_DB = 'CONFIG'
DEFAULT_CONFIG_FILE = 'default_config.json'
PLUGINS_PATH = "Plugins"


class BotProcess:
    def __init__(self, parent, settings_path):
        self.command_store = None
        self.config = None
        self.bot = None
        self.parent = parent
        self.settings_path = settings_path

    def __enter__(self):
        self.command_store = initialize_command_store(self.settings_path)
        self.config_store = initialize_config_store(self.settings_path)
        try:
            print('Attempting to start the Twitch bot')
            print("Access Token Length: {}".format(len(self.config_store['access_token'])))
            self.bot = TwitchBot(self.config_store['access_token'].decode(
                'utf-8'), self.config_store['nickname'].decode('utf-8'), message_handler=self.parent.message_handler)
            self.bot.begin()
            channels = self.config_store['channels'].decode('utf-8').split(',')
            for channel in channels:
                self.bot.join_channel(channel)
        except Exception as e:
            print(e)

        return self

    def __exit__(self, type, value, traceback):
        self.command_store.close()
        self.config_store.close()
        if not self.bot is None:
            self.bot.stop()
        for pname, plugin in self.parent.plugins.items():
            plugin.shutdown(self.parent)

class OBSTwitchBot(threading.Thread):

    def load_plugins(self):
            self.plugins = {}
            for fname in os.listdir(self.settings_path + PLUGINS_PATH):
                if fname.endswith('.py') is True:
                    module_name = fname.split('.')[0]
                    relative_path = "{}\\{}".format(self.settings_path + PLUGINS_PATH, fname)
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, relative_path)
                        plugin = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(plugin)
                        plugin.setup(self)
                        self.plugins[module_name] = plugin
                    except:
                        print("Failed to add module '{}'".format(module_name))

    def __init__(self, settings_path=""):
        threading.Thread.__init__(self)
        self.settings_path = settings_path
        self.bot = None
        self.is_running = False
        print(os.listdir())
        self.load_plugins()

        

    def run(self):
        self.is_running = True
        with BotProcess(self, self.settings_path) as bot:
            self.bot = bot
            while self.is_running:
                time.sleep(2)

    def stop(self):
        print("Stopping Twitchbot")
        self.is_running = False

    def set_access_token(self, token):
        if self.bot is None:
            return
        print("setting token")
        self.bot.config_store['access_token'] = token

    def set_nickname(self, name):
        if self.bot is None:
            return
        print("setting nickname")
        self.bot.config_store['nickname'] = name

    def dump_commands(self):
        if self.bot:
            out = {}
            for key in self.bot.command_store.keys():
                out[key.decode(
                    'utf-8')] = json.loads(self.bot.command_store[key].decode('utf-8'))
                print(out)
            with open(self.settings_path + COMMAND_DUMP, "w") as f:
                json.dump(out, f)

    def add_command(self, name, actions, validations):
        self.bot.command_store[name] = json.dumps({
            "actions": actions,
            "validations": validations
        })

    def message_handler(self, message):
        split_message = message['text'].split(' ')
        if not split_message[0][0] == '!':
            return
        command = split_message[0][1:].lower()
        self.do_get_command(command, message)

    def do_get_command(self, command, message):
        if not command in self.bot.command_store:
            return
        command_data = json.loads(
            self.bot.command_store[command].decode('utf-8'))
        self.do_command(command_data, message)

    def do_command(self, command_data, message):
        for action in command_data['actions']:
            print("Action:{}:{}".format(action['name'], str(action['args'])))
            def do_action_parallel():
                
                action_name = action['name']
                module = self.plugins[action_name.split('.')[0]]
                func = getattr(module, action_name.split('.')[1])

                if "args" in action:
                    args = action["args"]
                else:
                    args = None
                
                result = func(self, message, args)
                if result in action:
                    self.do_command(action[result], message)

            #run sibling actions in parallel    
            action_thread = threading.Thread(target=do_action_parallel)
            action_thread.start()


def initialize_command_store(settings_path=""):
    command_store = dbm.open(settings_path + COMMAND_DB, 'c')
    with open(settings_path + DEFAULT_COMMAND_FILE) as f:
        default_commands = json.load(f)
    for key, value in default_commands.items():
        command_store[key] = json.dumps(value)

    return command_store


def initialize_config_store(settings_path=""):
    config_store = dbm.open(settings_path + CONFIG_DB, 'c')
    with open(settings_path + DEFAULT_CONFIG_FILE) as f:
        default_config = json.load(f)
    for key, value in default_config.items():
        config_store[key] = value

    return config_store
