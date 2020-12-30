import os
import wx

import backup
import obs
import backup_ui

if __name__ == "__main__":
    app = wx.App()
    backup = backup.Backup(os.path.expanduser("~/obs-backups"), os.path.expanduser("~/.config/obs-studio"))
    obs = obs.Obs()
    frame = backup_ui.ObsBackupFrame(title="OBS Backup Tool", backup=backup, obs=obs)
    frame.Show()

    app.MainLoop()