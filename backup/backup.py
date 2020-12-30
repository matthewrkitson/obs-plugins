import datetime
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

    def backup(self, backup_name, confirm_continue=None):
        # The confirm_continue callback will be passed the backup name and
        # destination path if the destination backup already exists.
        # Return True to confirm that the overwrite should continue. 
        safe_backup_name = self._sanitise(backup_name)
        destination = os.path.join(self.backups_folder, safe_backup_name)

        if os.path.isdir(destination) and confirm_continue and not confirm_continue(backup_name, destination):
            return False

        process = subprocess.run(
            ["rsync", "-avP", self.obs_folder, destination],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)

        if process.returncode != 0:
            raise ChildProcessError(f"rsync exit code: {process.returncode}\n\n{process.stdout}\n\n{process.stderr}")

        return True

    def get_backup_DirEntries(self):
        return [ f for f in os.scandir(self.backups_folder) if f.is_dir() ]

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
        # https://github.com/matthewrkitson/obs-plugins/issues/3
        return backup_name

import wx

class ObsBackupFrame(wx.Frame):
    def __init__(self, title, backup, obs):
        super().__init__(parent=None, title=title)

        self.backup = backup
        self.obs = obs

        panel = wx.Panel(self)

        
        backup_name_lbl = wx.StaticText(panel, label="Create backup")
        self.backup_name_tb = wx.TextCtrl(panel, size=(500, -1))
        self.backup_name_tb.Bind(wx.EVT_TEXT, self.backup_name_changed)
        self.backup_btn = wx.Button(panel, label="Backup")
        self.backup_btn.Bind(wx.EVT_BUTTON, self.backup_button_clicked)
        self.backup_name_tb.Value = "" # Manually set to update button enabled-ness

        self.backup_sorter = self.name_sorter
        self.column_sorters = [ (self.name_sorter ,1), (self.date_sorter, -1) ] # Tuple is sorter and default direction. 
        self.backup_sorter_direction = 1 # +1 for ascending, -1 for descending.
        self.restore_list_data = list()
        restore_list_lbl = wx.StaticText(panel, label="Restore backup")
        self.restore_list_ctrl = wx.ListCtrl(panel, wx.ID_ANY, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.restore_list_ctrl.InsertColumn(0, "Name", width=300)
        self.restore_list_ctrl.InsertColumn(1, "Date", width=200)
        self.restore_list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.restore_list_item_selection_changed)
        self.restore_list_ctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.restore_list_item_selection_changed)
        self.restore_list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.restore_list_item_activated)
        self.restore_list_ctrl.Bind(wx.EVT_LIST_COL_CLICK, self.restore_list_column_clicked)
        self.restore_btn = wx.Button(panel, label="Restore")
        self.restore_btn.Bind(wx.EVT_BUTTON, self.restore_button_clicked)
        self.populate_restore_list(self.backup)
        self.restore_list_item_selection_changed(None) # Update button enabled-ness

        empty_cell = (0, 0)
        grid_sizer = wx.FlexGridSizer(2, vgap=10, hgap=10)
        grid_sizer.AddMany([
            (backup_name_lbl, 0), empty_cell,
            (self.backup_name_tb, 1, wx.EXPAND), (self.backup_btn, 0), 
            (restore_list_lbl, 0), empty_cell,
            (self.restore_list_ctrl, 1, wx.EXPAND), (self.restore_btn, 0)
        ])

        grid_sizer.SetFlexibleDirection(wx.BOTH)
        grid_sizer.AddGrowableCol(idx=0, proportion=3)
        grid_sizer.AddGrowableRow(idx=3, proportion=3)

        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(wx.StaticText(self, label="OBS Backup Tool"), 0, wx.ALIGN_CENTER | wx.ALL, 10)
        frame_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 5) 
 
        panel.SetSizerAndFit(grid_sizer)
        self.SetSizerAndFit(frame_sizer)

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

    def confirm_overwrite(self):
        return (
            lambda backup_name, destination:
                wx.MessageBox(
                    f"Backup {backup_name} already exists. Do you want to overwrite it? ", 
                    "Backup exists", 
                    wx.YES | wx.NO,
                    self) == wx.YES
        )

    def name_sorter(self, item1_index, item2_index):
        item1 = self.restore_list_data[item1_index]
        item2 = self.restore_list_data[item2_index]
        if item1.name == item2.name: return 0
        if item1.name > item2.name: return 1 * self.backup_sorter_direction
        if item1.name < item2.name: return -1 * self.backup_sorter_direction
        
        raise ValueError(f"Could not compare {item1.name} and {item2.name}")

    def date_sorter(self, item1_index, item2_index):
        item1 = self.restore_list_data[item1_index]
        item2 = self.restore_list_data[item2_index]
        if item1.stat().st_ctime == item2.stat().st_ctime: return 0
        if item1.stat().st_ctime > item2.stat().st_ctime: return 1 * self.backup_sorter_direction
        if item1.stat().st_ctime < item2.stat().st_ctime: return -1 * self.backup_sorter_direction

        raise ValueError(f"Could not compare {item1.stat().st_ctime} and {item2.stat().st_ctime}")

    @exception_handler
    def backup_button_clicked(self, event):
        backup_name = self.backup_name_tb.Value

        if self.cancel_because_obs_is_running():
            return

        if self.backup.backup(backup_name, self.confirm_overwrite()):
            wx.MessageBox(f"Created new backup: '{backup_name}'", "Created backup", wx.OK, self)
            self.populate_restore_list(self.backup)

    @exception_handler
    def backup_name_changed(self, event):
        name = event.String.strip()
        if name:
            self.backup_btn.Enable()
        else:
            self.backup_btn.Disable()

    def populate_restore_list(self, backup):
        self.restore_list_ctrl.DeleteAllItems()
        self.restore_list_data.clear()
        for dir_entry in backup.get_backup_DirEntries():
            index = self.restore_list_ctrl.ItemCount
            self.restore_list_data.insert(index, dir_entry)
            self.restore_list_ctrl.InsertItem(index, dir_entry.name)
            self.restore_list_ctrl.SetItem(index, column=1, label=f"{datetime.datetime.fromtimestamp(dir_entry.stat().st_ctime):%Y-%m-%d %H:%M:%S}")
            self.restore_list_ctrl.SetItemData(index, index)

        self.restore_list_ctrl.SortItems(self.backup_sorter)

    @exception_handler
    def restore_list_item_selection_changed(self, event):
        if self.restore_list_ctrl.SelectedItemCount:
            self.restore_btn.Enable()
        else:
            self.restore_btn.Disable()

    @exception_handler
    def restore_list_item_activated(self, event):
        self.restore_backup()

    @exception_handler
    def restore_list_column_clicked(self, event):
        (sorter, default_direction) = self.column_sorters[event.Column]
        if sorter == self.backup_sorter:
            self.backup_sorter_direction = -self.backup_sorter_direction
        else:
            self.backup_sorter_direction = default_direction
        self.backup_sorter = sorter

        self.restore_list_ctrl.SortItems(sorter)

    @exception_handler
    def restore_button_clicked(self, event):
        self.restore_backup()

    def restore_backup(self):
        if self.restore_list_ctrl.SelectedItemCount != 1:
            wx.MessageBox(self, f"Please select a backup to restore", "Select backup", wx.OK, self)
            return

        if self.cancel_because_obs_is_running():
            return
        
        selection_index = self.restore_list_ctrl.GetFirstSelected()
        data_index = self.restore_list_ctrl.GetItemData(selection_index)
        selection = self.restore_list_data[data_index]
        self.backup.restore(selection.name)
        wx.MessageDialog(self, f"Backup '{selection.name}' has been restored").ShowModal()

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
