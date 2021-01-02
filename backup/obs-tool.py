import os
import wx

import backup
import obs
import backup_ui

class ObsToolFrame(wx.Frame):
    def __init__(self, title, backup, obs):
        super().__init__(parent=None, title=title)

        panel = backup_ui.ObsBackupPanel(self, backup, obs)

        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(wx.StaticText(self, label="OBS Backup Tool"), 0, wx.ALIGN_CENTER | wx.ALL, 10)
        frame_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 5) 
        self.SetSizerAndFit(frame_sizer)

if __name__ == "__main__":
    app = wx.App()
    backup = backup.Backup(os.path.expanduser("~/obs-backups"), os.path.expanduser("~/.config/obs-studio"))
    obs = obs.Obs()
    frame = ObsToolFrame(title="OBS Backup Tool", backup=backup, obs=obs)
    frame.Show()

    app.MainLoop()