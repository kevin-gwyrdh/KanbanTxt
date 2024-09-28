# KanbanTxt - A light todo.txt editor that display the to do list as a kanban board.
# Copyright (C) 2022  KrisNumber24

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  
# If not, see https://github.com/KrisNumber24/KanbanTxt/blob/main/LICENSE.

import os
import pathlib
import re
from datetime import date
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
import tkinter.font as tkFont
import argparse
from idlelib.tooltip import Hovertip
import ctypes
import json


def f_sort_column_by_prio(d):
    return d['priority'] if d['priority'] is not None else 'z'


def f_sort_column_by_order(d):
    return d['index']


def f_sort_column_by_txt(d):
    return d['raw_txt']


def f_sort_column_by_subject(d):
    return d['subject']


def f_sort_column_by_tag(d, tag_name, tag_indicator):
    if len(d[tag_name]) < 1:
        return chr(ord('z') + 1)

    project_tags_copy = []
    for p in d[tag_name]:
        project_tags_copy.append(p[tag_name].casefold())
    project_tags_copy.sort()
    s = ' '.join(project_tags_copy)
    s = s.replace(tag_indicator, '')
    return s


def f_sort_column_by_project(d):
    return f_sort_column_by_tag(d, 'project', '+')


def f_sort_column_by_context(d):
    return f_sort_column_by_tag(d, 'context', '@')


SORT_METHODS = [
    {
        'text': "Task priority",
        'tooltip': 'Sort by task priority:\n'
                   'tasks with priority (A) will be put first, then (B)... up to (Z).\n'
                   'Tasks without set priority will be put last.\n'
                   'Tasks within the same priority will be put in order of their definition in the txt file.',
        'f': f_sort_column_by_prio,
        'rev': False
    },
    {
        'text': "Reversed task priority",
        'tooltip': 'Sort by task reversed priority:\n'
                   'tasks with priority (A) will be put last, before (B)... up to (Z).\n'
                   'Tasks without set priority will be put first.\n'
                   'Tasks within the same priority will be put in reversed order of their definition in the txt file.',
        'f': f_sort_column_by_prio,
        'rev': True
    },
    {
        'text': "Order in txt file",
        'tooltip': 'Tasks are ordered by their definition in the txt file:\n'
                   'if a task is defined earlier in txt than the other, it will appear higher.',
        'f': f_sort_column_by_order,
        'rev': False
    },
    {
        'text': "Reversed order in txt file",
        'tooltip': 'Tasks are ordered in reverse by their definition in the txt file:\n'
                   'if a task is defined later in txt than the other, it will appear higher.',
        'f': f_sort_column_by_order,
        'rev': True
    },
    {
        'text': "Alphabetically by subject",
        'tooltip': "Tasks are ordered lexicographically by their subject.\n"
                   "It won't include priority or other tags defined at the beginning of line in the todo.txt.",
        'f': f_sort_column_by_subject,
        'rev': False
    },
    {
        'text': "Alphabetically by text",
        'tooltip': "Tasks are ordered lexicographically by their definition in the txt file.\n"
                   "It WILL include priority or other tags defined at the beginning of line in the todo.txt.\n"
                    "This is similar to sorting by priority, but the tasks without priority will be sorted alphabetically and not by their order in txt file.",
        'f': f_sort_column_by_txt,
        'rev': False
    },
    {
        'text': "Alphabetically by project",
        'tooltip': "Tasks are ordered lexicographically by their project tags.\n"
                   "If task has multiple project tags, they will be first sorted alphabetically.",
        'f': f_sort_column_by_project,
        'rev': False
    },
    {
        'text': "Alphabetically by context",
        'tooltip': "Tasks are ordered lexicographically by their context tags.\n"
                   "If task has multiple context tags, they will be first sorted alphabetically.",
        'f': f_sort_column_by_context,
        'rev': False
    },
]

class CustomizeViewDialog(simpledialog.Dialog):
    def __init__(self, parent, title,
                 out_show_project,
                 out_show_context,
                 out_show_special_kv_data,
                 out_show_index,
                 out_show_priority,
                 out_show_date,
                 out_show_content,
                 out_sort_method,
                 out_col0_name,
                 out_col1_name,
                 out_col2_name,
                 out_col3_name,
                 out_fontsize,
                 out_ask_for_add,
                 out_ask_for_delete,
                 out_hide_memo,
                 out_hide_button_delete,
                 out_hide_button_add_date,
                 out_hide_buttons_assign_priority,
                 out_hide_buttons_move_to_column,
                 out_hide_buttons_move_line_up_down,
                 ):
        self.show_project = out_show_project
        self.show_context = out_show_context
        self.show_special_kv_data = out_show_special_kv_data
        self.show_index = out_show_index
        self.show_priority = out_show_priority
        self.show_date = out_show_date
        self.show_content = out_show_content
        self.sort_method = out_sort_method
        self.ask_for_add = out_ask_for_add
        self.ask_for_delete = out_ask_for_delete
        self.col_names = [
            out_col0_name,
            out_col1_name,
            out_col2_name,
            out_col3_name,
        ]
        self.font_size = out_fontsize
        self.hide_memo = out_hide_memo
        self.hide_button_delete = out_hide_button_delete
        self.hide_button_add_date = out_hide_button_add_date
        self.hide_buttons_assign_priority = out_hide_buttons_assign_priority
        self.hide_buttons_move_to_column = out_hide_buttons_move_to_column
        self.hide_buttons_move_line_up_down = out_hide_buttons_move_line_up_down
        super().__init__(parent, title)

    def create_checkbox(self, text, tooltip, variable, frame):
        checkbox = tk.Checkbutton(frame, text=text, variable=variable)
        Hovertip(checkbox, tooltip)
        checkbox.pack(anchor=tk.W)

    def create_radiobuttion(self, text, tooltip, variable, value, frame):
        radiobutton = tk.Radiobutton(frame, text=text, variable=variable, value=value)
        Hovertip(radiobutton, tooltip)
        radiobutton.pack(anchor=tk.W)

    def create_text_entry(self, tooltip, variable, frame, col, row):
        entry = tk.Entry(frame, textvariable=variable)
        Hovertip(entry, tooltip)
        entry.grid(row=row, column=col, padx=10, pady=10, sticky=tk.NW)

    def body(self, frame):
        grid_frame = tk.Frame(frame)
        grid_frame.pack(anchor=tk.NW, fill="both")

        row = 0
        frame_colnames = tk.LabelFrame(grid_frame, text="Column names: ")
        frame_colnames.grid(columnspan=3, row=row, column=0, padx=10, pady=10, sticky=tk.NW)

        for i, v in enumerate(self.col_names):
            self.create_text_entry(f"Name of column {i}.", v, frame_colnames, row=row, col=i)

        row = 1
        first_column_frame = tk.Frame(grid_frame)
        first_column_frame.grid(row=row, column=0, padx=10, pady=10, sticky=tk.NW)
        frame_sorting = tk.LabelFrame(first_column_frame, text="Sort tasks in columns by: ")
        frame_sorting.pack()
        for i in range(len(SORT_METHODS)):
            m = SORT_METHODS[i]
            self.create_radiobuttion(m['text'], m['tooltip'], self.sort_method, i, frame_sorting)

        second_column_frame = tk.Frame(grid_frame)
        second_column_frame.grid(row=row, column=1, padx=10, pady=10, sticky=tk.NW)
        frame_show_hide = tk.LabelFrame(second_column_frame, text="Show/hide task cards' elements: ")
        frame_show_hide.pack()
        self.create_checkbox('Priority', 'Show priority of a task on a card', self.show_priority, frame_show_hide)
        self.create_checkbox('Date', 'Show date of a task on a card', self.show_date, frame_show_hide)
        self.create_checkbox('Project', 'Show project labels of a task on a card', self.show_project, frame_show_hide)
        self.create_checkbox('Context', 'Show context labels of a task on a card', self.show_context, frame_show_hide)
        self.create_checkbox('Special k-v data', 'Show special k-v data labels of a task on a card', self.show_special_kv_data, frame_show_hide)
        self.create_checkbox('Index', 'Show line index of a task on a card', self.show_index, frame_show_hide)
        self.create_checkbox('Subject', 'Show the main content of a task on a card', self.show_content, frame_show_hide)

        frame_fontsize = tk.LabelFrame(second_column_frame, text="Font size: ")
        frame_fontsize.pack(fill='x', pady=10)
        fontsize_spinbox = tk.Spinbox(frame_fontsize, from_=4, to=100, textvariable=self.font_size, wrap=True)
        fontsize_spinbox.pack(anchor=tk.W, padx=10, pady=10, fill='x')

        third_column_frame = tk.Frame(grid_frame)
        third_column_frame.grid(row=row, column=2, padx=10, pady=10, sticky=tk.NW)

        frame_hide_editor_elements = tk.LabelFrame(third_column_frame, text="Show editor widgets: ")
        frame_hide_editor_elements.pack()
        self.create_checkbox("Memo", "", self.hide_memo, frame_hide_editor_elements)
        self.create_checkbox("Buttons 'Move to column'", "", self.hide_buttons_move_to_column, frame_hide_editor_elements)
        self.create_checkbox("Button 'Add date'", "", self.hide_button_add_date, frame_hide_editor_elements)
        self.create_checkbox("Button 'Delete'", "", self.hide_button_delete, frame_hide_editor_elements)
        self.create_checkbox("Buttons 'Move line up/down'", "", self.hide_buttons_move_line_up_down, frame_hide_editor_elements)
        self.create_checkbox("Buttons 'Assign priority'", "", self.hide_buttons_assign_priority, frame_hide_editor_elements)
 
        frame_ask_for = tk.LabelFrame(third_column_frame, text="Ask for confirmation, when: ")
        frame_ask_for.pack(fill='x', pady=(10, 0))
        self.create_checkbox("Adding new task", "", self.ask_for_add, frame_ask_for)
        self.create_checkbox("Removing a task", "", self.ask_for_delete, frame_ask_for)

    def exit(self):
        string_col_names = [x.get() for x in self.col_names]
        are_col_names_unique = len(string_col_names) == len(set(string_col_names))
        if not are_col_names_unique:
            tk.messagebox.showwarning(title="Error in column names", message=f"You can't set the same name for multiple columns.")
            return
        self.destroy()

    def buttonbox(self):
        ok_button = tk.Button(self, text='OK', width=5, command=self.exit)
        ok_button.pack(side='right', padx=15, pady=(0, 10))
        self.bind("<Escape>", lambda event: self.exit())
        self.bind("<Return>", lambda event: self.exit())


