import datetime
import wx

class ObsToolFrame(wx.Frame):
    def __init__(self, title, backup, obs):
        super().__init__(parent=None, title=title)

        panel = ObsBackupPanel(self, backup, obs)

        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(wx.StaticText(self, label="OBS Backup Tool"), 0, wx.ALIGN_CENTER | wx.ALL, 10)
        frame_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 5) 
        self.SetSizerAndFit(frame_sizer)

class ObsBackupPanel(wx.Panel):
    def __init__(self, parent, backup, obs):
        super().__init__(parent=parent)

        self.backup = backup
        self.obs = obs
    
        backup_name_lbl = wx.StaticText(self, label="Create backup")
        self.backup_name_tb = wx.TextCtrl(self, size=(500, -1))
        self.backup_name_tb.Bind(wx.EVT_TEXT, self.backup_name_changed)
        self.backup_btn = wx.Button(self, label="Backup")
        self.backup_btn.Bind(wx.EVT_BUTTON, self.backup_button_clicked)
        self.backup_name_tb.Value = "" # Manually set to update button enabled-ness

        self.backup_sorter = self.name_sorter
        self.column_sorters = [ (self.name_sorter ,1), (self.date_sorter, -1) ] # Tuple is sorter and default direction. 
        self.backup_sorter_direction = 1 # +1 for ascending, -1 for descending.
        self.restore_list_data = list()
        restore_list_lbl = wx.StaticText(self, label="Restore backup")
        self.restore_list_ctrl = wx.ListCtrl(self, wx.ID_ANY, style=wx.LC_REPORT)
        self.restore_list_ctrl.InsertColumn(0, "Name", width=300)
        self.restore_list_ctrl.InsertColumn(1, "Date", width=200)
        self.restore_list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.restore_list_item_selection_changed)
        self.restore_list_ctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.restore_list_item_selection_changed)
        self.restore_list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.restore_list_item_activated)
        self.restore_list_ctrl.Bind(wx.EVT_LIST_COL_CLICK, self.restore_list_column_clicked)

        self.restore_btn = wx.Button(self, label="Restore")
        self.restore_btn.Bind(wx.EVT_BUTTON, self.restore_button_clicked)
        self.delete_btn = wx.Button(self, label="Delete")
        self.delete_btn.Bind(wx.EVT_BUTTON, self.delete_button_clicked)

        empty_cell = (0, 0)
        button_sizer = wx.BoxSizer(wx.VERTICAL)
        button_sizer.Add(self.restore_btn, 0, wx.EXPAND)
        button_sizer.AddSpacer(5)
        button_sizer.Add(self.delete_btn, 0, wx.EXPAND)

        self.populate_restore_list(self.backup)
        self.restore_list_item_selection_changed(None) # Update button enabled-ness

        grid_sizer = wx.FlexGridSizer(2, vgap=10, hgap=10)
        grid_sizer.AddMany([
            (backup_name_lbl, 0), empty_cell,
            (self.backup_name_tb, 1, wx.EXPAND), (self.backup_btn, 0), 
            (restore_list_lbl, 0), empty_cell,
            (self.restore_list_ctrl, 1, wx.EXPAND), (button_sizer, 0)
        ])

        grid_sizer.SetFlexibleDirection(wx.BOTH)
        grid_sizer.AddGrowableCol(idx=0, proportion=3)
        grid_sizer.AddGrowableRow(idx=3, proportion=3)
 
        self.SetSizerAndFit(grid_sizer)

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
        self.restore_list_item_selection_changed(None)

    @exception_handler
    def restore_list_item_selection_changed(self, event):
        enable_restore_button = self.restore_list_ctrl.SelectedItemCount == 1
        enable_delete_button = self.restore_list_ctrl.SelectedItemCount >= 1

        self.restore_btn.Enable(enable_restore_button)
        self.delete_btn.Enable(enable_delete_button)

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
            wx.MessageBox(f"Please select a backup to restore", "Select backup", wx.OK, self)
            return

        if self.cancel_because_obs_is_running():
            return
        
        selected_item_index = self.restore_list_ctrl.GetFirstSelected()
        data_index = self.restore_list_ctrl.GetItemData(selected_item_index)
        selection = self.restore_list_data[data_index]
        self.backup.restore(selection.name)
        wx.MessageBox(f"Backup '{selection.name}' has been restored", "Backup restored", wx.OK, self)

    def delete_button_clicked(self, event):
        backup_count = self.restore_list_ctrl.SelectedItemCount
        sure_response = wx.MessageBox(f"Are you sure you want to delete {backup_count} backup(s)?", "Are you sure?", wx.YES | wx.NO, self)
        if sure_response == wx.NO:
            return

        failures = list()
        selected_item_index = self.restore_list_ctrl.GetFirstSelected()
        while selected_item_index != -1:
            data_index = self.restore_list_ctrl.GetItemData(selected_item_index)
            selection = self.restore_list_data[data_index]
            try:
                self.backup.delete(selection.name)
            except:
                failures.append(selection.name)

            selected_item_index = self.restore_list_ctrl.GetNextSelected(selected_item_index)

        if len(failures) > 0:
            wx.MessageBox(f"Failed to delete {len(failures)} backup(s)\n\n" + "\n".join(failures), "Deletion failed", wx.OK, self)

        self.populate_restore_list(self.backup)
        

    def cancel_because_obs_is_running(self):
        if self.obs.is_running():
            dialog_result = wx.MessageBox("Warning: OBS is still running. Are you sure you want to continue?", "OBS still running", wx.YES | wx.NO, self)
            if dialog_result == wx.NO:
                return True
        else:
            return False