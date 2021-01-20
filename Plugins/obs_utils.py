import obspython as obs
import time

DELAY = 10
last_scene_change = {"t": 0}
def setup(bot):
    last_scene_change["t"] = time.time()

def shutdown(bot):
    pass

def change_to_scene(bot, message, args):
    time_to_wait = time.time() - last_scene_change["t"]
    last_scene_change["t"] = time.time()
    if time_to_wait < DELAY:
        message['ttw'] = "{:.1f}".format(time_to_wait)
        return "CommandToSoon"
    scene_name = args['scene']
    scenes = obs.obs_frontend_get_scenes()
    for scene in scenes:
        print(obs.obs_source_get_name(scene))
        if obs.obs_source_get_name(scene) == scene_name:

            current_scene = obs.obs_frontend_get_current_scene()
            scenes.remove(current_scene)
            obs.obs_frontend_set_current_scene(scene)
    return 'Success'
    