class KanbanTxtViewer:
    THEMES = {
        'LIGHT_COLORS': {
            "column0": '#f27272',
            "column1": '#00b6e4',
            "column2": '#22b57f',
            "column3": "#8BC34A",
            "column0-column": '#daecf1',
            "column1-column": '#daecf1',
            "column2-column": '#daecf1',
            "column3-column": "#daecf1",
            "important": "#a7083b",
            "project": '#00b6e4',
            'context': '#1c9c6d',
            'main-background': "#C0D6E8",
            'card-background': '#ffffff',
            'done-card-background': '#edf5f7',
            'editor-background': '#cae1e8',
            'main-text': '#4c6066',
            'editor-text': '#000000',
            'button': '#415358',
            'kv-data': '#b8becc',
            'priority_color_scale': [
                "#ec1c24",
                "#ff7f27",
                "#ffca18",
                "#77dd77",
                "#aec6cf"
            ]
        },

        'DARK_COLORS': {
            "column0": '#f27272',
            "column1": '#00b6e4',
            # gwyrdh wait to grey
            "column2": '#9FA1A2',
            "column3": "#8BC34A",
            # gwyrdh charcoal
            "column0-column": '#2F383E',
            "column1-column": '#2F383E',
            "column2-column": '#2F383E',
            "column3-column": "#2F383E",
            "important": "#e12360",
            # gwyrdh colour theme for select
            "project": '#2EB398',
            'context': '#1c9c6d',
            # gwyrdh charcoal softens the card background
            'main-background': '#222B2F',
            'card-background': '#222B2F',
            # Gwyrdh almost black
            #'card-background': '#1A2023',
            'done-card-background': '#1A2023',
            'editor-background': '#222B2F',
            'main-text': '#b6cbd1',
            'editor-text': '#cee4eb',
            'button': '#b6cbd1',
            'kv-data': '#43454a',
            'priority_color_scale': [
                "#ff6961",
                "#ffb347",
                "#fdfd96",
                "#77dd77",
                "#aec6cf"
            ]
        },
        
'ORIGINALDARK_COLORS': {
            "column0": '#f27272',
            "column1": '#00b6e4',
            "column2": '#22b57f',
            "column3": "#8BC34A",
            "column0-column": '#15151f',
            "column1-column": '#15151f',
            "column2-column": '#15151f',
            "column3-column": "#15151f",
            "important": "#e12360",
            # gwyrdh colour theme for select
            "project": '#2EB398',
            'context': '#1c9c6d',
            'main-background': "#1f1f2b",
            'card-background': '#2c2c3a',
            'done-card-background': '#1f1f2b',
            'editor-background': '#15151f',
            'main-text': '#b6cbd1',
            'editor-text': '#cee4eb',
            'button': '#b6cbd1',
            'kv-data': '#43454a',
            'priority_color_scale': [
                "#ff6961",
                "#ffb347",
                "#fdfd96",
                "#77dd77",
                "#aec6cf"
            ],
            'select': '#2EB398'
        },
    }

    FONTS = []
	# gwyrdh edit to minimal text
    KANBAN_KEY = "k"

    KANBAN_VAL_IN_PROGRESS = "do"

    KANBAN_VAL_VALIDATION = "wt"

    CONFIG_PATH = 'config.json'
    CONFIG_KEY_FONT_SIZE = 'card_font_size'
    CONFIG_KEY_HIDE_PROJECT = 'card_hide_project'
    CONFIG_KEY_HIDE_CONTEXT = 'card_hide_context'
    CONFIG_KEY_HIDE_SPECIAL_KV_DATA = 'card_hide_special_kv_data'
    CONFIG_KEY_HIDE_INDEX = 'card_hide_index'
    CONFIG_KEY_HIDE_PRIORITY = 'card_hide_priority'
    CONFIG_KEY_HIDE_DATE = 'card_hide_date'
    CONFIG_KEY_HIDE_SUBJECT = 'card_hide_subject'
    CONFIG_KEY_SORT_METHOD = 'sort_method'
    CONFIG_KEY_ASK_FOR_ADD = 'ask_for_new_task'
    CONFIG_KEY_ASK_FOR_DELETE = 'ask_for_delete'
    CONFIG_KEY_HIDE_MEMO = 'hide_memo'
    CONFIG_KEY_HIDE_BUTTONS_MOVE_TO_COLUMN = 'hide_buttons_move_to_column'
    CONFIG_KEY_HIDE_BUTTONS_ASSIGN_PRIORITY = 'hide_buttons_assign_priority'
    CONFIG_KEY_HIDE_BUTTONS_MOVE_LINE_UP_DOWN = 'hide_buttons_move_line_up_down'
    CONFIG_KEY_HIDE_BUTTON_ADD_DATE = 'hide_button_add_date'
    CONFIG_KEY_HIDE_BUTTON_DELETE = 'hide_button_delete'
    CONFIG_KEY_DARKMODE = 'darkmode'
    CONFIG_KEY_COL_0_NAME = 'column_0'
    CONFIG_KEY_COL_1_NAME = 'column_1'
    CONFIG_KEY_COL_2_NAME = 'column_2'
    CONFIG_KEY_COL_3_NAME = 'column_3'

    CONFIG_DEFAULTS = {
        CONFIG_KEY_ASK_FOR_ADD: True,
        CONFIG_KEY_ASK_FOR_DELETE: True,
        CONFIG_KEY_FONT_SIZE: 10,
        CONFIG_KEY_HIDE_PROJECT: False,
        CONFIG_KEY_HIDE_CONTEXT: False,
        CONFIG_KEY_HIDE_SPECIAL_KV_DATA: False,
        CONFIG_KEY_HIDE_INDEX: False,
        CONFIG_KEY_HIDE_PRIORITY: False,
        CONFIG_KEY_HIDE_DATE: False,
        CONFIG_KEY_HIDE_SUBJECT: False,
        CONFIG_KEY_SORT_METHOD: 0,
        CONFIG_KEY_DARKMODE: False,
        CONFIG_KEY_HIDE_BUTTON_ADD_DATE: False,
        CONFIG_KEY_HIDE_BUTTON_DELETE: False,
        CONFIG_KEY_HIDE_BUTTONS_ASSIGN_PRIORITY: False,
        CONFIG_KEY_HIDE_BUTTONS_MOVE_TO_COLUMN: False,
        CONFIG_KEY_HIDE_BUTTONS_MOVE_LINE_UP_DOWN: False,
        CONFIG_KEY_HIDE_MEMO: False,
        CONFIG_KEY_COL_0_NAME: "To Do",
        CONFIG_KEY_COL_1_NAME: "In progress",
        CONFIG_KEY_COL_2_NAME: "Validation",
        CONFIG_KEY_COL_3_NAME: "Done",
    }

    def __init__(self, file='', darkmode=None) -> None:
        self.config = None
        if os.path.exists(self.CONFIG_PATH):
            with open(self.CONFIG_PATH, "r") as config_file:
                self.config = json.load(config_file)

        self.COLUMN_0_NAME = self.get_value_from_config_or_default(self.CONFIG_KEY_COL_0_NAME)
        self.COLUMN_1_NAME = self.get_value_from_config_or_default(self.CONFIG_KEY_COL_1_NAME)
        self.COLUMN_2_NAME = self.get_value_from_config_or_default(self.CONFIG_KEY_COL_2_NAME)
        self.COLUMN_3_NAME = self.get_value_from_config_or_default(self.CONFIG_KEY_COL_3_NAME)

        self.COLUMNS_NAMES = [
            self.COLUMN_0_NAME,
            self.COLUMN_1_NAME,
            self.COLUMN_2_NAME,
            self.COLUMN_3_NAME
        ]

        self.card_font_size = self.get_value_from_config_or_default(self.CONFIG_KEY_FONT_SIZE)

        self.show_project = not self.get_value_from_config_or_default(self.CONFIG_KEY_HIDE_PROJECT)
        self.show_context = not self.get_value_from_config_or_default(self.CONFIG_KEY_HIDE_CONTEXT)
        self.show_special_kv_data = not self.get_value_from_config_or_default(self.CONFIG_KEY_HIDE_SPECIAL_KV_DATA)
        self.show_index = not self.get_value_from_config_or_default(self.CONFIG_KEY_HIDE_INDEX)
        self.show_priority = not self.get_value_from_config_or_default(self.CONFIG_KEY_HIDE_PRIORITY)
        self.show_date = not self.get_value_from_config_or_default(self.CONFIG_KEY_HIDE_DATE)
        self.show_content = not self.get_value_from_config_or_default(self.CONFIG_KEY_HIDE_SUBJECT)

        self.hide_memo = self.get_value_from_config_or_default(self.CONFIG_KEY_HIDE_MEMO)
        self.hide_button_delete = self.get_value_from_config_or_default(self.CONFIG_KEY_HIDE_BUTTON_DELETE)
        self.hide_button_add_date = self.get_value_from_config_or_default(self.CONFIG_KEY_HIDE_BUTTON_ADD_DATE)
        self.hide_buttons_assign_priority = self.get_value_from_config_or_default(self.CONFIG_KEY_HIDE_BUTTONS_ASSIGN_PRIORITY)
        self.hide_buttons_move_to_column = self.get_value_from_config_or_default(self.CONFIG_KEY_HIDE_BUTTONS_MOVE_TO_COLUMN)
        self.hide_buttons_move_line_up_down = self.get_value_from_config_or_default(self.CONFIG_KEY_HIDE_BUTTONS_MOVE_LINE_UP_DOWN)

        self.ask_for_add = self.get_value_from_config_or_default(self.CONFIG_KEY_ASK_FOR_ADD)
        self.ask_for_delete = self.get_value_from_config_or_default(self.CONFIG_KEY_ASK_FOR_DELETE)

        self.sort_method_idx = self.get_value_from_config_or_default(self.CONFIG_KEY_SORT_METHOD)

        self.filter_view_message = None
        self.editor_warning_tooltip = None
        self.widgets_for_disable_in_filter_mode = []
        self.non_filtered_content_line_mapping = None
        self.non_filtered_content = None
        self.filter = None

        self.drag_begin_cursor_pos = (0, 0)
        self.dragged_widgets = []
        self.drop_areas = []
        self.drop_areas_frame = None
        self.drop_area_highlight = None

        if darkmode is None:
            darkmode = self.get_value_from_config_or_default(self.CONFIG_KEY_DARKMODE)
        self.darkmode = darkmode

        self.file = file

        self.current_date = date.today()

        self.ui_columns = {}
        for col in self.COLUMNS_NAMES:
            self.ui_columns[col] = []

        self._after_id = -1

        self.selected_task_card = None

        self.draw_ui(1000, 700, 0, 0)

    def draw_ui(self, window_width, window_height, window_x, window_y):
        # Define theme
        dark_option = 'LIGHT_COLORS'
        if self.darkmode: 
            dark_option = 'DARK_COLORS'

        default_scheme = list(self.THEMES.keys())[0]
        color_scheme = self.THEMES.get(dark_option, default_scheme)

        self.COLORS = color_scheme

        # Create main window
        self.main_window = tk.Tk()
        self.main_window.bind('<Button-1>', self.clear_drop_areas_frame)
        self.main_window.bind('<Motion>', self.highlight_drop_area)
        self.main_window.bind('<Control-f>', self.activate_search_input)
        self.main_window.bind('<Escape>', self.deactivate_search_input)
        self.main_window.bind('<Control-MouseWheel>', self.on_control_scroll)
        self.main_window.bind('<Alt-v>', self.on_customize_view_button)

        self.main_window.title('KanbanTxt')
        icon_path = pathlib.Path('icons8-kanban-64.png')
        if icon_path.exists():
            self.main_window.iconphoto(False, tk.PhotoImage(file=icon_path))

        self.main_window['background'] = self.COLORS['main-background']
        self.main_window['relief'] = 'flat'
