import psutil

class Obs:
    def __init__(self):
        pass

    def is_running(self):
        try:
            return any([proc.name().lower() == "obs" for proc in psutil.process_iter()])
        except:
            return False