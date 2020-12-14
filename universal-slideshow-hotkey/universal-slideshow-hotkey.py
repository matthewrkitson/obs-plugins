import obspython as obs

class Hotkey:
    def __init__(self, _id, description, callback, obs_settings):
        self.description = description
        self.obs_data = obs_settings
        self.hotkey_id = obs.OBS_INVALID_HOTKEY_ID
        self.hotkey_saved_key = None
        self.callback = callback
        self._id = _id

        self.load_hotkey()
        self.register_hotkey()
        self.save_hotkey()

    def register_hotkey(self):
        obs.script_log(obs.LOG_DEBUG, f"Registering hotkey {self._id}")
        self.hotkey_id = obs.obs_hotkey_register_frontend("htk_id" + str(self._id), self.description, self.callback)
        obs.obs_hotkey_load(self.hotkey_id, self.hotkey_saved_key)

    def unregister_hotkey(self):
        obs.script_log(obs.LOG_DEBUG, f"Unregistering hotkey {self._id}")
        obs.obs_hotkey_unregister(self.callback)

    def load_hotkey(self):
        obs.script_log(obs.LOG_DEBUG, f"Loading hotkey {self._id}")
        self.hotkey_saved_key = obs.obs_data_get_array(self.obs_data, "htk_id" + str(self._id))
        obs.obs_data_array_release(self.hotkey_saved_key)

    def save_hotkey(self):
        obs.script_log(obs.LOG_DEBUG, f"Saving hotkey {self._id}")
        self.hotkey_saved_key = obs.obs_hotkey_save(self.hotkey_id)
        obs.obs_data_set_array(self.obs_data, "htk_id" + str(self._id), self.hotkey_saved_key)
        obs.obs_data_array_release(self.hotkey_saved_key)

def script_description():
    return "Allows registration of a single hotkey to advance any slideshow. "

def script_update(settings):
    pass

def script_defaults(settings):
    pass

ush_active_next_hotkey = None
ush_active_back_hotkey = None
ush_active_reset_hotkey = None
ush_showing_inactive_next_hotkey = None
ush_showing_inactive_back_hotkey = None
ush_showing_inactive_reset_hotkey = None

def script_load(settings):
    # Register six hotkey callbacks:
    # One each for "active" and "showing but not active" of:
    #  - next
    #  - prevous
    #  - restart
    # 
    #  - A source is only considered active if it’s being shown on the final mix
    #  - A source is considered showing if it’s being displayed anywhere at all, whether on a display context or on the final output

    global ush_active_next_hotkey
    global ush_active_back_hotkey
    global ush_active_reset_hotkey
    global ush_showing_inactive_next_hotkey
    global ush_showing_inactive_back_hotkey
    global ush_showing_inactive_reset_hotkey

    obs.script_log(obs.LOG_DEBUG, "Loading universal slideshow hotkey script")
    ush_active_next_hotkey = Hotkey("ush_active_next", "Active slideshow: Next", ush_active_next, settings)
    ush_active_back_hotkey = Hotkey("ush_active_back", "Active slideshow: Back", ush_active_back, settings)
    ush_active_reset_hotkey = Hotkey("ush_active_reset", "Active slideshow: Reset", ush_active_reset, settings)
    ush_showing_inactive_next_hotkey = Hotkey("ush_showing_inactive_next", "Showing but not active slideshow: Next", ush_showing_inactive_next, settings)
    ush_showing_inactive_back_hotkey = Hotkey("ush_showing_inactive_back", "Showing but not active slideshow: Back", ush_showing_inactive_back, settings)
    ush_showing_inactive_reset_hotkey = Hotkey("ush_showing_inactive_reset", "Showing but not active slideshow: Reset", ush_showing_inactive_reset, settings)

def script_unload():
    obs.script_log(obs.LOG_DEBUG, "Unoading universal slideshow hotkey script")
    ush_active_next_hotkey.unregister_hotkey()
    ush_active_back_hotkey.unregister_hotkey()
    ush_active_reset_hotkey.unregister_hotkey()
    ush_showing_inactive_next_hotkey.unregister_hotkey()
    ush_showing_inactive_back_hotkey.unregister_hotkey()
    ush_showing_inactive_reset_hotkey.unregister_hotkey()

def script_save(settings):
    ush_active_next_hotkey.save_hotkey()
    ush_active_back_hotkey.save_hotkey()
    ush_active_reset_hotkey.save_hotkey()
    ush_showing_inactive_next_hotkey.save_hotkey()
    ush_showing_inactive_back_hotkey.save_hotkey()
    ush_showing_inactive_reset_hotkey.save_hotkey()

def active(source):
    return obs.obs_source_active(source)

def showing_but_inactive(source):
    return obs.obs_source_showing(source) and not obs.obs_source_active(source)

def next(source):
    obs.obs_source_media_next(source)

def back(source):
    obs.obs_source_media_previous(source)

def reset(source):
    obs.obs_source_media_restart(source)

def ush_active_next(pressed):
    obs.script_log(obs.LOG_DEBUG, "ush_active_next callback received: pressed=" + str(pressed))
    process_key(pressed, active, next)

def ush_active_back(pressed):
    obs.script_log(obs.LOG_DEBUG, "ush_active_back callback received: pressed=" + str(pressed))
    process_key(pressed, active, back)

def ush_active_reset(pressed):
    obs.script_log(obs.LOG_DEBUG, "ush_active_reset callback received: pressed=" + str(pressed))
    process_key(pressed, active, reset)

def ush_showing_inactive_next(pressed):
    obs.script_log(obs.LOG_DEBUG, "ush_showing_inactive_next callback received: pressed=" + str(pressed))
    process_key(pressed, showing_but_inactive, next)

def ush_showing_inactive_back(pressed):
    obs.script_log(obs.LOG_DEBUG, "ush_showing_inactive_back callback received: pressed=" + str(pressed))
    process_key(pressed, showing_but_inactive, back)

def ush_showing_inactive_reset(pressed):
    obs.script_log(obs.LOG_DEBUG, "ush_showing_inactive_reset callback received: pressed=" + str(pressed))
    process_key(pressed, showing_but_inactive, reset)

def process_key(pressed, filter, action):
    if not pressed: 
        return
    
    obs.script_log(obs.LOG_DEBUG, "Processing hotkey")
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            source_name = obs.obs_source_get_name(source)
            if source_id == "slideshow" and filter(source):
                obs.script_log(obs.LOG_DEBUG, "Performing " + action.__name__ + " on " + source_id + " " + source_name)
                action(source)


        obs.source_list_release(sources)