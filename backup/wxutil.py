import wx

def exception_handler(func):
    def inner_function(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except Exception as error:
            # Not much more we can do here. 
            # TODO: Add logging? 
            # https://github.com/matthewrkitson/obs-plugins/issues/5
            wx.MessageBox(f"{error}", "An error occurred", wx.OK, self)

    return inner_function
