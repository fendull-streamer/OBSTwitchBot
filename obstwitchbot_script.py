from obstwitchbot import *
import obspython as obs
import time
import os
import importlib.util
BOT_PATH = "C:\\Users\\johnc\\Documents\\NewNotFendull\\"

spec = importlib.util.spec_from_file_location("notfendull", BOT_PATH + "notfendull.py")
nf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nf)
bot = nf.OBSTwitchBot(settings_path=BOT_PATH)

def script_load(settings):
	try:
		time.sleep(1)
		bot.start()
	except:
		pass

def script_unload():
	bot.stop()

def script_description():
	return "The official Rosebot for managing easter eggs on KayeRoseTV's Twitch Channel"

def script_update(settings):

	access_token  = obs.obs_data_get_string(settings, "access_token")
	nickname = obs.obs_data_get_string(settings, "nickname")
	print("Nickname: {}".format(nickname))
	if access_token is not None:
		bot.set_access_token(access_token)
	if nickname is not None:
		bot.set_nickname(nickname)

def script_properties():
	props = obs.obs_properties_create()

	obs.obs_properties_add_text(props, "access_token", "Access Token (ex: 'oauth:xxxxxxxxxxxxxxx')", obs.OBS_TEXT_DEFAULT)
	obs.obs_properties_add_text(props, "nickname", "Bot Account Name", obs.OBS_TEXT_DEFAULT)

	return props

def change_to_scene(scene_name):

	scenes = obs.obs_frontend_get_scenes()
	for scene in scenes:
		print(obs.obs_source_get_name(scene))
		if obs.obs_source_get_name(scene) == scene_name:

			current_scene = obs.obs_frontend_get_current_scene()
			scenes.remove(current_scene)
			obs.obs_frontend_set_current_scene(scene)
