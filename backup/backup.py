import os
import psutil
import subprocess
import wx

class Obs:
    def __init__(self):
        pass

    def is_running(self):
        try:
            return any([proc.name().lower() == "obs" for proc in psutil.process_iter()])
        except:
            return False


class Backup:
    def __init__(self, backups_folder, obs_folder):
        self.backups_folder = backups_folder.rstrip("/")
        self.obs_folder = obs_folder.rstrip("/")
        self.obs_foldername = os.path.basename(self.obs_folder)

        if not os.path.isdir(self.backups_folder):
            os.makedirs(self.backups_folder)

    def backup(self, backup_name):
        #TODO: Check whether backup already exists.
        safe_backup_name = self._sanitise(backup_name)
        destination = os.path.join(self.backups_folder, safe_backup_name)
        process = subprocess.run(
            ["rsync", "-avP", self.obs_folder, destination],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)

        if process.returncode != 0:
            raise ChildProcessError(f"rsync exit code: {process.returncode}\n\n{process.stdout}\n\n{process.stderr}")

    def get_backups(self):
        return [ f.name for f in os.scandir(self.backups_folder) if f.is_dir() ]

    def restore(self, backup_name):
        # Backup name is expected to be the name of the folder only (not the full path to the backup)
        backup_folder = os.path.join(self.backups_folder, backup_name).rstrip("/")
        process = subprocess.run(
            ["rsync", "-avP", f"{backup_folder}/{self.obs_foldername}/", self.obs_folder],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)

        if process.returncode != 0:
            raise ChildProcessError(f"rsync exit code: {process.returncode}\n\n{process.stdout}\n\n{process.stderr}")
        pass

    def _sanitise(self, backup_name):
        # TODO: implement some kind of sanitisation...
        return backup_name

class ObsBackupFrame(wx.Frame):
    def __init__(self, title, backup, obs):
        super().__init__(parent=None, title=title)

        # This Frame contains a title and a panel arranged in a vertical BoxSizer
        #
        #  ---------------
        #  |    Title    |
        #  | ----------- |
        #  |    Panel    |
        #  ---------------
        #
        # The panel is a 3x2 grid. Each row has a label, a control, and a button. 
        #
        # The central control should stretch with the grid. 
        #
        # The control should start off three times bigger than the label and/or
        # the button, but the best I can do is set an initial size of the 
        # button to be 300 pixels wide. 
        #

        self.backup = backup
        self.obs = obs

        panel = wx.Panel(self)

        grid_sizer = wx.FlexGridSizer(3, vgap=10, hgap=10)
        
        backup_name_lbl = wx.StaticText(panel, label="Backup name: ")
        self.backup_name_tb = wx.TextCtrl(panel, size=(300, -1))
        self.backup_btn = wx.Button(panel, label="Backup")
        self.backup_btn.Bind(wx.EVT_BUTTON, self.backup_button_clicked)

        restore_list_lbl = wx.StaticText(panel, label="Backup to restore: ")
        self.restore_list_dd = wx.ComboBox(panel, choices=["one", "two", "three"], style=wx.CB_READONLY)
        self.restore_list_dd.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.restore_combobox_expanded)
        self.restore_btn = wx.Button(panel, label="Restore")
        self.restore_btn.Bind(wx.EVT_BUTTON, self.restore_button_clicked)

        grid_sizer.AddMany([
            (backup_name_lbl, 0), (self.backup_name_tb, 1, wx.EXPAND), (self.backup_btn, 0), 
            (restore_list_lbl, 0), (self.restore_list_dd, 1, wx.EXPAND), (self.restore_btn, 0)
        ])

        grid_sizer.SetFlexibleDirection(wx.BOTH)
        grid_sizer.AddGrowableCol(1, 3)

        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(wx.StaticText(self, label="OBS Backup Tool"), 0, wx.ALIGN_CENTER | wx.ALL, 10)
        frame_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 5) 
        panel.SetSizerAndFit(grid_sizer)
        self.SetSizerAndFit(frame_sizer)

    def backup_button_clicked(self, event):
        backup_name = self.backup_name_tb.Value
        if not backup_name:
            # TODO: Set a validator on the button so it's only enabled when a valid name is entered.
            wx.MessageDialog(self, f"Please enter a name for the backup").ShowModal()
            return

        if self.cancel_because_obs_is_running():
            return

        self.backup.backup(backup_name)
        wx.MessageDialog(self, f"Created new backup: '{backup_name}'").ShowModal()

    def restore_button_clicked(self, event):
        selection = self.restore_list_dd.StringSelection
        if not selection:
            wx.MessageDialog(self, f"Please select a backup to restore").ShowModal()
            return
        
        if self.cancel_because_obs_is_running():
            return

        self.backup.restore(selection)
        wx.MessageDialog(self, f"Backup '{selection}' has been restored").ShowModal()

    def restore_combobox_expanded(self, event):
        available_backups = self.backup.get_backups()
        self.restore_list_dd.Set(available_backups)

    def cancel_because_obs_is_running(self):
        if self.obs.is_running():
            dialog_result = wx.MessageBox("Warning: OBS is still running. Are you sure you want to continue?", "OBS still running", wx.YES | wx.NO, self)
            if dialog_result == wx.NO:
                return True
        else:
            return False



if __name__ == "__main__":
    app = wx.App()
    backup = Backup(os.path.expanduser("~/obs-backups"), os.path.expanduser("~/.config/obs-studio"))
    obs = Obs()
    frame = ObsBackupFrame(title="OBS Backup Tool", backup=backup, obs=obs)
    frame.Show()

    app.MainLoop()