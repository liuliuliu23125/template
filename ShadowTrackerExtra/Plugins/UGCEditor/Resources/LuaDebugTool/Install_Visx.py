import os
import shutil
import json
import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.withdraw()  # 隐藏主窗口

def IsNeedInstallVisx():
    vscode_visx_path = os.path.join(os.path.expanduser('~'), '.vscode\\extensions\\UGC_Lua_Visx')
    if os.path.exists(vscode_visx_path):
        return False

    target_json = os.path.join(os.path.expanduser('~'), '.vscode\\extensions\\extensions.json') 
    if not os.path.exists(source_json):
        return True

    with open(target_json, 'r') as f1:
        target_json_data = json.load(f1)
        f1.close()
        # print(target_json_data[1])

    for _JsonData in target_json_data:
        if _JsonData["relativeLocation"] == "UGC_Lua_Visx":
            return False
        
    return True

def IsHasVSCodePath():
    vscode_path = os.path.join(os.path.expanduser('~'), '.vscode')
    if not os.path.exists(vscode_path):
        messagebox.showinfo("Waring", "没有发现VSCode安装目录") 
        return False
    
    return True

def CheckAndRemoveOldVisx():
    vscode_visx_path = os.path.join(os.path.expanduser('~'), '.vscode\\extensions\\UGC_Lua_Visx')
    if os.path.exists(vscode_visx_path):
        try:
            os.chmod(vscode_visx_path, 0o777)
            shutil.rmtree(vscode_visx_path)
            print("Delete Folder:", vscode_visx_path)
        except Exception as e:
            messagebox.showinfo("Waring", "旧插件删除失败") 
            

def CopyVisxToVSCodePath():
    source_folder = os.path.join(os.getcwd(), "UGC_Lua_Visx")  # 当前目录中的子文件夹
    target_folder = os.path.join(os.path.expanduser('~'), '.vscode\\extensions\\UGC_Lua_Visx')  # 目标文件夹路径

    print("CopyVisxToVSCodePath source_folder", source_folder)
    print("CopyVisxToVSCodePath target_folder", target_folder)

    try:
        os.mkdir(target_folder)
        print(f"文件夹 '{target_folder}' 创建成功")
    except FileExistsError:
        messagebox.showinfo("Waring", "文件夹 '{target_folder}' 已存在")

    try:
        os.chmod(target_folder, 0o777)
        shutil.rmtree(target_folder)
        shutil.copytree(source_folder, target_folder)
        print("文件夹复制成功！", target_folder)
    except FileExistsError:
        messagebox.showinfo("Waring", "旧插件还在，复制失败") 
    except Exception as e:
        messagebox.showinfo("Waring", e) 

def RegisterVisx():
    target_json = os.path.join(os.path.expanduser('~'), '.vscode\\extensions\\extensions.json') 
    with open(target_json, 'r') as f1:
        target_json_data = json.load(f1)
        f1.close()
        # print(target_json_data[1])

    for _JsonData in target_json_data:
        if _JsonData["relativeLocation"] == "UGC_Lua_Visx":
             messagebox.showinfo("Waring", "之前已经注册过插件！")
             return False

    source_json = os.path.join(os.getcwd(), 'visx.json') 
    if not os.path.exists(source_json):
        messagebox.showinfo("Waring", "没有发现 visx.json")
        return False


    with open(source_json, 'r') as f2:
        source_json_data = json.load(f2)
        source_json_data["location"]['fsPath'] = os.path.join(os.path.expanduser('~'), '.vscode\\extensions\\UGC_Lua_Visx')
        source_json_data["location"]['path'] = os.path.join(os.path.expanduser('~'), '.vscode\\extensions\\UGC_Lua_Visx')
        source_json_data["location"]['external'] = "file:///" + os.path.join(os.path.expanduser('~'), '.vscode\\extensions\\UGC_Lua_Visx')
        f2.close()
    
    target_json_data.append(source_json_data)
    # print(target_json_data)

    #保存结果
    with open(target_json, 'w') as f:
        json.dump(target_json_data, f, indent=4)
        f.close()

    return True

def MainLog():
    if IsHasVSCodePath() == False:
        return
    
    CheckAndRemoveOldVisx()
    CopyVisxToVSCodePath()
    RegisterVisx()

MainLog()
    