#        self.main_window.geometry("%dx%d+%d+%d" % (window_width, window_height, window_x, window_y))
        #Gwyrdh edit to open window set size - was opening small
        self.main_window.geometry('1700x900+1+1')
        self.FONTS.append(tkFont.Font(name='main', font='Ubuntu',size=10))
        self.FONTS.append(tkFont.Font(name='h2', font='Ubuntu',size=16))
        self.FONTS.append(tkFont.Font(name='done-task', font='Ubuntu',size=10,overstrike=1))
        #self.FONTS.append(tkFont.Font(name='h2', family='Ubuntu', size=14, weight=tkFont.NORMAL))
        #self.FONTS.append(tkFont.Font(name='done-task', font='Ubuntu', size='10', overstrike=1))
        #self.FONTS.append(tkFont.Font(name='main', font='Ubuntu', size=10, weight=tkFont.NORMAL))
        #self.FONTS.append(tkFont.Font(name='h2', family='Ubuntu', size=14, weight=tkFont.NORMAL))
        #self.FONTS.append(tkFont.Font(name='done-task', font='Ubuntu', size='10', overstrike=1))

        # Bind shortkey to open or save a new file
        self.main_window.bind('<Control-s>', self.reload_and_create_file)
        self.main_window.bind('<Control-o>', self.open_file_dialog)
        # Gwyrdh Added short cut to add date
        self.main_window.bind('<Control-d>', self.add_date)
        # Gwyrdh added shortcut to quit
        self.main_window.bind('<Control-q>', self.quit)

       
        self.draw_editor_panel()
        self.draw_content_frame()

        # Load the file provided in arguments if there is one
        if os.path.isfile(self.file):
            self.load_txt_file()
       	# Gwyrdh added def for quit shortcut
    def quit(self, event=None):
        self.main_window.destroy()
        
    def activate_search_input(self, event):
        if self.filter is not None:
            self.clear_filter()
        self.filter_entry_box.focus()

    def deactivate_search_input(self, event):
        if self.filter is not None:
            self.clear_filter()
        self.text_editor.focus()

    def get_cursor_pos(self):
        return self.main_window.winfo_pointerx(), self.main_window.winfo_pointery()

    def clear_drop_areas_frame(self, event=None):
        if self.drop_areas_frame is not None:
            self.drop_areas_frame.destroy()
            self.drop_areas_frame = None

    def on_click(self, event):
        self.drag_begin_cursor_pos = self.get_cursor_pos()
        self.highlight_task(event)

    def on_drag_init(self, event):
        dragged_widget_name = event.widget.winfo_name()
        if dragged_widget_name in self.dragged_widgets:
            return
        self.clear_drop_areas_frame()
        self.dragged_widgets.append(dragged_widget_name)
        self.main_window.after(50, self.on_drag, event) # a little delay to give the UI time to refresh highlighted task card

    def highlight_drop_area(self, event):
        if self.drop_areas_frame is None:
            return
        if len(self.drop_areas) == 0:
            return
        drop_canvas = self.drop_areas_frame.winfo_children()[0]
        if self.drop_area_highlight is not None:
            drop_canvas.delete(self.drop_area_highlight)
            self.drop_area_highlight = None

        drop_area = self.get_drop_area_from_cursor()
        if drop_area is not None:
            self.drop_area_highlight = drop_canvas.create_rectangle(drop_area['x1'], drop_area['y1'], drop_area['x2'], drop_area['y2'], fill="", outline='red', width=3)

    def on_drag(self, event):
        event.widget.config(cursor="fleur")

        # properties of a single drop area
        drop_area_width = 100
        drop_area_height = 100
        drop_area_spacing = 25

        # properties of the parent window for drop areas
        # should appear above currently dragged task card, and it should not protrude beyond
        # the border of the main window
        drop_areas_frame_border = 4
        drop_areas_title_text_pos_y = 10
        drop_areas_pos_x = drop_area_spacing
        drop_areas_pos_y = 2 * drop_areas_title_text_pos_y

        self.drop_areas.clear()
        # determine whether user dragged vertically (to change priority) or horizontally (to change column)
        cursor_x_pos, cursor_y_pos = self.get_cursor_pos()
        distance_x = abs(cursor_x_pos - self.drag_begin_cursor_pos[0])
        distance_y = abs(cursor_y_pos - self.drag_begin_cursor_pos[1])
        if distance_x >= distance_y:
            drop_areas_title = "Move this task to:"
            move_functors = {
                self.COLUMN_0_NAME: self.move_to_todo,
                self.COLUMN_1_NAME: self.move_to_in_progress,
                self.COLUMN_2_NAME: self.move_to_validation,
                self.COLUMN_3_NAME: self.move_to_done,
            }
            for idx, column_name in enumerate(self.COLUMNS_NAMES):
                self.drop_areas.append({
                    'name': column_name,
                    'color': self.COLORS[f"column{idx}"],
                    'functor': move_functors[column_name],
                    'x1': drop_areas_pos_x,
                    'y1': drop_areas_pos_y,
                    'x2': drop_areas_pos_x + drop_area_width,
                    'y2': drop_areas_pos_y + drop_area_height
                })
                drop_areas_pos_x += drop_area_spacing + drop_area_width
        else:
            drop_areas_title = "Change priority to:"
            priority_functors = {
                "A": self.change_priority_to_A,
                "B": self.change_priority_to_B,
                "C": self.change_priority_to_C,
                "D": self.change_priority_to_D,
                "E": self.change_priority_to_E,
                "(none)": lambda: self.change_priority(None, "")
            }
            i = 0
            for priority in priority_functors.keys():
                color = 'white'
                if i < len(self.COLORS['priority_color_scale']):
                    color = self.COLORS['priority_color_scale'][i]
                i += 1
                self.drop_areas.append({
                    'name': priority,
                    'color': color,
                    'functor': priority_functors[priority],
                    'x1': drop_areas_pos_x,
                    'y1': drop_areas_pos_y,
                    'x2': drop_areas_pos_x + drop_area_width,
                    'y2': drop_areas_pos_y + drop_area_height
                })
                drop_areas_pos_x += drop_area_spacing + drop_area_width

        task_card_frame_widget = self.get_task_card_frame_widget(event.widget)
        drop_areas_frame_width = (drop_area_width + drop_area_spacing) * (len(self.drop_areas) + 1)
        drop_areas_frame_pos_x = cursor_x_pos - int(drop_areas_frame_width / 2)
        drop_areas_frame_pos_y = task_card_frame_widget.winfo_rooty() - drop_area_height - drop_area_spacing

        main_window_geometry = [int(a) for a in re.split('[+x]', self.main_window.geometry())]
        main_window_end_pos_x = main_window_geometry[0] + main_window_geometry[2]
        drop_areas_frame_pos_x_offset = drop_areas_frame_pos_x + drop_areas_frame_width - main_window_end_pos_x
        if drop_areas_frame_pos_x_offset >= 0:
            drop_areas_frame_pos_x -= drop_areas_frame_pos_x_offset + drop_area_spacing

        # use a Toplevel window, overridedirect and "-topmost" attribute to trick tkinter into
        # displaying this window on top in a desired position
        self.drop_areas_frame = tk.Toplevel(self.main_window, padx=0, pady=0, background=self.COLORS['button'], borderwidth=drop_areas_frame_border)
        self.drop_areas_frame.geometry(f"{drop_areas_frame_width}x{drop_area_height + drop_area_spacing + drop_areas_title_text_pos_y}+{drop_areas_frame_pos_x}+{drop_areas_frame_pos_y}")
        self.drop_areas_frame.overrideredirect(True)
        self.drop_areas_frame.wm_attributes("-topmost", True)

        # canvas to paint drop areas onto
        canvas_width = (drop_area_width + drop_area_spacing) * (len(self.drop_areas)) + drop_area_spacing
        canvas = tk.Canvas(self.drop_areas_frame,
                           borderwidth=0,
                           bg="white",
                           width=canvas_width)
        canvas.pack()
        for drop_area in self.drop_areas:
            canvas.create_rectangle(drop_area['x1'], drop_area['y1'], drop_area['x2'], drop_area['y2'], fill=drop_area['color'])
            canvas.create_text(drop_area['x1'] + drop_area_width / 2, drop_area['y1'] + drop_area_height / 2, text=drop_area['name'], fill='black')
        canvas.create_text(canvas_width / 2, drop_areas_title_text_pos_y, text=drop_areas_title, fill='black')

    def is_cursor_in_box(self, box_x1, box_y1, box_x2, box_y2):
        cursor_pos_x, cursor_pos_y = self.get_cursor_pos()
        return box_x1 < cursor_pos_x < box_x2 and box_y1 < cursor_pos_y < box_y2

    def get_drop_area_from_cursor(self):
        if self.drop_areas_frame is not None and len(self.drop_areas) > 0:
            drop_canvas = self.drop_areas_frame.winfo_children()[0]
            for i in range(len(self.drop_areas)):
                canvas_offset_x = drop_canvas.winfo_rootx()
                canvas_offset_y = drop_canvas.winfo_rooty()

                drop_top_left_x = self.drop_areas[i]['x1'] + canvas_offset_x
                drop_top_left_y = self.drop_areas[i]['y1'] + canvas_offset_y
                drop_bottom_right_x = self.drop_areas[i]['x2'] + canvas_offset_x
                drop_bottom_right_y = self.drop_areas[i]['y2'] + canvas_offset_y
                if self.is_cursor_in_box(drop_top_left_x, drop_top_left_y, drop_bottom_right_x, drop_bottom_right_y):
                    return self.drop_areas[i]
        return None

    def on_drop(self, event):
        dragged_widget_name = event.widget.winfo_name()
        if dragged_widget_name not in self.dragged_widgets:
            return

        self.dragged_widgets.remove(dragged_widget_name)
        event.widget.config(cursor="hand2")
        if self.drop_areas_frame is None:
            return

        drop_area = self.get_drop_area_from_cursor()
        if drop_area is not None:
            drop_area['functor']()

        self.drop_areas.clear()
        self.clear_drop_areas_frame()

    def on_customize_view_button(self, event=None):
        show_project_var = tk.IntVar(value=self.show_project)
        show_context_var = tk.IntVar(value=self.show_context)
        show_special_kv_data_var = tk.IntVar(value=self.show_special_kv_data)
        show_index = tk.IntVar(value=self.show_index)
        show_priority_var = tk.IntVar(value=self.show_priority)
        show_date_var = tk.IntVar(value=self.show_date)
        show_content_var = tk.IntVar(value=self.show_content)

        ask_for_add_var = tk.IntVar(value=self.ask_for_add)
        ask_for_delete_var = tk.IntVar(value=self.ask_for_delete)

        out_sort_method = tk.StringVar(value=self.sort_method_idx)

        out_fontsize = tk.StringVar(value=self.card_font_size)

        out_col0_name = tk.StringVar(value=self.COLUMN_0_NAME)
        out_col1_name = tk.StringVar(value=self.COLUMN_1_NAME)
        out_col2_name = tk.StringVar(value=self.COLUMN_2_NAME)
        out_col3_name = tk.StringVar(value=self.COLUMN_3_NAME)

        hide_memo = tk.IntVar(value=not self.hide_memo)
        hide_button_delete = tk.IntVar(value=not self.hide_button_delete)
        hide_button_add_date = tk.IntVar(value=not self.hide_button_add_date)
        hide_buttons_assign_priority = tk.IntVar(value=not self.hide_buttons_assign_priority)
        hide_buttons_move_to_column = tk.IntVar(value=not self.hide_buttons_move_to_column)
        hide_buttons_move_line_up_down = tk.IntVar(value=not self.hide_buttons_move_line_up_down)

        CustomizeViewDialog(title="Customize view",
                            parent=self.main_window,
                            out_show_date=show_date_var,
                            out_show_priority=show_priority_var,
                            out_show_content=show_content_var,
                            out_show_context=show_context_var,
                            out_show_project=show_project_var,
                            out_show_special_kv_data=show_special_kv_data_var,
                            out_show_index=show_index,
                            out_sort_method=out_sort_method,
                            out_fontsize=out_fontsize,
                            out_col0_name=out_col0_name,
                            out_col1_name=out_col1_name,
                            out_col2_name=out_col2_name,
                            out_col3_name=out_col3_name,
                            out_ask_for_add=ask_for_add_var,
                            out_ask_for_delete=ask_for_delete_var,
                            out_hide_memo=hide_memo,
                            out_hide_button_delete=hide_button_delete,
                            out_hide_button_add_date=hide_button_add_date,
                            out_hide_buttons_assign_priority=hide_buttons_assign_priority,
                            out_hide_buttons_move_to_column=hide_buttons_move_to_column,
                            out_hide_buttons_move_line_up_down=hide_buttons_move_line_up_down,
                            )

        self.show_date = show_date_var.get()
        self.show_priority = show_priority_var.get()
        self.show_content = show_content_var.get()
        self.show_context = show_context_var.get()
        self.show_project = show_project_var.get()
        self.show_special_kv_data = show_special_kv_data_var.get()
        self.show_index = show_index.get()

        self.ask_for_delete = ask_for_delete_var.get()
        self.ask_for_add = ask_for_add_var.get()

        self.sort_method_idx = int(out_sort_method.get())

        self.card_font_size = int(out_fontsize.get())

        self.hide_memo = not hide_memo.get()
        self.hide_button_add_date = not hide_button_add_date.get()
        self.hide_button_delete = not hide_button_delete.get()
        self.hide_buttons_move_line_up_down = not hide_buttons_move_line_up_down.get()
        self.hide_buttons_move_to_column = not hide_buttons_move_to_column.get()
        self.hide_buttons_assign_priority = not hide_buttons_assign_priority.get()

        new_column_names = [
            out_col0_name.get(),
            out_col1_name.get(),
            out_col2_name.get(),
            out_col3_name.get(),
        ]

        are_new_column_names_unique = len(new_column_names) == len(set(new_column_names))
        has_any_column_changed = False
        if are_new_column_names_unique:
            for i, new_name in enumerate(new_column_names):
                old_name = self.COLUMNS_NAMES[i]
                if old_name != new_name:
                    self.ui_columns[new_name] = self.ui_columns[old_name]
                    del self.ui_columns[old_name]
                    self.progress_bars[new_name] = self.progress_bars[old_name]
                    del self.progress_bars[old_name]
                    has_any_column_changed = True

            if has_any_column_changed:
                self.COLUMNS_NAMES = new_column_names
                self.COLUMN_0_NAME = new_column_names[0]
                self.COLUMN_1_NAME = new_column_names[1]
                self.COLUMN_2_NAME = new_column_names[2]
                self.COLUMN_3_NAME = new_column_names[3]
                self.store_in_config(self.CONFIG_KEY_COL_0_NAME, self.COLUMN_0_NAME)
                self.store_in_config(self.CONFIG_KEY_COL_1_NAME, self.COLUMN_1_NAME)
                self.store_in_config(self.CONFIG_KEY_COL_2_NAME, self.COLUMN_2_NAME)
                self.store_in_config(self.CONFIG_KEY_COL_3_NAME, self.COLUMN_3_NAME)

        self.store_in_config(self.CONFIG_KEY_HIDE_DATE, not self.show_date)
        self.store_in_config(self.CONFIG_KEY_HIDE_PRIORITY, not self.show_priority)
        self.store_in_config(self.CONFIG_KEY_HIDE_SUBJECT, not self.show_content)
        self.store_in_config(self.CONFIG_KEY_HIDE_CONTEXT, not self.show_context)
        self.store_in_config(self.CONFIG_KEY_HIDE_PROJECT, not self.show_project)
        self.store_in_config(self.CONFIG_KEY_HIDE_SPECIAL_KV_DATA, not self.show_special_kv_data)
        self.store_in_config(self.CONFIG_KEY_HIDE_INDEX, not self.show_index)

        self.store_in_config(self.CONFIG_KEY_ASK_FOR_ADD, self.ask_for_add)
        self.store_in_config(self.CONFIG_KEY_ASK_FOR_DELETE, self.ask_for_delete)

        self.store_in_config(self.CONFIG_KEY_SORT_METHOD, self.sort_method_idx)

        self.store_in_config(self.CONFIG_KEY_FONT_SIZE, self.card_font_size)

        editor_widget_change_state = [
            self.store_in_config(self.CONFIG_KEY_HIDE_MEMO, self.hide_memo),
            self.store_in_config(self.CONFIG_KEY_HIDE_BUTTON_ADD_DATE, self.hide_button_add_date),
            self.store_in_config(self.CONFIG_KEY_HIDE_BUTTON_DELETE, self.hide_button_delete),
            self.store_in_config(self.CONFIG_KEY_HIDE_BUTTONS_ASSIGN_PRIORITY, self.hide_buttons_assign_priority),
            self.store_in_config(self.CONFIG_KEY_HIDE_BUTTONS_MOVE_LINE_UP_DOWN, self.hide_buttons_move_line_up_down),
            self.store_in_config(self.CONFIG_KEY_HIDE_BUTTONS_MOVE_TO_COLUMN, self.hide_buttons_move_to_column)
        ]
        has_any_editor_widget_changed = any(editor_widget_change_state)
        if has_any_column_changed or has_any_editor_widget_changed:
            self.recreate_main_window()
        self.save_config_file()

        self.reload_ui_from_text()

    def get_value_from_config_or_default(self, key):
        value = None
        if self.config is not None:
            value = self.config.get(key)
        if value is None:
            value = self.CONFIG_DEFAULTS[key]
        return value

    def store_in_config(self, key, value):
        value_changed = True
        if self.config is None:
            self.config = {}
        if self.config.get(key, None) == value:
            value_changed = False
        self.config[key] = value
        return value_changed

    def save_config_file(self):
        if self.config is None:
            return
        try:
            with open(self.CONFIG_PATH, "w") as f:
                json.dump(self.config, f, sort_keys=True, indent=4)
        except Exception as error:
            tk.messagebox.showwarning(title="Error writing config file", message=f"Can't save the file '{self.CONFIG_PATH}', make sure you have the right to write here!")

    def draw_editor_panel(self):
        self.widgets_for_disable_in_filter_mode.clear()

        # EDITION FRAME
        edition_frame = tk.Frame(self.main_window, bg=self.COLORS['editor-background'], width=20)
        edition_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.main_window.grid_rowconfigure(0, weight=1)
        self.main_window.grid_columnconfigure(0, weight=1)

        # HEADER
        editor_header = tk.Frame(edition_frame, bg=self.COLORS['editor-background'])
        editor_header.pack(side='top', fill='both', expand=0, padx=10, pady=0)
		# gwyrdh added buttons up down date and delete to save space
        load_button = self.create_button(
            editor_header,
            text="🗁",
            # gwyrdh change from 2
            bordersize=1,
            color=self.COLORS['button'],
            activetextcolor=self.COLORS['main-background'],
            command=self.open_file_dialog,
            tooltip="Open file",
            disable_in_filter_view=True
        )
        load_button.pack(side="right", padx=(10,0), pady=10, anchor=tk.NE)

        save_button = self.create_button(
            editor_header,
            text="⟳",
            bordersize=1,
            color=self.COLORS['button'],
            activetextcolor=self.COLORS['main-background'],
            command=self.reload_and_create_file,
            tooltip="Reload UI and save file"
        )
        save_button.pack(side="right", padx=(10,0), pady=10, anchor=tk.NE)
        
        date_button = self.create_button(
            editor_header,
            text="+ date",
            bordersize=1,
            color=self.COLORS['button'],
            activetextcolor=self.COLORS['main-background'],
            command=self.add_date
        )
        date_button.pack(side="right", padx=(10,0), pady=10, anchor=tk.NE)
        
        delete_button = self.create_button(
            editor_header,
            text="Delete",
            bordersize=1,
            color=self.COLORS['button'],
            activetextcolor=self.COLORS['main-background'],
            command=self.remove_line
        )
        delete_button.pack(side="right", padx=(10,0), pady=10, anchor=tk.NE)
        
        up_button = self.create_button(
            editor_header,
            text="↑",
            bordersize=1,
            color=self.COLORS['button'],
            activetextcolor=self.COLORS['main-background'],
            command=self.move_line_up
        )
        up_button.pack(side="right", padx=(10,0), pady=10, anchor=tk.NE)
        
        down_button = self.create_button(
            editor_header,
            text="↓",
            bordersize=1,
            color=self.COLORS['button'],
            activetextcolor=self.COLORS['main-background'],
            command=self.move_line_down
        )
        down_button.pack(side="right", padx=(10,0), pady=10, anchor=tk.NE)

        # Light mode / dark mode switch
        button_color = self.COLORS['button']

        darkmode_button_border = tk.Frame(
            editor_header,
            bg=button_color
        )
        darkmode_button_border.pack(side="left", padx=(10,0), pady=10, anchor=tk.NE)
        darkmode_button = tk.Label(
            darkmode_button_border, 
            text='🔘', 
            relief='flat', 
            bg=self.COLORS['editor-background'], 
            fg=button_color,
            # Gwyrdh font change
            #font=tkFont.nametofont(font))
            font=('Ubuntu', 10))
        darkmode_button.pack(side="left", padx=2, pady=2)
        darkmode_button.bind("<Button-1>", self.on_switch_darkmode)

        darkmode_button = tk.Label(
            darkmode_button_border, 
            text='🌙', 
            relief='flat', 
            bg=button_color, 
            fg=self.COLORS['editor-background'],
            # Gwyrdh font change
            #font=tkFont.nametofont(font))
            font=('Ubuntu', 12))
        darkmode_button.pack(side="left", padx=2, pady=2)
        darkmode_button.bind("<Button-1>", self.on_switch_darkmode)
        # END Light mode / dark mode switch

        show_hide_button = self.create_button(editor_header,
                                              "👁",
                                              command=self.on_customize_view_button,
                                              bordersize=1,
                                              color=self.COLORS['button'],
                                              activetextcolor=self.COLORS['main-background'],
                                              tooltip="Customize view")
        show_hide_button.pack(side="left", padx=(10,0), pady=10, anchor=tk.NE)
        #END HEADER

        # Separator
        tk.Frame(edition_frame, height=1, bg=self.COLORS['main-text']).pack(side='top', fill='x')

        # MEMO
        cheat_sheet = tk.Label(edition_frame, text='------ Memo ------\n'
            f'{self.KANBAN_KEY}:{self.KANBAN_VAL_IN_PROGRESS} \t—  {self.COLUMN_1_NAME}\n'
            f'{self.KANBAN_KEY}:{self.KANBAN_VAL_VALIDATION} \t—  {self.COLUMN_2_NAME}\n'
            f'x \t\t—  {self.COLUMN_3_NAME}\n'
            'F5,  Ctrl + s \t—  refresh and save\n'
            'Alt + ↑ / ↓ \t—  move line up / down\n'
            'Alt + v \t\t—  customize view\n'
            'Ctrl + f \t\t—  filter tasks\n'
            'ESC \t\t—  close filter/customize view\n',
            bg=self.COLORS['editor-background'],
            anchor=tk.NW,
            justify='left',
            fg=self.COLORS['main-text'],
            font=tkFont.nametofont('main'),
        )
        if not self.hide_memo:
            cheat_sheet.pack(side="top", fill="x", padx=10)
        # MEMO END

        # Separator
        tk.Frame(edition_frame, height=1, bg=self.COLORS['main-text']).pack(side='top', fill='x')

        self.filter_frame = tk.Frame(edition_frame, bg=self.COLORS['editor-background'])
        self.filter_frame.pack(side='top', fill='both', expand=0, padx=10, pady=0)

        filter_label = tk.Label(self.filter_frame, text='Filter:',
            bg=self.COLORS['editor-background'],
            anchor=tk.NW,
            justify='left',
            fg=self.COLORS['main-text'],
            font=tkFont.nametofont('main'))
        filter_label.pack(side="left", padx=(10,0), anchor=tk.W)

        filter_text_var = tk.StringVar(self.filter_frame)
        self.filter_entry_box = tk.Entry(self.filter_frame,
            textvariable=filter_text_var,
            bd=0,
            font=(main, 12),
            bg=self.COLORS['done-card-background'],
            fg=self.COLORS['main-text'],
            insertbackground=self.COLORS['main-text'])
        self.filter_entry_box.pack(side="left", padx=(10,0), anchor=tk.W)
        self.filter_entry_box.bind('<Return>', self.apply_filter)
        self.widgets_for_disable_in_filter_mode.append(self.filter_entry_box)

        self.apply_filter_button = self.create_button(
            self.filter_frame,
            text="apply",
            # gwyrdh reduce border size
            bordersize=1,
            color=self.COLORS['button'],
            activetextcolor=self.COLORS['main-background'],
            command=self.apply_filter,
            tooltip="Apply search filter",
            disable_in_filter_view=True
        )
        self.apply_filter_button.pack(side="left", padx=(10,0), pady=10, anchor=tk.NE)

        self.clear_filter_button = self.create_button(
            self.filter_frame,
            # gwyrdh change text to clear
            text="clear",
            bordersize=1,
            color=self.COLORS['button'],
            activetextcolor=self.COLORS['main-background'],
            command=self.clear_filter,
            tooltip="Close search results mode",
            disable_in_filter_view=True
        )
        self.clear_filter_button.winfo_children()[0].configure(state='disabled')
        self.clear_filter_button.pack(side="left", padx=(10, 0), pady=10, anchor=tk.NE)

        self.use_regex_val = tk.IntVar()
        self.use_regex_checkbox = tk.Checkbutton(self.filter_frame,
                                                 text='use regex',
                                                 variable=self.use_regex_val,
                                                 fg=self.COLORS['button'],
                                                 bg=self.COLORS['editor-background'],
                                                 selectcolor=self.COLORS['done-card-background']
                                                 )
        # gwyrdh removed to save space
        # self.use_regex_checkbox.pack(side="left", padx=(10, 0), anchor=tk.W)
        # user_regex_hovertip = Hovertip(self.use_regex_checkbox, "If selected, uses a regular expression for matching each line; otherwise uses simple search, case insensitive.")
        self.widgets_for_disable_in_filter_mode.append(self.use_regex_checkbox)

        # Separator
        tk.Frame(edition_frame, height=1, bg=self.COLORS['main-text']).pack(side='top', fill='x')

        # EDITOR
        self.text_editor = tk.Text(
            edition_frame, 
            bg=self.COLORS['editor-background'], 
            insertbackground=self.COLORS['editor-text'], 
            fg=self.COLORS['editor-text'], 
            relief="flat", 
            width=40,
            height=10,
            maxundo=10,
            undo=True,
            wrap=tk.WORD,
            spacing1=10,
            spacing3=10,
            insertwidth=3,
        )
        self.text_editor.pack(side="top", fill="both", expand=1, padx=10, pady=10)
        self.text_editor.tag_configure('pair', background=self.COLORS['done-card-background'])
        self.text_editor.tag_configure('current_pos', foreground='black', background=self.COLORS['project'], selectbackground=self.COLORS["column0"])
        self.text_editor.tag_configure('insert', background='red')

        # EDITOR TOOLBAR
        editor_toolbar = tk.Frame(edition_frame, bg=self.COLORS['editor-background'])
        editor_toolbar.pack(side='top', padx=10, pady=10, fill='both')

        # Move to todo
        if not self.hide_buttons_move_to_column:
            self.create_button(
                editor_toolbar, 
                '✅→⚫', 
                self.COLORS["column0"], 
                command=self.move_to_todo,
                tooltip=f"Move task to {self.COLUMN_0_NAME}"
            ).grid(row=0, sticky='ew', column=0, padx=5, pady=5)

        # Cycle through priorities
        if not self.hide_buttons_assign_priority:
            self.create_button(
                editor_toolbar,
                '⧉ ↻',
                self.COLORS['priority_color_scale'][4],
                command=self.change_priority,
                tooltip="Change priority to higher"
            ).grid(row=0, sticky='ew', column=4, padx=5, pady=5)

        # Move to In progress
        if not self.hide_buttons_move_to_column:
            self.create_button(
                editor_toolbar,
                '✅→⚫',
                self.COLORS["column1"],
                command=self.move_to_in_progress,
                tooltip=f"Move task to {self.COLUMN_1_NAME}"
            ).grid(row=0, sticky='ew', column=1, padx=5, pady=5)

        # Move to Validation
        if not self.hide_buttons_move_to_column:
            self.create_button(
                editor_toolbar,
                '✅→⚫',
                self.COLORS["column2"],
                command=self.move_to_validation,
                tooltip=f"Move task to {self.COLUMN_2_NAME}"
            ).grid(row=0, sticky='ew', column=2, padx=5, pady=5)

        # Move to Done
        if not self.hide_buttons_move_to_column:
            self.create_button(
                editor_toolbar,
                '✅→⚫',
                self.COLORS["column3"],
                command=self.move_to_done,
                tooltip=f"Move task to {self.COLUMN_3_NAME}"
            ).grid(row=0, sticky='ew', column=3, padx=5, pady=5)

        # Set prios A..E
        if not self.hide_buttons_assign_priority:
            self.create_button(
                editor_toolbar,
                f'⧉ A',
                self.COLORS['priority_color_scale'][0],
                command=self.change_priority_to_A,
                tooltip="Set priority to A"
            ).grid(row=3, sticky='ew', column=0, padx=5, pady=5)

            self.create_button(
                editor_toolbar,
                f'⧉ B',
                self.COLORS['priority_color_scale'][1],
                command=self.change_priority_to_B,
                tooltip="Set priority to B"
            ).grid(row=3, sticky='ew', column=1, padx=5, pady=5)
    
            self.create_button(
                editor_toolbar,
                f'⧉ C',
                self.COLORS['priority_color_scale'][2],
                command=self.change_priority_to_C,
                tooltip="Set priority to C"
            ).grid(row=3, sticky='ew', column=2, padx=5, pady=5)
    
            self.create_button(
                editor_toolbar,
                f'⧉ D',
                self.COLORS['priority_color_scale'][3],
                command=self.change_priority_to_D,
                tooltip="Set priority to D"
            ).grid(row=3, sticky='ew', column=3, padx=5, pady=5)
    
            self.create_button(
                editor_toolbar,
                f'⧉ E',
                self.COLORS['priority_color_scale'][4],
                command=self.change_priority_to_E,
                tooltip="Set priority to E"
            ).grid(row=3, sticky='ew', column=4, padx=5, pady=5)
    
            self.create_button(
                editor_toolbar,
                f'⧉ ☒',
                self.COLORS['important'],
                command=lambda: self.change_priority(None, ''),
                tooltip="Remove priority"
            ).grid(row=2, sticky='ew', column=4, padx=5, pady=5)
    
        # Add date
        if not self.hide_button_add_date:
            self.create_button(
                editor_toolbar, 
                '+ date', 
                self.COLORS['button'], 
                command=self.add_date
            ).grid(row=2, sticky='ew', column=0, padx=5, pady=5)

        if not self.hide_buttons_move_line_up_down:
            # Move line up
            self.create_button(
                editor_toolbar, 
                '↑', 
                self.COLORS['button'], 
                command=self.move_line_up,
                tooltip="Move line up",
                disable_in_filter_view=True
            ).grid(row=2, sticky='ew', column=1, padx=5, pady=5)
    
            # Move line down
            self.create_button(
                editor_toolbar, 
                '↓', 
                self.COLORS['button'], 
                command=self.move_line_down,
                tooltip="Move line down",
                disable_in_filter_view=True
            ).grid(row=2, sticky='ew', column=2, padx=5, pady=5)

        if not self.hide_button_delete:
            # Delete line
            self.create_button(
                editor_toolbar, 
                'Delete', 
                self.COLORS['button'], 
                command=self.remove_line,
                tooltip="Remove current line",
                disable_in_filter_view=True
            ).grid(row=2, sticky='ew', column=3, padx=5, pady=5)

        editor_toolbar.columnconfigure(0, weight=1, uniform='toolbar-item')
        editor_toolbar.columnconfigure(1, weight=1, uniform='toolbar-item')
        editor_toolbar.columnconfigure(2, weight=1, uniform='toolbar-item')
        editor_toolbar.columnconfigure(3, weight=1, uniform='toolbar-item')
        editor_toolbar.columnconfigure(4, weight=1, uniform='toolbar-item')
        # EDITOR TOOLBAR END

        #EDITOR END

        # Bind all the option to update and save the file
        self.text_editor.bind('<Return>', self.on_return_pressed)
        self.text_editor.bind('<BackSpace>', self.on_backspace_pressed)
        self.text_editor.bind('<Delete>', self.on_delete_pressed)
        self.text_editor.bind('<space>', self.on_whitespace_pressed)
        self.text_editor.bind('<Tab>', self.on_whitespace_pressed)
        self.text_editor.bind('<Control-space>', self.reload_and_save)
        self.text_editor.bind('<F5>', self.reload_and_save)

        # Bind navigation keys for proper tasks highlights
        # todo: make this more efficient, no need to update on every left/right, also no need to update editor colors
        self.text_editor.bind('<Up>', self.schedule_update_of_editor_line_colors)
        self.text_editor.bind('<Down>', self.schedule_update_of_editor_line_colors)
        self.text_editor.bind('<Right>', self.schedule_update_of_editor_line_colors)
        self.text_editor.bind('<Left>', self.schedule_update_of_editor_line_colors)
        self.text_editor.bind('<Control-End>', self.schedule_update_of_editor_line_colors)
        self.text_editor.bind('<Control-Home>', self.schedule_update_of_editor_line_colors)
        self.text_editor.bind('<Button-1>', self.schedule_update_of_editor_line_colors)

        # Shortkeys
        # gwyrdh changed order to make more sense
        self.text_editor.bind('<Alt-Up>', self.move_line_up)
        self.text_editor.bind('<Alt-Down>', self.move_line_down)
        self.text_editor.bind('<Control-Key-1>', self.move_to_todo)
        self.text_editor.bind('<Control-Key-2>', self.move_to_in_progress)
        self.text_editor.bind('<Control-Key-3>', self.move_to_validation)
        self.text_editor.bind('<Control-Key-4>', self.move_to_done)
        self.text_editor.bind('<Control-Key-5>', self.change_priority)    

    def draw_content_frame(self):
        # Create content view that will display kanban

        # SCROLLABLE CANVAS
        # Use canvas to make content view scrollable
        self.content_canvas = tk.Canvas(
            self.main_window, 
            bg=self.COLORS['main-background'], 
            bd=0, 
            highlightthickness=0, 
            relief=tk.FLAT
        )
        self.content_canvas.grid(row=0, column=1, sticky=tk.NSEW, padx=10, pady=10)
        
        # Give more space to the kanban view
        # gwyrdh increased weight nb need to edit buttons to allow this
        self.main_window.grid_columnconfigure(1, weight=30)

        # The frame inside the canvas. It manage the widget displayed inside the canvas
        self.content_frame = tk.Frame(self.content_canvas, bg=self.COLORS['main-background'])


        content_scrollbar = tk.Scrollbar(
            self.main_window, 
            orient="vertical", 
            command=self.content_canvas.yview
        )
        content_scrollbar.grid(row=0, column=2, sticky='ns')
        
        self.canvas_frame = self.content_canvas.create_window(
            (0, 0), window=self.content_frame, anchor="nw")

        # Attach the scroll bar position to the visible region of the canvas
        self.content_canvas.configure(yscrollcommand=content_scrollbar.set)
        # END SCROLLABLE CANVAS

        # Prepare progress bars and kanban itself
        # gwyrdh increased height 
        self.progress_bar = tk.Frame(self.content_frame, height=30, bg=self.COLORS['done-card-background'])
        self.progress_bar.pack(side='top', fill='x', padx=10, pady=10)
        self.progress_bars = {}

        # position of the current sub progress bar
        sub_bar_pos = 0
        # number of the current column in the tkinter grid
        column_number = 0

        # Frame containing the kanban
        self.kanban_frame = tk.Frame(self.content_frame, bg=self.COLORS['main-background'])
        self.kanban_frame.pack(fill='both')

        # Create each column and its associated progress bar
        for idx, (key, column) in enumerate(self.ui_columns.items()):
            column_color = self.COLORS[f'column{idx}-column']

            # Create the kanban column
            ui_column = tk.Frame(self.kanban_frame, bg=column_color)
            ui_column.grid(
                row=1, column=column_number, padx=10, pady=0, sticky='nwe')
            self.kanban_frame.grid_columnconfigure(
                column_number, weight=1, uniform="kanban")

            top_border = tk.Frame(
                ui_column, 
                bg=self.COLORS[f'column{idx}'],
                height=8
            )
            top_border.pack(fill='x', side="top", anchor=tk.W)

            title_color = self.COLORS[f'column{idx}']
            if title_color == self.COLORS[f'column{idx}-column']:
                title_color = self.COLORS['main-background']
            label = tk.Label(
                ui_column, 
                text=self.COLUMNS_NAMES[idx], 
                fg=title_color, 
                bg=ui_column['bg'], 
                anchor=tk.W, 
                # gwyrdh edit font
                font=('Ubuntu', 16)
                #font=tkFont.nametofont('h2')
            )
            label.pack(padx=10, pady=(3, 10), fill='x', side="top", anchor=tk.W)

            ui_column_content = tk.Frame(ui_column, bg=ui_column['bg'], height=0)
            ui_column_content.pack(side='top', padx=10, pady=(0,10), fill='x')

            self.ui_columns[key] = ui_column
            self.ui_columns[key].content = ui_column_content

            
            # Create the progress bar associated to the column
            self.progress_bars[key] = {}
            self.progress_bars[key]['bar'] = tk.Frame(
                self.progress_bar, bg=self.COLORS[f'column{idx}'])
            self.progress_bars[key]['bar'].place(
                relx=sub_bar_pos, relwidth=0.25, relheight=1)
            
            # Add a label in the progress bar that display the number of tasks
            # in the column
            bar_label_text = key + ': -'
            self.progress_bars[key]['label'] = tk.Label(
                self.progress_bars[key]['bar'], 
                text=bar_label_text, 
                fg=self.COLORS['main-background'], 
                bg=self.progress_bars[key]['bar']['bg'], 
                font=('Ubuntu', 10))
            self.progress_bars[key]['label'].pack(side='left', padx=5)
            
            sub_bar_pos += 0.25
            column_number += 1

        # Bind signals
        #self.content_canvas.bind('<Configure>', self.adapt_canvas_to_window)

        # Allow to bind the mousewheel event to the canvas and scroll through it
        # with the wheel
        self.content_canvas.bind('<Enter>', self.bind_to_mousewheel)
        self.content_canvas.bind('<Leave>', self.unbind_to_mousewheel)

        # Move the scroll region according to the scroll
        self.content_frame.bind(
            "<Configure>",
            lambda e: self.content_canvas.configure(
                scrollregion=self.content_canvas.bbox("all")
            )
        )

        # resize kanban frame when window is resied
        self.content_canvas.bind('<Configure>', self.on_window_resize)
    

    def create_button(
        self,
        parent, 
        text="button",
        color="black",
        activetextcolor="white",
        # gwyrdh reduce size
        bordersize=1,
        command=None,
        tooltip=None,
        disable_in_filter_view=False
    ):
        """Create a button with a border and no background"""
        button_frame = tk.Frame(
            parent,
            bg=color
        )
        button = tk.Button(
            button_frame,
            text=text,
            relief='flat',
            bg=parent['bg'],
            fg=color,
            activebackground=color,
            activeforeground=activetextcolor,
            borderwidth=0,
            #font=tkFont.nametofont('main'),
            font=('Ubuntu', 10),
            command=command)
        button.pack(padx=bordersize, pady=bordersize, fill='both')
        if disable_in_filter_view:
            self.widgets_for_disable_in_filter_mode.append(button)
        if tooltip is not None:
            hovertip = Hovertip(button, tooltip)
        return button_frame


    def fread(self, filename):
        """Read file and close the file."""
        with open(filename, 'r', encoding='utf8') as f:
            return f.read()

    def fwrite(self, filename, text):
        """Write content to file and close the file."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)

    def parse_todo_txt(self, p_todo_txt):
        """Parse a todo txt content and return data as a dictionary"""
        tasks = {}
        for col in self.COLUMNS_NAMES:
            tasks[col] = []

        # Erase the columns content
        for ui_column_name, ui_column in self.ui_columns.items():
            ui_column.content.pack_forget()
            for widget in ui_column.content.winfo_children():
                widget.destroy()

        todo_list = p_todo_txt.split("\n")

        cards_data = []
        for index, task_txt in enumerate(todo_list):
            if len(task_txt) != 0:
                task_data = re.match(
                    r'^(?P<isDone>x )? '
                    r'?(?P<priority>\([A-Z]\))? '
                    r'?(?P<dates>\d\d\d\d-\d\d-\d\d( \d\d\d\d-\d\d-\d\d)?)? '
                    r'?(?P<subject>.+)',
                    task_txt)

                # special key-vals, context or project tags may occur basically everywhere in the line,
                # so don't try to fit it into the structured regex above, just make a new search
                special_kv_r = re.compile(r'(?P<key>[^:\s]+):(?P<val>[^:\s]+)')
                special_kv_data = [m.groupdict() for m in special_kv_r.finditer(task_txt)]

                project_r = re.compile(r' (?P<project>\+\S+)')
                project_data = [m.groupdict() for m in project_r.finditer(task_txt)]

                context_r = re.compile(r' (?P<context>@\S+)')
                context_data = [m.groupdict() for m in context_r.finditer(task_txt)]

                task = task_data.groupdict()
                task['is_important'] = False

                subject = task.get('subject', '???')

                # remove any special key-val strings, project and context tags from the subject text for clarity
                subject = re.sub(special_kv_r, "", subject)
                subject = re.sub(project_r, "", subject)
                subject = re.sub(context_r, "", subject)

                category = self.COLUMN_0_NAME

                category_map = {
                    self.KANBAN_VAL_IN_PROGRESS: self.COLUMN_1_NAME,
                    self.KANBAN_VAL_VALIDATION: self.COLUMN_2_NAME,
                }

                for i in range(0, len(special_kv_data)):
                    kv = special_kv_data[i]
                    if kv['key'] == self.KANBAN_KEY:
                        v = kv['val']
                        if v in category_map.keys():
                            category = category_map[v]
                            break

                if task.get("isDone"):
                    category = self.COLUMN_3_NAME

                priority = None
                if task.get("priority"):
                    priority = task['priority'][1]  # get only letter without parenthesis

                tasks[category].append(task)

                start_date = None
                end_date = None
                if task.get('dates'):
                    dates = []
                    dates = task.get('dates').split(' ')
                    if len(dates) == 1:
                        start_date = date.fromisoformat(dates[0])
                    elif len(dates) == 2:
                        start_date = date.fromisoformat(dates[1])
                        end_date = date.fromisoformat(dates[0])

                card_bg = self.COLORS['card-background']
                font=tkFont.nametofont('main'),
                #font = 'main'
                #font=('Ubuntu',8)
                # gwyrdh working on apply done styling
                #if category == 'Done':
                if category == self.COLUMN_3_NAME:
                	#gwyrdh done card background
                    card_bg = self.COLORS['column0-column']
                    #card_bg = self.COLORS['done-card-background']
                    # gwyrdh set font in code
                    #font = ('Ubuntu',16)
                    #font=("Ubuntu", self.card_font_size + 4)
                    font = 'done-task'
                    #font=tkFont.nametofont('done-task')
                    #font=tkFont.nametofont('h2')

                card_parent = self.ui_columns[category].content

                cards_data.append({
                    'parent': card_parent,
                    'subject': subject,
                    'bg': card_bg,
                    'font': font,
                    'project': project_data,
                    'context': context_data,
                    'start_date': start_date,
                    'end_date': end_date,
                    'state': category,
                    'name': "task#" + str(index + 1),
                    'special_kv_data': special_kv_data,
                    'priority': priority,
                    'index': index,
                    'raw_txt': task_txt
                })

        sort_method = SORT_METHODS[self.sort_method_idx]
        cards_data.sort(key=sort_method['f'], reverse=sort_method['rev'])
        for card in cards_data:
            index = card['index']
            if self.filter is not None:
                index = self.non_filtered_content_line_mapping[index]
            self.draw_card(
                card['parent'],
                card['subject'],
                card['bg'],
                card['font'],
                project=card['project'],
                context=card['context'],
                start_date=card['start_date'],
                end_date=card['end_date'],
                state=card['state'],
                name=card['name'],
                special_kv_data=card['special_kv_data'],
                priority=card['priority'],
                index=index,
            )

        # Compute proportion for each column tasks and update progress bars
        tasks_number = {}
        for col in self.COLUMNS_NAMES:
            tasks_number[col] = len(tasks[col])

        total_tasks = 0

        for key, number in tasks_number.items():
            total_tasks += number

        if total_tasks > 0:
            percentages = {}
            for col in self.COLUMNS_NAMES:
                percentages[col] = tasks_number[col] / total_tasks

            bar_x = 0

            for key, progress_bar in self.progress_bars.items():
                progress_bar['bar'].place(relx=bar_x, relwidth=percentages[key], relheight=1)
                label_text = f"{tasks_number[key]}"
                progress_bar['label'].config(text=label_text)
                bar_x += percentages[key]

        for ui_column_name, ui_column in self.ui_columns.items():
            tmp_frame = tk.Frame(ui_column.content, width=0, height=0)
            tmp_frame.pack()
            ui_column.content.update()
            tmp_frame.destroy()
            ui_column.content.pack(side='top', padx=10, pady=(0,10), fill='x')
        
        self.update_editor_line_colors()

        self.main_window.update()

        return tasks;


    def draw_card(
        self,
        parent,
        subject,
        bg,
        # gwyrdh no change here
        font='main',
        #font=('Ubuntu',6),
        project=None,
        context=None,
        start_date=None,
        end_date=None,
        state=None,
        name="",
        special_kv_data=None,
        priority=None,
        index=None
    ):
        def bind_highlight_and_drag_n_drop(widget):
            widget.bind('<Button-1>', self.on_click)
            widget.bind('<B1-Motion>', self.on_drag_init)
            widget.bind('<ButtonRelease>', self.on_drop)

        def get_widget_name(subject_name):
            ret_name = str(get_widget_name.counter) + subject_name
            get_widget_name.counter += 1
            return ret_name
        get_widget_name.counter = 0

        # Create the card frame
        ui_card_highlight = tk.Frame(parent, bd=2, bg=self.COLORS['column1-column'], height=200, name="highlightFrame"+name)
        ui_card = tk.Frame(ui_card_highlight, bd=0, bg=bg, height=200, cursor='hand2', name=get_widget_name(name))

        subject_padx = 10

        # If needed, add a color border for priority marking
        if priority is not None and self.show_priority:
            prio_color = self.get_priority_color(priority)
            important_border = tk.Frame(ui_card, bg=prio_color, width="3", name=get_widget_name(name))
            bind_highlight_and_drag_n_drop(important_border)
            important_border.pack(side="left", fill='y')
            important_label = tk.Label(
                ui_card,
                text=priority,
                fg=prio_color,
                bg=ui_card['bg'],
                anchor=tk.W,
                font=tkFont.Font(family='Ubuntu', size=self.card_font_size + 8, weight=tkFont.BOLD),
                name=get_widget_name(name)
            )
            important_label.pack(side="left", anchor=tk.NW, padx=0, pady=(5,0))
            bind_highlight_and_drag_n_drop(important_label)
            subject_padx = 0

        if self.show_content:
            card_label = tk.Label(
                ui_card, 
                text=subject, 
                fg=self.COLORS['main-text'], 
                bg=ui_card['bg'], 
                anchor=tk.W, 
                wraplength=200, 
                justify='left',
                # gwyrdh remove font size from self.card
                #font=(font, self.card_font_size),
                font=('Ubuntu',11),
                name=get_widget_name(name)
            )

            # Adapt elide length when width change
            card_label.bind("<Configure>", self.on_card_width_changed)
            bind_highlight_and_drag_n_drop(card_label)
            card_label.pack(padx=subject_padx, pady=5, fill='x', side="top", anchor=tk.W)

        # If needed, show the task duration
        if start_date and self.show_date:
            duration = 0
            if not end_date:
                end_date = self.current_date

            duration = end_date.toordinal() - start_date.toordinal()
            duration_string = "%d days" % (duration)

            duration_label = tk.Label(
                ui_card, 
                text = duration_string,
                fg=self.COLORS[state], 
                bg=ui_card['bg'], 
                anchor=tk.W, 
                justify='left',
                font=("Ubuntu", self.card_font_size - 2),
                wraplength=85,
                name=get_widget_name(name)
            )
            if (project or context) and (len(project) > 0 or len(context) > 0):
                duration_label.pack(side="top", anchor=tk.NW, padx=10, pady=0)
            else:
                duration_label.pack(side="top", anchor=tk.NW, padx=10, pady=(0,2))
            bind_highlight_and_drag_n_drop(duration_label)

        # Add project and context tags if needed
        if project and len(project) > 0 and self.show_project:
            project_string = ", ".join([p["project"] for p in project])
            project_label = tk.Label(
                ui_card, 
                text=project_string, 
                fg=self.COLORS["project"], 
                bg=ui_card['bg'], 
                anchor=tk.E,
                name=get_widget_name(name),
                # gwyrdh change to -1
                font=('Ubuntu', self.card_font_size - 1),
                wraplength=200,
                justify='left',
            )
            project_label.pack(padx=10, pady=2, fill='x', side="top", anchor=tk.E)
            bind_highlight_and_drag_n_drop(project_label)

        if context and len(context) > 0 and self.show_context:
            context_string = ", ".join([c["context"] for c in context])
            context_label = tk.Label(
                ui_card, 
                text=context_string, 
                fg=self.COLORS['context'], 
                bg=ui_card['bg'], 
                anchor=tk.E,
                name=get_widget_name(name),
                font=('Ubuntu', self.card_font_size - 1),
                wraplength=200,
                justify='left',
            )
            context_label.pack(padx=10, pady=2, fill='x', side="top", anchor=tk.E)
            bind_highlight_and_drag_n_drop(context_label)

        if special_kv_data is not None and len(special_kv_data) > 0 and self.show_special_kv_data:
            special_kv_data_string = ", ".join([f"{special_kv_data_entry['key']}:{special_kv_data_entry['val']}" for
                                                special_kv_data_entry in special_kv_data])
            special_kv_entry_label = tk.Label(
                ui_card,
                text=special_kv_data_string,
                fg=self.COLORS['kv-data'],
                bg=ui_card['bg'],
                anchor=tk.E,
                name=get_widget_name(name),
                font=('Ubuntu', self.card_font_size - 2),
                wraplength=200,
                justify='left',
            )
            special_kv_entry_label.pack(padx=10, pady=2, fill='x', side="top", anchor=tk.E)
            bind_highlight_and_drag_n_drop(special_kv_entry_label)

        if index is not None and self.show_index:
            index_string = f"#{index}"
            index_va = tk.StringVar(value=index_string)
            index_label = tk.Entry(
                ui_card,
                fg=self.COLORS['kv-data'],
                bg=ui_card['bg'],
                name=get_widget_name(name),
                font=('Ubuntu', self.card_font_size - 2),
                textvariable=index_va,
                borderwidth=0,
                state="readonly",
                readonlybackground=ui_card['bg'],
            )
            index_label.pack(padx=0, pady=2, side="top", anchor=tk.W)

        ui_card.pack(padx=1, pady=(0, 10), side="top", fill='x', expand=1, anchor=tk.NW)
        ui_card_highlight.pack(padx=0, pady=(0, 1), side="top", fill='x', expand=1, anchor=tk.NW)
        bind_highlight_and_drag_n_drop(ui_card)

        return ui_card

    def on_control_scroll(self, event):
        delta = (event.delta/120)
        new_font_size = self.card_font_size + int(delta)
        if new_font_size <= 4:
            new_font_size = 4
        if new_font_size != self.card_font_size:
            self.card_font_size = new_font_size
            self.reload_ui_from_text()
            self.store_in_config(self.CONFIG_KEY_FONT_SIZE, new_font_size)
            self.save_config_file()
        return "break"

    def open_file_dialog(self, event=None):
        """Open a dialog to select a file to load"""
        self.file = filedialog.askopenfilename(
            initialdir='.', 
            filetypes=[("todo list file", "*todo.txt"), ("txt file", "*.txt")],
            title='Choose a todo list to display')
        self.load_txt_file()

    def apply_filter(self, event=None):
        self.filter_frame.configure(bg=self.COLORS['project'])
        self.clear_filter_button.configure(bg='red')
        self.filter = self.filter_entry_box.get()
        non_filtered_lines = self.non_filtered_content.split('\n')
        self.non_filtered_content_line_mapping = []
        filtered_content = []
        if self.non_filtered_content is not None:
            for i in range(len(non_filtered_lines)):
                line = non_filtered_lines[i]

                if self.use_regex_val.get():
                    is_this_line_included = len(re.findall(self.filter, line)) > 0
                else:
                    is_this_line_included = self.filter.casefold() in line.casefold()

                if is_this_line_included:
                    filtered_content.append(line)
                    self.non_filtered_content_line_mapping.append(i)

        filtered_text = '\n'.join(filtered_content)
        self.reload_ui_from_text(filtered_text, f"KanbanTxt - {pathlib.Path(self.file).name} !! FILTER VIEW ACTIVE !!")
        self.text_editor.edit_reset()
        self.text_editor.mark_set('insert', "1.0")
        self.schedule_update_of_editor_line_colors()
        self.text_editor.see('insert')
        if self.filter_view_message is not None:
            self.remove_custom_tooltip(self.filter_view_message)
        self.filter_view_message = self.add_custom_tooltip(self.filter_frame, f" Filter view: showing {len(filtered_content)} of {len(non_filtered_lines)} tasks ")
        for widget in self.widgets_for_disable_in_filter_mode:
            if widget['state'] == 'disabled':
                widget.config(state='normal')
            else:
                widget.config(state='disabled')

    def clear_filter(self):
        self.non_filtered_content = self.merge_filtered_with_original()
        self.filter = None
        if self.filter_view_message is not None:
            self.remove_custom_tooltip(self.filter_view_message)
        self.filter_view_message = None
        for widgets in self.widgets_for_disable_in_filter_mode:
            if widgets['state'] == 'disabled':
                widgets.config(state='normal')
            else:
                widgets.config(state='disabled')

        self.filter_frame.configure(bg=self.COLORS['editor-background'])
        self.clear_filter_button.configure(bg=self.COLORS['main-text'])

        if self.non_filtered_content is not None:
            editor_insert_address = self.text_editor.index(tk.INSERT)
            selected_line = int(editor_insert_address.split('.')[0])
            self.reload_ui_from_text(self.non_filtered_content, f"KanbanTxt - {pathlib.Path(self.file).name}")
            self.text_editor.edit_reset()
            line_number_to_select = 0
            if self.non_filtered_content_line_mapping is not None and selected_line <= len(self.non_filtered_content_line_mapping):
                line_number_to_select = self.non_filtered_content_line_mapping[selected_line-1]
            self.text_editor.mark_set('insert', f"{line_number_to_select + 1}.0")
            self.schedule_update_of_editor_line_colors(None)
            self.text_editor.see('insert')
            self.reload_and_save()

    def merge_filtered_with_original(self):
        if self.filter is None:
            return self.non_filtered_content

        filtered_content = self.text_editor.get("1.0", "end-1c").split('\n')
        non_filtered_content = self.non_filtered_content.split('\n')

        for i in range(len(filtered_content)):
            if i < len(self.non_filtered_content_line_mapping):
                target_index = self.non_filtered_content_line_mapping[i]
                non_filtered_content[target_index] = filtered_content[i]
        return '\n'.join(non_filtered_content)

    def load_txt_file(self):
        if os.path.isfile(self.file):
            content = self.fread(self.file)
            title = f"KanbanTxt - {pathlib.Path(self.file).name}"
            self.non_filtered_content = content
            self.reload_ui_from_text(content, title)
    
    def reload_ui_from_text(self, text=None, title=None):
        if text is None:
            text = self.text_editor.get("1.0", "end-1c")
        self.text_editor.delete('1.0', 'end')
        self.text_editor.insert(tk.INSERT, text)
        self.text_editor.focus()
        self.text_editor.mark_set('insert', 'end')
        self.text_editor.see('insert')
        todo_cards = self.parse_todo_txt(text)
        if title is not None:
            self.main_window.title(title)

    def reload_and_save(self, event=None):
        """Reload the kanban and save the editor content in the current todo.txt
            file """
        was_filter_active = self.filter is not None
        editor_insert_address = self.text_editor.index(tk.INSERT)
        selected_line = int(editor_insert_address.split('.')[0])
        if was_filter_active:
            self.clear_filter()

        self.non_filtered_content = self.text_editor.get("1.0", "end-1c")

        if self.file:
            self.fwrite(self.file, self.non_filtered_content)

        if was_filter_active:
            self.apply_filter()
        else:
            self.parse_todo_txt(self.non_filtered_content)

        self.text_editor.mark_set('insert', f"{selected_line}.0")
        self.text_editor.see('insert')


    def reload_and_create_file(self, event=None):
        """In case no file were open, open a dialog to choose where to save the 
            current data"""
        if not os.path.isfile(self.file):
            new_file = filedialog.asksaveasfile(
                initialdir='.',
                defaultextension='.todo.txt',
                title='Choose a location to save your todo list',
                confirmoverwrite=True,
                filetypes=[('todo list file', '*todo.txt')])
            
            if not new_file:
                return

            # just create the file
            self.file = new_file.name
            new_file.close()
            
            # as tk does'nt support double extensions, we have to write it here
            file_path, extension = os.path.splitext(self.file)
            if extension != 'todo.txt':
                os.rename(self.file, file_path + '.todo.txt')
                self.file = file_path + '.todo.txt'
        
        self.reload_and_save()


    # BINDING CALLBACKS

    def adapt_canvas_to_window(self, event):
        """Resize canvas when window is resized"""
        canvas_width = event.width
        self.content_canvas.itemconfig(self.canvas_frame, width = canvas_width)
                
    def hide_content(self):
        self.progress_bar.pack_forget()
        self.kanban_frame.pack_forget()


    def display_content(self):
        self.progress_bar.pack(side='top', fill='x', padx=10, pady=10)
        self.kanban_frame.pack(fill='both')


    def on_card_width_changed(self, event):
        """Adapt todo cards text wrapping when the window is resized"""
        event.widget['wraplength'] = event.width - 20
    

    def bind_to_mousewheel(self, event):
        """Allow scroll event while pointing the kanban frame"""
        # with Windows OS
        event.widget.bind_all("<MouseWheel>", self.scroll)
        # with Linux OS
        event.widget.bind_all("<Button-4>", self.scroll)
        event.widget.bind_all("<Button-5>", self.scroll)
    

    def unbind_to_mousewheel(self, event):
        """Disable scroll event while not pointing the kanban frame"""
        # with Windows OS
        event.widget.unbind_all("<MouseWheel>")
        # with Linux OS
        event.widget.unbind_all("<Button-4>")
        event.widget.unbind_all("<Button-5>")


    def scroll(self, event):
        """Scroll through the kanban frame"""
        self.content_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_switch_darkmode(self, event):
        """Switch from light and dark mode, destroy the UI and recreate it to
            apply the modification"""
        if self.filter is not None:
            return
        self.darkmode = not self.darkmode
        self.recreate_main_window()

    def recreate_main_window(self):
        window_geometry = self.main_window.geometry()
        window_state = self.main_window.state()
        width, height, x, y = re.split("[x+]", window_geometry)

        self.main_window.destroy()
        self.draw_ui(int(width), int(height), int(x), int(y))
        self.main_window.state(window_state)
        self.store_in_config(self.CONFIG_KEY_DARKMODE, self.darkmode)
        self.save_config_file()

    def move_line_up(self, event=None):
        if self.filter is not None:
            return
        current_line = self.text_editor.get("insert linestart", "insert lineend")
        self.text_editor.delete("insert linestart", "insert lineend + 1c")
        self.text_editor.insert("insert linestart -1l", current_line + '\n')
        if event:
            self.text_editor.mark_set('insert', 'insert linestart -1l')
        else:
            self.text_editor.mark_set('insert', 'insert linestart -2l')

        self.update_editor_line_colors()

    def move_line_down(self, event=None):
        if self.filter is not None:
            return
        current_line = self.text_editor.get("insert linestart", "insert lineend")
        self.text_editor.delete("insert linestart", "insert lineend + 1c")
        self.text_editor.insert("insert linestart +1l", current_line + '\n')
        if event:
            self.text_editor.mark_set('insert', 'insert lineend')
        else:
            self.text_editor.mark_set('insert', 'insert lineend +1l')

        self.update_editor_line_colors()

    def remove_line(self, event=None):
        if self.filter is not None:
            return
        self.text_editor.delete("insert linestart", "insert lineend + 1c")

    def set_state(self, task, newState):
        task = re.sub(rf'\s{self.KANBAN_KEY}:[^\s^:]+', '', task)
        task = re.sub(r'^x ', '', task)
        task = re.sub(r'^ ', '', task)
        if newState == 'x':
            task = newState + ' ' + task
        else:
            task = task + newState
        return task

    def set_priority(self, task, new_priority):
        priority_done_r = re.compile(r'^x \([A-Z]\) ')
        priority_not_done_r = re.compile(r'^\([A-Z]\) ')
        had_priority = True if re.match(priority_done_r, task) or re.match(priority_not_done_r, task) else False
        is_done = True if re.match(r'^x ', task) else False

        if is_done:
            if had_priority:
                result = f"x {re.sub(priority_done_r, new_priority, task)}"
            else:
                task_without_done_marking = task[2:]
                result = f"x {new_priority}{task_without_done_marking}"
        else:
            if had_priority:
                result = re.sub(priority_not_done_r, new_priority, task)
            else:
                result = f"{new_priority}{task}"
        return result

    def set_editor_line_state(self, new_state):
        current_line = self.text_editor.get("insert linestart", "insert lineend")
        current_line = self.set_state(current_line, new_state)

        # if edit is made in the last line, temporarily add a newline at the end, to avoid
        # line shifting when deleting and inserting the current_line
        cursor_address = self.text_editor.index(tk.INSERT)
        cursor_line = int(cursor_address.split('.')[0])
        last_line_address = self.text_editor.index('end')
        last_line = int(last_line_address.split('.')[0])
        is_in_last_line = cursor_line == last_line - 1
        if is_in_last_line:
            self.text_editor.insert("end", "\n")
        self.text_editor.delete("insert linestart", "insert lineend + 1c")
        self.text_editor.insert("insert linestart", current_line + '\n')
        self.text_editor.mark_set('insert', 'insert linestart -1l')
        if is_in_last_line:
            self.text_editor.delete("end-1l linestart", "end-1l lineend + 1c")
        self.reload_and_save()

    def set_editor_line_priority(self, new_priority_override=None):
        current_line = self.text_editor.get("insert linestart", "insert lineend")
        if new_priority_override is None:
            priority_match = re.match(r'^(?P<isDone>x )?(?P<priority>\([A-Z]\))?', current_line)
            highest_prio = 'A'
            lowest_prio = 'E'
            new_priority = f"({lowest_prio}) "
            if priority_match['priority']:
                current_priority = priority_match['priority']
                current_priority_code = ord(current_priority[1])
                new_priority_code = current_priority_code - 1
                if current_priority_code == ord(highest_prio):
                    new_priority = ""
                else:
                    if new_priority_code < ord(highest_prio):
                        new_priority_code = ord(lowest_prio)
                    new_priority = f"({chr(new_priority_code)}) "
        else:
            if len(new_priority_override) > 0:
                new_priority = f"({new_priority_override}) "
            else:
                new_priority = f""

        current_line = self.set_priority(current_line, new_priority)
        # if edit is made in the last line, temporarily add a newline at the end, to avoid
        # line shifting when deleting and inserting the current_line
        cursor_address = self.text_editor.index(tk.INSERT)
        cursor_line = int(cursor_address.split('.')[0])
        last_line_address = self.text_editor.index('end')
        last_line = int(last_line_address.split('.')[0])
        is_in_last_line = cursor_line == last_line - 1
        if is_in_last_line:
            self.text_editor.insert("end", "\n")
        self.text_editor.delete("insert linestart", "insert lineend + 1c")
        self.text_editor.insert("insert linestart", current_line + '\n')
        self.text_editor.mark_set('insert', 'insert linestart -1l')
        if is_in_last_line:
            self.text_editor.delete("end-1l linestart", "end-1l lineend + 1c")
        self.reload_and_save()

    def move_to_todo(self, event=None):
    	# gwyrdh changed from ' ' 
        self.set_editor_line_state(" ")

    def change_priority_to_A(self):
        self.change_priority(None, "A")

    def change_priority_to_B(self):
        self.change_priority(None, "B")

    def change_priority_to_C(self):
        self.change_priority(None, "C")
    def change_priority_to_D(self):
        self.change_priority(None, "D")

    def change_priority_to_E(self):
        self.change_priority(None, "E")

    def change_priority(self, event=None, new_priority=None):
        self.set_editor_line_priority(new_priority)

    def move_to_in_progress(self, event=None):
        self.set_editor_line_state(f' {self.KANBAN_KEY}:{self.KANBAN_VAL_IN_PROGRESS}')

    def move_to_validation(self, event=None):
        self.set_editor_line_state(f' {self.KANBAN_KEY}:{self.KANBAN_VAL_VALIDATION}')

    def move_to_done(self, event=None):
    	# gwyrdh tried to find font change
        #font=tkFont.Font(family="Helvetica",size=36,weight="bold")
        #font.setStrikeOut(True)
        #font=('Ubuntu', 6)
        # font=tkFont.nametofont('done-task')
		# gwyrdh added to remove priority
        self.change_priority(None, "")
    	# gwyrdh added add date to X
        current_line = self.text_editor.get("insert linestart", "insert lineend")
        match = re.match(r'x|\([A-C]\) ', current_line)
        insert_index = 0
        if match:
            insert_index = match.end()
        
        self.text_editor.insert("insert linestart +%dc" % (insert_index), str(self.current_date) + " ")
        
        self.set_editor_line_state('x')

    def add_date(self, event=None):
        current_line = self.text_editor.get("insert linestart", "insert lineend")
        match = re.match(r'x|\([A-C]\) ', current_line)
        insert_index = 0
        if match:
            insert_index = match.end()
        
        self.text_editor.insert("insert linestart +%dc" % (insert_index), str(self.current_date) + " ")
    

    def on_window_resize(self, event):
        self.hide_content()
        
        if self._after_id:
            self.main_window.after_cancel(self._after_id)
        
        self._after_id = self.main_window.after(100, self.update_canvas, event)


    def update_canvas(self, event):
        self.content_canvas.itemconfig(self.canvas_frame, width = event.width)

        if event.width < 700:
            index = 1
            for column_name, column in self.ui_columns.items():
                column.grid(
                    row=index, column=0, pady=10, sticky='nwe', columnspan=4)
                index += 1
            
        else:
            index = 0
            for column_name, column in self.ui_columns.items():
                column.grid(
                    row=1, column=index, padx=10, sticky='nwe', columnspan=1)
                index += 1

        self.display_content()
        pass

    def is_deletion_forbidden(self, is_removing_rhs=False):
        allow_delete = True
        cursor_address = self.text_editor.index(tk.INSERT)
        cursor_row = int(cursor_address.split('.')[1])
        forbidden_row = 0
        if is_removing_rhs:
            cursor_line = int(cursor_address.split('.')[0])
            last_row_address = self.text_editor.index(f'{cursor_line}.end')
            last_row = int(last_row_address.split('.')[1])
            forbidden_row = last_row

        current_line_text = self.text_editor.get("insert linestart", "insert lineend")
        # we don't allow deletion, when:
        #   - user have selected the whole text in line,
        #   - user have selected text in a way that after its deletion there will be empty line or only whitespace left,
        #   - user is at the forbidden row of the line (e.g. last row for 'delete' button),
        #   - there will be no non-whitespace left after deletion.
        if self.text_editor.tag_ranges(tk.SEL):
            selected_text_in_line = self.text_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
            text_left_begin = self.text_editor.get("insert linestart", tk.SEL_FIRST)
            text_left_end = self.text_editor.get(tk.SEL_LAST, "insert lineend")
            text_combined = text_left_begin + text_left_end
            if len(text_combined.strip()) == 0:
                allow_delete = False
        else:
            if cursor_row == forbidden_row:
                allow_delete = False
            else:
                deleted_char_index = cursor_row if is_removing_rhs else cursor_row - 1
                text_after_deletion = current_line_text[0:deleted_char_index] + current_line_text[deleted_char_index+1:]
                if len(text_after_deletion.strip()) == 0:
                    allow_delete = False
        return not allow_delete

    def show_task_deletion_warning(self):
        return tk.messagebox.askyesno(default=tk.messagebox.NO, title="Deleting task", message="You are about to delete a task.\n"
                                                                                               "This will make an impact on the tasks IDs.\n\n"
                                                                                               "Do you want to proceed with removal?")

    def on_backspace_pressed(self, event=None):
        if self.filter is None:
            if self.ask_for_delete and self.is_deletion_forbidden(is_removing_rhs=False):
                response = self.show_task_deletion_warning()
                if response == False:
                    return "break"
            self.schedule_update_of_editor_line_colors(event)
            return
        if self.is_deletion_forbidden(is_removing_rhs=False):
            self.flash_editor_warning_tooltip("Can't remove tasks when the filter view is active!")
            return "break"

    def on_whitespace_pressed(self, event=None):
        # don't allow to replace the whole line with whitespace in filter view
        if self.text_editor.tag_ranges(tk.SEL):
            text_left_begin = self.text_editor.get("insert linestart", tk.SEL_FIRST)
            text_left_end = self.text_editor.get(tk.SEL_LAST, "insert lineend")
            text_combined = text_left_begin + text_left_end
            if len(text_combined.strip()) == 0:
                if self.filter is not None:
                    self.flash_editor_warning_tooltip("Can't remove tasks when the filter view is active!")
                    return "break"
                elif self.ask_for_delete:
                    response = self.show_task_deletion_warning()
                    if response == False:
                        return "break"

    def on_delete_pressed(self, event=None):
        if self.filter is None:
            if self.ask_for_delete and self.is_deletion_forbidden(is_removing_rhs=True):
                response = self.show_task_deletion_warning()
                if response == False:
                    return "break"
            self.schedule_update_of_editor_line_colors(event)
            return

        if self.is_deletion_forbidden(is_removing_rhs=True):
            self.flash_editor_warning_tooltip("Can't remove tasks when the filter view is active!")
            return "break"

    def on_return_pressed(self, event=None):
        cursor_pos = self.text_editor.index(tk.INSERT)

        if self.filter is None:
            if self.ask_for_add:
                end_pos = self.text_editor.index(tk.END)
                cursor_line = int(cursor_pos.split('.')[0])
                end_line = int(end_pos.split('.')[0])
                response = False
                if cursor_line != end_line - 1:
                    response = tk.messagebox.askyesnocancel(title="Add new task", message="You are creating new task in the middle of the txt file.\n"
                                                                                          "This will make an impact on the tasks IDs.\n\n"
                                                                                          "Do you want to add it at the end [Yes] or at the current cursor position [No]?")
                if response is None:  # cancel
                    return "break"
                elif response is False:  # do not move, stay here
                    pass
                elif response is True:  # move to the end
                    self.text_editor.mark_set(tk.INSERT, tk.END)
            self.main_window.after(100, self.reload_and_save)
            return

        self.reload_ui_from_text()
        self.text_editor.mark_set('insert', cursor_pos)
        self.text_editor.see('insert')
        self.update_editor_line_colors()
        self.flash_editor_warning_tooltip("Can't add new tasks when the filter view is active!")
        return "break"

    def schedule_update_of_editor_line_colors(self, event=None):
        self.main_window.after(100, self.update_editor_line_colors)

    def update_editor_line_colors(self, event=None):
        nb_line = int(self.text_editor.index('end-1c').split('.')[0])

        selected_line = int(self.text_editor.index(tk.INSERT).split('.')[0])
        task_card_found = False
        columns = self.kanban_frame.winfo_children()
        for column in columns:
            if task_card_found:
                break
            task_cards = column.winfo_children()[2].winfo_children()
            for task_card in task_cards:
                if task_card.winfo_name().endswith(f"task#{selected_line}"):
                    self.highlight_selected_task_card(task_card)
                    task_card_found = True
                    break
        if not task_card_found:
            self.highlight_selected_task_card(None)

        for line_idx in range(nb_line + 1):
            self.text_editor.tag_remove('pair', str(line_idx) + '.0', str(line_idx) + '.0 lineend +1c')
            self.text_editor.tag_remove('current_pos', str(line_idx) + '.0', str(line_idx) + '.0 lineend +1c')
            if line_idx == selected_line:
                self.text_editor.tag_add('current_pos', str(line_idx) + '.0', str(line_idx) + '.0 lineend +1c')
            elif line_idx % 2 == 0:
                self.text_editor.tag_add('pair', str(line_idx) + '.0', str(line_idx) + '.0 lineend +1c')

    def get_task_card_frame_widget(self, any_subwidget):
        # get first parent which starts with "highlightFrame" in its name
        selected_task_card_frame = None
        parent = any_subwidget
        max_depth = 5
        for i in range(0, max_depth):
            if parent is None:
                break
            if parent.winfo_name().startswith("highlightFrame"):
                selected_task_card_frame = parent
                break
            parent = parent.master
        return selected_task_card_frame

    def highlight_selected_task_card(self, selected_widget):
        # get first parent which starts with "highlightFrame" in its name
        selected_highlight_frame = self.get_task_card_frame_widget(selected_widget)

        if self.selected_task_card is not None:
            try:
                self.selected_task_card.configure(background=self.COLORS[f'column3-column'])
            except:
                self.selected_task_card = None

        if selected_highlight_frame is not None:
            selected_highlight_frame.configure(background=self.COLORS['project'])
            self.selected_task_card = selected_highlight_frame

    def highlight_task(self, event):
        self.clear_drop_areas_frame()
        selected_widget = event.widget
        self.highlight_selected_task_card(selected_widget)
        searched_task_line = selected_widget.winfo_name()[1:].replace("task#", "")
        self.text_editor.mark_set('insert', searched_task_line + ".end")
        self.text_editor.see('insert')
        self.schedule_update_of_editor_line_colors()

    def get_priority_color(self, current_priority):
        index = ord(current_priority) - ord('A')
        if index >= len(self.COLORS['priority_color_scale']) or index < 0:
            index = -1
        return self.COLORS['priority_color_scale'][index]

    def add_custom_tooltip(self, widget, text):
        x, y, _, _ = widget.bbox("insert")
        abs_rootx = self.main_window.winfo_rootx()
        abs_rooty = self.main_window.winfo_rooty()
        rootx = widget.winfo_rootx()
        rooty = widget.winfo_rooty()
        x += rootx - abs_rootx + 5
        y += rooty - abs_rooty - 20
        custom_tooltip = tk.Label(text=text, background="lightyellow", relief="solid", borderwidth=1, font=(main, 12))
        custom_tooltip.place(x=x, y=y)
        return custom_tooltip

    def remove_custom_tooltip(self, tooltip):
        tooltip.place_forget()

    def flash_editor_warning_tooltip(self, text):
        if self.editor_warning_tooltip is not None:
            self.hide_editor_warning_tooltip()
        self.text_editor.bell()
        self.editor_warning_tooltip = self.add_custom_tooltip(self.text_editor, text)
        self.main_window.after(2000, self.hide_editor_warning_tooltip)

    def hide_editor_warning_tooltip(self):
        if self.editor_warning_tooltip is not None:
            self.remove_custom_tooltip(self.editor_warning_tooltip)
            self.editor_warning_tooltip = None


def main(args):
    
    app = KanbanTxtViewer(args.file, args.darkmode)
    if os.name == 'nt':
        app.main_window.state('zoomed')
    app.main_window.mainloop()
    

if __name__ == '__main__':
    if os.name == 'nt':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('KanbanTxt')
    arg_parser = argparse.ArgumentParser(description='Display a todo.txt file as a kanban and allow to edit it')
    arg_parser.add_argument('--file', help='Path to a todo.txt file', required=False, default='', type=str)
    arg_parser.add_argument('--darkmode', help='Is the UI should use dark theme', required=False, default=None, action='store_true')
    args = arg_parser.parse_args()
    main(args)
