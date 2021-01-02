import os
import wx

import backup.backup
import backup.backup_ui
import backup.obs

class ObsToolFrame(wx.Frame):
    def __init__(self, title, backuper, obs):
        super().__init__(parent=None, title=title)

        panel = backup.backup_ui.ObsBackupPanel(self, backuper, obs)

        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(wx.StaticText(self, label="OBS Backup Tool"), 0, wx.ALIGN_CENTER | wx.ALL, 10)
        frame_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 5) 
        self.SetSizerAndFit(frame_sizer)

if __name__ == "__main__":
    app = wx.App()
    backuper = backup.backup.Backup(os.path.expanduser("~/obs-backups"), os.path.expanduser("~/.config/obs-studio"))
    obs = backup.obs.Obs()
    frame = ObsToolFrame(title="OBS Backup Tool", backuper=backuper, obs=obs)
    frame.Show()

    app.MainLoop()