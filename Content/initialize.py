# -*- coding: utf-8 -*-
"""
初始化 unreal Qt 环境
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2020-05-30 21:47:47'

import os
import sys
import json
import time
import posixpath

from functools import partial
from collections import OrderedDict

import unreal
from Qt import QtCore, QtWidgets, QtGui
from dayu_widgets import dayu_theme


DIR = os.path.dirname(__file__)
menus = unreal.ToolMenus.get()

global last_tick
last_tick = time.time()

FORMAT_ARGS = {
    "Content": DIR
}

COMMAND_TYPE = {
    "COMMAND": unreal.ToolMenuStringCommandType.COMMAND,
    "PYTHON": unreal.ToolMenuStringCommandType.PYTHON,
    "CUSTOM": unreal.ToolMenuStringCommandType.CUSTOM,
}

INSERT_TYPE = {
    "AFTER": unreal.ToolMenuInsertType.AFTER,
    "BEFORE": unreal.ToolMenuInsertType.BEFORE,
    "DEFAULT": unreal.ToolMenuInsertType.DEFAULT,
    "FIRST": unreal.ToolMenuInsertType.FIRST,
}

MENU_TYPE = {
    "BUTTON_ROW": unreal.MultiBoxType.BUTTON_ROW,
    "MENU": unreal.MultiBoxType.MENU,
    "MENU_BAR": unreal.MultiBoxType.MENU_BAR,
    "TOOL_BAR": unreal.MultiBoxType.TOOL_BAR,
    "TOOL_MENU_BAR": unreal.MultiBoxType.TOOL_MENU_BAR,
    "UNIFORM_TOOL_BAR": unreal.MultiBoxType.UNIFORM_TOOL_BAR,
    "VERTICAL_TOOL_BAR": unreal.MultiBoxType.VERTICAL_TOOL_BAR,
}

ENTRY_TYPE = {
    "BUTTON_ROW": unreal.MultiBlockType.BUTTON_ROW,
    "EDITABLE_TEXT": unreal.MultiBlockType.EDITABLE_TEXT,
    "HEADING": unreal.MultiBlockType.HEADING,
    "MENU_ENTRY": unreal.MultiBlockType.MENU_ENTRY,
    "MENU_SEPARATOR": unreal.MultiBlockType.MENU_SEPARATOR,
    "NONE": unreal.MultiBlockType.NONE,
    "TOOL_BAR_BUTTON": unreal.MultiBlockType.TOOL_BAR_BUTTON,
    "TOOL_BAR_COMBO_BUTTON": unreal.MultiBlockType.TOOL_BAR_COMBO_BUTTON,
    "TOOL_BAR_SEPARATOR": unreal.MultiBlockType.TOOL_BAR_SEPARATOR,
    "WIDGET": unreal.MultiBlockType.WIDGET,
}

ACTION_TYPE = {
    "BUTTON": unreal.UserInterfaceActionType.BUTTON,
    "CHECK": unreal.UserInterfaceActionType.CHECK,
    "COLLAPSED_BUTTON": unreal.UserInterfaceActionType.COLLAPSED_BUTTON,
    "NONE": unreal.UserInterfaceActionType.NONE,
    "RADIO_BUTTON": unreal.UserInterfaceActionType.RADIO_BUTTON,
    "TOGGLE_BUTTON": unreal.UserInterfaceActionType.TOGGLE_BUTTON,
}


def handle_menu(data):
    """
    handle_menu 递归生成菜单
    """
    menu = data.get("menu")
    if not menu:
        return

    for section, config in data.get("section", {}).items():
        config = config if isinstance(config, dict) else {"label": config}
        config.setdefault("label", "untitle")
        # NOTE 如果存在 insert_type 需要将字符串转换
        insert = INSERT_TYPE.get(config.get("insert_type", "").upper())
        if insert:
            config["insert_type"] = insert
        insert_name = config.get("insert_name")
        config["insert_name"] = insert_name if insert_name else "None"
        menu.add_section(section, **config)

    for prop, value in data.get("property", {}).items():
        if prop == "menu_owner" or value == "":
            continue
        elif prop == "menu_type":
            value = MENU_TYPE.get(value.upper())
        menu.set_editor_property(prop, value)

    for entry_name, config in data.get("entry", {}).items():
        prop = config.get("property", {})

        for k, v in prop.items():
            # NOTE 跳过 owner 和 script_object
            prop.pop("owner") if not prop.get("owner") is None else None
            prop.pop("script_object") if not prop.get("script_object") is None else None
            
            if v == '':
                prop.pop(k)
            elif k == "insert_position":
                position = INSERT_TYPE.get(v.get("position", "").upper())
                v["position"] = position if position else unreal.ToolMenuInsertType.FIRST
                v["name"] = v.get("name", "")
                prop[k] = unreal.ToolMenuInsert(**v)
            elif k == "type":
                typ = ENTRY_TYPE.get(str(v).upper())
                prop[k] = typ if typ else unreal.MultiBlockType.MENU_ENTRY
            elif k == "user_interface_action_type":
                typ = ACTION_TYPE.get(str(v).upper())
                prop.update({k:typ}) if typ else prop.pop(k)

        prop.setdefault("name", entry_name)
        prop.setdefault("type", unreal.MultiBlockType.MENU_ENTRY)
        entry = unreal.ToolMenuEntry(**prop)
        tooltip = config.get('tooltip')
        entry.set_tool_tip(tooltip) if tooltip else None
        
        entry.set_label(config.get('label', "untitle"))
        typ = COMMAND_TYPE.get(config.get("type", "").upper(), 0)

        command = config.get('command', '').format(**FORMAT_ARGS)
        entry.set_string_command(typ, "", string=command)
        menu.add_menu_entry(config.get('section', ''), entry)

    for entry_name, config in data.get("sub_menu", {}).items():
        init = config.get("init", {})
        owner = menu.get_name()
        section_name = init.get("section", "")
        name = init.get("name", entry_name)
        label = init.get("label", "")
        tooltip = init.get("tooltip", "")
        menu = menu.add_sub_menu(
            owner, section_name, name, label, tooltip)
        config.setdefault('menu', menu)
        handle_menu(config)

def read_json(json_path):
    with open(json_path, 'r') as f:
        data = json.load(
            f, object_pairs_hook=OrderedDict, encoding='utf-8')
    return data

def create_menu():
    # NOTE 读取 menu json 配置
    json_path = posixpath.join(DIR, "menu.json")
    menu_json = read_json(json_path)

    fail_menus = {}
    # NOTE https://forums.unrealengine.com/development-discussion/python-scripting/1767113-making-menus-in-py
    for tool_menu, config in menu_json.items():
        # NOTE 获取主界面的主菜单位置
        menu = menus.find_menu(tool_menu)
        if not menu:
            fail_menus.update({tool_menu:config})
            continue
        config.setdefault('menu', menu)
        handle_menu(config)

    # NOTE 刷新组件
    menus.refresh_all_widgets()
    
    # NOTE 获取当前不存在的菜单 | 设置定时任务嵌入
    if fail_menus:
        def timer_add_menu(menu_dict,timer):
            # NOTE 判断当前是否卡顿状态 | 如果卡顿就跳过执行 
            # NOTE 避免处于加载状态导致引擎崩溃 !FUObjectThreadContext::Get().IsRoutingPostLoad -> Cannot call UnrealScript while PostLoading objects
            global last_tick
            tick_elapsed = time.time() - last_tick
            if (tick_elapsed > 0.3):
                return
            
            # NOTE 如果 menu_dict 清空则停止计时器
            if not menu_dict:
                timer.stop()
                del timer
                return

            flag = False
            for tool_menu, config in menu_dict.items():
                menu = menus.find_menu(tool_menu)
                if not menu:
                    continue
                # NOTE 清除找到的menu
                menu_dict.pop(tool_menu)
                flag = True
                config.setdefault('menu', menu)
                handle_menu(config)
                
            if flag:
                menus.refresh_all_widgets()
        timer =  QtCore.QTimer()
        timer.timeout.connect(partial(timer_add_menu,fail_menus,timer))
        timer.start(1000)

def register_BP():
    # NOTE 执行 BP 目录下所有的 python 脚本 注册蓝图
    path = os.path.join(DIR,"BP")
    if not os.path.exists(path):
        return
    for root,directories,files in os.walk(path):
        for f in files:
            if not f.endswith(".py"):
                continue
            command = 'py "%s"' % posixpath.join(root,f).replace("\\","/")
            unreal.SystemLibrary.execute_console_command(None,command)
        
def slate_deco(func):
    def wrapper(self, single=True, *args, **kwargs):
        # NOTE 只保留一个当前类窗口
        if single:
            for win in QtWidgets.QApplication.topLevelWidgets():
                if win is self:
                    continue
                elif self.__class__.__name__ in str(type(win)):
                    win.deleteLater()
                    # win.setParent(None)
                    win.close()

        # NOTE https://forums.unrealengine.com/unreal-engine/unreal-studio/1526501-how-to-get-the-main-window-of-the-editor-to-parent-qt-or-pyside-application-to-it
        # NOTE 让窗口嵌入到 unreal 内部
        unreal.parent_external_window_to_slate(self.winId())
        res = func(self, *args, **kwargs)
        # NOTE 添加 dayu_widget 的样式
        dayu_theme.apply(self)
        return res
    return wrapper


# This function will receive the tick from Unreal
def __QtAppTick__(delta_seconds):
    # TODO 不添加事件处理 Qt 的窗口运行正常 | 添加反而会让 imgui 失去焦点
    # QtWidgets.QApplication.processEvents()
    # NOTE 处理 deleteDeferred 事件
    QtWidgets.QApplication.sendPostedEvents()
    global last_tick
    last_tick = time.time()

# This part is for the initial setup. Need to run once to spawn the application.
unreal_app = QtWidgets.QApplication.instance()
if not unreal_app:
    unreal_app = QtWidgets.QApplication([])
    tick_handle = unreal.register_slate_post_tick_callback(__QtAppTick__)
    __QtAppQuit__ = partial(
        unreal.unregister_slate_post_tick_callback, tick_handle)
    unreal_app.aboutToQuit.connect(__QtAppQuit__)

    with open(os.path.join(DIR, "main.css"), 'r') as f:
        unreal_app.setStyleSheet(f.read())

    # NOTE 重载 show 方法
    QtWidgets.QWidget.show = slate_deco(QtWidgets.QWidget.show)

    create_menu()
    register_BP()
