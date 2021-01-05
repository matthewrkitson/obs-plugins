import os
import wx

import backup.backup
import backup.backup_ui
import backup.obs
import bulkrename.bulkrename_ui

class ObsToolFrame(wx.Frame):
    def __init__(self, title, backuper, obs):
        super().__init__(parent=None, title=title)

        notebook = wx.Notebook(self)

        backup_tab = backup.backup_ui.ObsBackupPanel(notebook, backuper, obs)
        rename_tab = bulkrename.bulkrename_ui.BulkRenamePanel(notebook)

        notebook.AddPage(rename_tab, "Bulk rename")
        notebook.AddPage(backup_tab, "Backup and Restore")

        notebook_sizer = wx.FlexGridSizer(cols=1)
        notebook_sizer.SetFlexibleDirection(wx.BOTH)
        notebook_sizer.AddGrowableCol(idx=0, proportion=1)
        notebook_sizer.AddGrowableRow(idx=0, proportion=1)
        notebook_sizer.Add(notebook, proportion=0, flag=wx.EXPAND | wx.ALL, border=5) 

        self.SetSizerAndFit(notebook_sizer)


if __name__ == "__main__":
    app = wx.App()
    backuper = backup.backup.Backup(os.path.expanduser("~/obs-backups"), os.path.expanduser("~/.config/obs-studio"))
    obs = backup.obs.Obs()
    frame = ObsToolFrame(title="OBS Backup Tool", backuper=backuper, obs=obs)
    frame.Show()

    app.MainLoop()