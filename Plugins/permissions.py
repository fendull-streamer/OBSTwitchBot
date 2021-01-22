import time
import dbm
import json

PERMISSIONS_DB = "PERMISSIONS"
PERMISSIONS_DEFAULT = "PERMISSIONS.json"
permissions_store = {}

def setup(bot):
    settings_path = bot.settings_path
    plugins_path = bot.plugins_path
    permissions_store = dbm.open(settings_path + PERMISSIONS_DB, 'c')
    with open(settings_path + plugins_path + "\\" + PERMISSIONS_DEFAULT) as f:
        default_commands = json.load(f)
    for key, value in default_commands.items():
        permissions_store[key] = json.dumps(value)

def shutdown(bot):
    pass

def has_permission(bot, message, args):
    permission_name = args['permission_name'].lower()
    user = message['sender']

    super_users = json.loads(permissions_store['super_user'].decode('utf-8'))
    if user.lower() in super_users:
        print("Super uset")
        return 'Success'

    if permission_name in permissions_store:
        permissions = permissions_store[permission_name]
        if len(permissions) > 0:
            permissions = json.loads(permissions.decode('utf-8'))
            if user in permissions:
                if time.time() < permissions[user]:
                    return 'Success'
                del permissions[user]
                permissions_store[permission_name] = json.dumps(permissions)

    return 'Failure'


def set_permission(bot, message, args):
    split_message = message['text']
    if len(split_message) < 4:
        return "InvalidMessage"
    permission_name = split_message[2].lower()
    if permission_name == "superuser":
        return 'InvalidPermission'
    permission_user = split_message[1].lower()
    permission_time = split_message[3].lower()
    seconds_per_unit = {
        "h": 60*60,
        "d": 60*60*24,
        "s": 1,
        "m": 60
    }
    try:
        time_amount = int(permission_time[0:-1])
        time_multiplier = seconds_per_unit[permission_time[-1]]
        save_permission_until = time.time() + time_amount * time_multiplier
    except Exception as e:
        print("failed to parse time unit")
        print(e)
        return "InvalidTimeUnit"
    
    if permission_name in permissions_store:
        permissions = permissions_store[permission_name]
        if len(permissions) > 0:
            permissions = json.loads(permissions.decode('utf-8'))
            permissions[permission_user] = save_permission_until
            permissions_store[permission_name] = json.dumps(permissions)
            return "Success"
    permissions_store[permission_name] = json.dumps({
        permission_user: save_permission_until
    })
    return 'Success'


    