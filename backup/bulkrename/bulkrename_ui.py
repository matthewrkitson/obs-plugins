import os
import re
import wx

import wxutil

class BulkRenamePanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent=parent)

        folder_lbl = wx.StaticText(parent=self, label="Folder")
        self.folder_tb = wx.TextCtrl(parent=self)
        self.folder_tb.Bind(wx.EVT_KILL_FOCUS, self.folder_textbox_lost_focus)
        folder_browse_btn = wx.Button(parent=self, label="Browse...")
        folder_browse_btn.Bind(wx.EVT_BUTTON, self.folder_browse_button_clicked)

        search_lbl = wx.StaticText(parent=self, label="Path pattern (regex)")
        self.search_tb = wx.TextCtrl(parent=self)
        self.search_tb.Value = "(?i)^(.*)[.]png$"
        self.search_tb.Bind(wx.EVT_TEXT, self.search_pattern_changed)

        replace_lbl = wx.StaticText(parent=self, label="Replacement pattern (regex)")
        self.replace_tb = wx.TextCtrl(parent=self)
        self.replace_tb.Value = "\\1.png"
        self.replace_tb.Bind(wx.EVT_TEXT, self.replace_pattern_changed)

        self.regex_feedback_txt = wx.StaticText(parent=self, label="")

        self.replacements_lc = wx.ListCtrl(parent=self, style=wx.LC_REPORT)
        self.replacements_lc.InsertColumn(0, "Original path", width=300)
        self.replacements_lc.InsertColumn(1, "New path", width=300)
        # self.replacements_lc.Bind(wx.EVT_LIST_ITEM_SELECTED, self.replacement_list_item_selection_changed)
        # self.replacements_lc.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.replacement_list_item_selection_changed)
        # self.replacements_lc.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.replacement_list_item_activated)
        # self.replacements_lc.Bind(wx.EVT_LIST_COL_CLICK, self.replacement_list_column_clicked)

        apply_btn = wx.Button(parent=self, label="Apply")
        apply_btn.Bind(wx.EVT_BUTTON, self.apply_button_clicked)

        refresh_btn = wx.Button(parent=self, label="Refresh")
        refresh_btn.Bind(wx.EVT_BUTTON, self.refresh_button_clicked)

        self.recurse_cb = wx.CheckBox(parent=self, label="Include sub-folders")
        self.recurse_cb.Value = True
        self.recurse_cb.Bind(wx.EVT_CHECKBOX, self.recurse_checkbox_changed)

        grid_sizer = wx.GridBagSizer(vgap=10, hgap=10)
        
        grid_sizer.Add(folder_lbl, wx.GBPosition(0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.folder_tb, wx.GBPosition(0, 1), flag=wx.EXPAND)
        grid_sizer.Add(folder_browse_btn, wx.GBPosition(0, 2), flag=wx.ALIGN_RIGHT | wx.FIXED_MINSIZE)
        grid_sizer.Add(self.recurse_cb, wx.GBPosition(1, 0), wx.GBSpan(1, 3))

        grid_sizer.Add(search_lbl, wx.GBPosition(2, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.search_tb, wx.GBPosition(2, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
    
        grid_sizer.Add(replace_lbl, wx.GBPosition(3, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.replace_tb, wx.GBPosition(3, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)

        grid_sizer.Add(self.regex_feedback_txt, wx.GBPosition(4, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
    
        grid_sizer.Add(self.replacements_lc, wx.GBPosition(5, 0), wx.GBSpan(1, 3), wx.EXPAND)
    
        box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        box_sizer.Add(apply_btn, proportion=0, flag=wx.RIGHT, border=5)
        box_sizer.Add(refresh_btn, proportion=0, flag=wx.RIGHT, border=5)
        grid_sizer.Add(box_sizer, wx.GBPosition(6, 0))

        grid_sizer.SetFlexibleDirection(wx.BOTH)
        grid_sizer.AddGrowableCol(idx=1, proportion=1)
        grid_sizer.AddGrowableRow(idx=5, proportion=1)

        padding_sizer = wx.BoxSizer(wx.VERTICAL)
        padding_sizer.Add(grid_sizer, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        self.SetSizerAndFit(padding_sizer)
    
    @wxutil.exception_handler
    def folder_browse_button_clicked(self, event):
        dir_dialog = wx.DirDialog(self, "Select a folder")
        if dir_dialog.ShowModal() == wx.ID_CANCEL:
            return

        path = dir_dialog.Path
        self.folder_tb.Value = path
        self.update_file_list()
        self.preview_transform()

    @wxutil.exception_handler
    def folder_textbox_lost_focus(self, event):
        if os.path.isdir(self.folder_tb.Value):
            self.update_file_list()
            self.preview_transform()

    @wxutil.exception_handler
    def recurse_checkbox_changed(self, event):
        self.update_file_list()
        self.preview_transform()

    @wxutil.exception_handler
    def apply_button_clicked(self, event):
        root = self.folder_tb.Value
        for index in range(self.replacements_lc.ItemCount):
            try:
                source_subpath = self.replacements_lc.GetItem(index, col=0).Text
                destination_subpath = self.replacements_lc.GetItem(index, col=1).Text

                source_path = os.path.join(root, source_subpath)
                destination_path = os.path.join(root, destination_subpath)
                
                if destination_path != source_path:
                    destination_folder = os.path.dirname(destination_path)
                    os.makedirs(destination_folder, exist_ok=True)
                    os.rename(source_path, destination_path)
                    self.replacements_lc.SetItem(index, column=0, label=destination_subpath)

            except Exception as error:
                self.replacements_lc.SetItem(index, column=1, label=str(error))

    @wxutil.exception_handler
    def refresh_button_clicked(self, event):
        self.update_file_list()
        self.preview_transform()

    def update_file_list(self):
        recurse = self.recurse_cb.Value
        folder = self.folder_tb.Value

        if not folder:
            return

        file_tuples = []
        if not recurse:
            dirnames = []
            filenames = [ f.name for f in os.scandir(folder) if f.is_file() ]
            file_tuples = [ (folder, dirnames, filenames) ]
        else:
            file_tuples = os.walk(folder)

        filepaths = []
        count = 0
        for (dirpath, dirnames, filenames) in file_tuples:
            for filename in filenames:
                filepaths.append(os.path.join(dirpath, filename)[len(folder):].lstrip(os.path.sep))
                count += 1
                if count > 2999:
                    if recurse: 
                        raise ValueError(f"Too many files found (more than {count}).\n\nTry turning off 'Include sub-folders' to select fewer files.")
                    else:
                        raise ValueError(f"Too many files found (more than {count}).\n\nTry selecting a folder with fewer files.")

        self.replacements_lc.DeleteAllItems()

        index = 0
        for filepath in filepaths:
            self.replacements_lc.InsertItem(index, filepath)
            index += 1

    @wxutil.exception_handler
    def search_pattern_changed(self, event):
        self.preview_transform()

    @wxutil.exception_handler
    def replace_pattern_changed(self, event):
        self.preview_transform()

    def validate_regex(self):
        try:
            regex = re.compile(self.search_tb.Value)
            self.regex_feedback_txt.Label = ""
            self.search_tb.ForegroundColour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
            return regex
        except re.error as error:
            self.regex_feedback_txt.Label = f"Regex error: {error}"
            self.search_tb.ForegroundColour = wx.TheColourDatabase.Find("RED")
            return False

    def preview_transform(self):
        regex = self.validate_regex()
        if regex: 
            replacement_pattern = self.replace_tb.Value
            for index in range(self.replacements_lc.ItemCount):
                new_path = None
                try:
                    original_path = self.replacements_lc.GetItem(index).Text
                    new_path = regex.sub(replacement_pattern, original_path)
                except re.error as error:
                    new_path = str(error)

                self.replacements_lc.SetItem(index, column=1, label=new_path)