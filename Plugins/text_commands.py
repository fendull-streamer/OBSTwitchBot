import json

def shutdown(bot):
    pass

def chat(bot, message, args):
    
    try:
        response = args['response']

        built_response = message_builder(message, response)

        bot.bot.bot.send_to_channel(built_response, message['channel'])

        return 'Success'
    except Exception as e:
        print('chat failed')
        print(e)
        return 'Failure'

def add(bot, message, args):
    split_message = message['text'].split(' ')
    if len(split_message) < 3:
        return 'InvalidMessage'

    command_name = split_message[1]

    if command_name in bot.bot.command_store:
        
        command = bot.bot.command_store[command_name]
        if len(command) > 0:
            return 'CommandAlreadyExists'
    
    new_text = ' '.join(split_message[2:])
    bot.bot.command_store[command_name] = json.dumps({
        "actions": [
            {
                "name": "text_commands.chat",
                "args": {
                    "response": new_text
                }
            }
        ],
        "type": "text"
    })
    print(bot.bot.command_store[command_name])
    return 'Success'

def edit(bot, message, args):

    split_message = message['text'].split(' ')
    if len(split_message) < 3:
        return 'InvalidMessage'

    command_name = split_message[1]

    if not command_name in bot.bot.command_store:
        return 'CommandDoesNotExist'
    command = bot.bot.command_store[command_name]
    if len(command) < 1:
        return 'CommandDoesNotExist'
    command = json.loads(command.decode('utf-8'))
    if not 'type' in command:
        return 'InvalidCommandType'
    if not command['type'] == 'text':
        return 'InvalidCommandType'

    new_text = ' '.join(split_message[2:])
    bot.bot.command_store[command_name] = json.dumps({
        "actions": [
            {
                "name": "text_commands.chat",
                "args": {
                    "response": new_text
                }
            }
        ],
        "type": "text"
    })
    return 'Success'
    
def delete(bot, message, args):
    
    split_message = message['text'].split(' ')
    if len(split_message) < 2:
        return 'InvalidMessage'

    command_name = split_message[1]
    if command_name in bot.bot.command_store:
        command = bot.bot.command_store[command_name]
        if len(command) > 0:
            command = json.loads(command.decode('utf-8'))
            if not 'type' in command:
                return 'InvalidCommandType'
            if not command['type'] == 'text':
                return 'InvalidCommandType'
    try:
        del bot.bot.command_store[command_name]
    except Exception as e:
        print("Command '{}' does not exist".format(command_name))
        print(e)
        return 'Failure'
    return 'Success'

def message_builder(message, response):
    split_message = message['text'].split(' ')
    for i in range(len(split_message)):
        message['arg'+ str(i)] = split_message[i]
    idx = 0
    start_idx = 0
    end_idx = 0
    while idx < len(response):
        if response[idx] == "{":
            start_idx = idx
            while idx < len(response):
                if response[idx] == "}":
                    template = response[start_idx + 1: idx]
                    if template in message:
                        response = response[0:start_idx] + message[template] + response[idx + 1:]
                        idx = idx + len(message[template]) - (idx - start_idx + 1)
                    break 
                idx = idx + 1
        idx = idx + 1                

    return response