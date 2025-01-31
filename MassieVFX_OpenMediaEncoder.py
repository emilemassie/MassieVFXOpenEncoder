import os, sys, json, subprocess, winreg, signal

import PyQt6
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt6 import QtGui, uic, QtCore, QtWidgets
from PyQt6.QtCore import Qt
from threading import Timer
import ctypes, cv2


def is_admin():
        try:
                return ctypes.windll.shell32.IsUserAnAdmin()
        except:
                False

def get_ffmpeg_exec():
    if getattr(sys, 'frozen', False):
        if sys.platform == "win32":  # Windows
            basedir = sys._MEIPASS
        elif sys.platform == "darwin":  # macOS
            basedir = os.path.dirname(os.path.abspath(__file__))
        elif sys.platform.startswith("linux"):  # Linux
            basedir = os.path.dirname(os.path.abspath(__file__))
            raise EnvironmentError("Unsupported operating system")
        
    else:
        basedir = '.'#os.path.dirname(os.path.abspath(__file__))
        basedir = str(basedir)

    # Determine the ffmpeg directory based on the OS
    if sys.platform == "win32":  # Windows
        ffmpeg_exec = basedir+'/ffmpeg.exe'
    elif sys.platform == "darwin":  # macOS
        ffmpeg_exec = basedir+'/ffmpeg'
    elif sys.platform.startswith("linux"):  # Linux
        ffmpeg_exec = basedir+'/ffmpeg'
        raise EnvironmentError("Unsupported operating system")

    return ffmpeg_exec

class FFmpegWorker(QtCore.QThread):
    progress = QtCore.pyqtSignal(int, float)
    finished = QtCore.pyqtSignal()
    log_update = QtCore.pyqtSignal(str)  # Signal to update the log
    sent_message_box = QtCore.pyqtSignal(str,str) 

    def __init__(self, input_files, output_file, profile, parent):
        super().__init__()
        self.parent = parent
        self.input_file = input_files
        self.output_file = output_file
        self.profile = profile 
        self.ffmpeg_exec = get_ffmpeg_exec()
        self.is_running = True
        self.paused = False
        self.prompt_value = None

    def run(self):
        # Set the creation flags to avoid a popup window on Windows
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        cap = cv2.VideoCapture(self.input_file) 
        property_id = int(cv2.CAP_PROP_FRAME_COUNT)  
        length = int(cv2.VideoCapture.get(cap, property_id)) 
        self.length = length

        #cmd = f'ffmpeg.exe -v quiet -stats -i {file} {arguments} {file_list[0]}_{profile["name"]}{profile["extension"]} > nul'
        cmd = [self.ffmpeg_exec, "-y", "-i", self.input_file] 

        if 'max_file_size' in self.profile.keys():
            a = self.profile['ffmpeg_arguments']
            for i in range(len(a)):
                if a[i] == '#max_file_size#':
                    max_file_size = self.profile['max_file_size']
                    bitrate = int(max_file_size)*160000/(int(length))

                    print(bitrate)
                    a[i] = str(int(bitrate))+'k'

        if 'quality' in self.profile.keys():
            a = self.profile['ffmpeg_arguments']
            for i in range(len(a)):
                if a[i] == '#quality#':
                    quality = self.profile['quality']
                    a[i] = str(int(quality))
        if 'prompt' in self.profile.keys():
            a = self.profile['ffmpeg_arguments']
            for i in range(len(a)):
                if a[i] == '#prompt#':
                    prompt = self.profile['prompt']
                    self.paused = True
                    self.sent_message_box.emit(prompt[0],prompt[1])
                    while self.paused:
                        pass
                    value = self.prompt_value
                    if value:
                        print(value)
                        a[i] = str(int(value))
                        wait = False
                    else:
                        print('passing')
                        a[i] = str(int(prompt[1]))
                        
        

        cmd += self.profile['ffmpeg_arguments']
        cmd.append(f'{self.output_file}')
        print(cmd)
            
        # Use subprocess.Popen to capture output in real-time and avoid window popup
        self.process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
            creationflags=creationflags
        )

        # Monitor the output for progress updates
        while True:
            line = self.process.stderr.readline()  # Read the stderr line by line
            if line == '' and self.process.poll() is not None:
                break  # Exit if no more output and the process has finished
            if "frame=" in line:
                # Extract frame information and emit progress signal
                frame_data = line.split("frame=")[1].split()[0]
                if frame_data.isdigit():
                    
                    percent = int(frame_data)/int(length)
                    self.progress.emit(int(frame_data), percent)  # Emit progress signal with frame count

            # Optionally, emit other updates based on different ffmpeg output logs
            #if line:
            #    self.log_update.emit(line.strip())  # Emit log updates for other messages

        self.process.wait()  # Ensure the process completes before moving on
        self.finished.emit()

class MVFX_FFMPEG_ENCODER(QMainWindow):
    def __init__(self, file, profile):
        super().__init__()
        self.file = file
        self.profile = self.get_profile(profile)
        self.root_folder = os.path.dirname(os.path.abspath(__file__))
        self.initUI()
        self.EncodeWithConfig(file, self.profile)

    
    def initUI(self):
        uic.loadUi(os.path.join(self.root_folder,'ui','mvfx_ffmpeg_encoder.ui'), self) 
        self.setWindowTitle('MassieVFX FFMPEG Encoder')
        self.setWindowIcon(PyQt6.QtGui.QIcon(os.path.join(self.root_folder,'icon.ico')))
        self.file_label.setText(os.path.basename(self.file))
        self.profile_label.setText(self.profile['name'])
        self.update_logs(f'Endoding : {self.file}\nProfile : {self.profile["name"]}')
        self.update_logs(f'-----------------------------\n\n')
        self.done_button.released.connect(lambda: sys.exit(0))
        self.setWindowIcon(QtGui.QIcon(os.path.join(self.root_folder,'icon.ico')))
        self.setWindowFlags(self.windowFlags() & QtCore.Qt.WindowType.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowType.WindowMinMaxButtonsHint)
        self.show()


    def get_profile(self,profile):
        with open(profile) as json_file:
            config = json.load(json_file)
        return config

    def EncodeWithConfig(self, file, profile):
        arguments = profile['ffmpeg_arguments']
        file_list = os.path.basename(file).split('.')
        new_file_name = os.path.join(os.path.dirname(file),f'{file_list[0]}_{profile["name"]}{profile["extension"]}')
        #self.command = f'ffmpeg.exe -v quiet -stats -i {file} {arguments} {file_list[0]}_{profile["name"]}{profile["extension"]} > nul'
        #print(self.command)
        
        self.worker = FFmpegWorker(file, new_file_name, profile, self)
        self.worker.progress.connect(self.update_progress)
        self.worker.sent_message_box.connect(self.show_msg_box)
        self.worker.finished.connect(self.on_finished)
        self.worker.log_update.connect(self.update_logs)  # Connect log update signal
        self.worker.start()
    
    def show_msg_box(self, message, default = ''):
        self.worker.prompt_value = None
        text, okPressed = QtWidgets.QInputDialog.getText(None, "Get text", message, text=default)   
        if okPressed and text != '':
            self.worker.prompt_value = str(int(text))
            self.worker.paused = False
            return 
        else:
            self.worker.prompt_value = None
            self.worker.paused = False

    def update_progress(self, frame, progress):
        # Update the progress bar based on the number of frames processed
        self.pbar.setValue(int(progress*100))
        if frame > 0 :
            self.update_logs('Exporting frame: ' + str(frame) + '/'+str(self.worker.length))

    def on_finished(self):
        self.update_logs(f'File Transcoded')
        self.pbar.setValue(100)
        self.done_button.setEnabled(True)

    def update_logs(self, message, color=None):
        if color:
            self.logs.append(f'<p style="color:{color};">'+message+'</p> ')
        else:
            self.logs.append(message)  # Append message to log view

        self.logs.moveCursor(QtGui.QTextCursor.MoveOperation.End)

    def closeEvent(self, *args, **kwargs):
        super(QMainWindow, self).closeEvent(*args, **kwargs)
        subprocess.call(['taskkill', '/F', '/T', '/PID',  str(self.worker.process.pid)])

class MASSIEVFX_OPEN_MEDIA_ENCODER(QMainWindow):
    def __init__(self):
        super().__init__()
        self.root_folder = os.path.dirname(os.path.abspath(__file__))
        self.ProfilePath = os.path.join(os.getcwd(),'profiles')
        os.makedirs(self.ProfilePath, exist_ok=True)
        self.ROOTKEY = r'*\\shell\\MassieVFXOpenEncoder'
        self.activeDir = self.ROOTKEY
        uic.loadUi(os.path.join(self.root_folder,'ui','mvfx_media_encoder.ui'), self) 
        self.setWindowIcon(QtGui.QIcon(os.path.join(self.root_folder,'icon.ico')))
        self.setWindowTitle('Massie VFX Open Media Encoder')

        self.Tree.setObjectName("Tree")
        self.Tree.header().setVisible(False)
        self.parentElement = self.Tree
        self.Tree.setHeaderLabels(["Folder Structure"])
        self.populate_tree(self.ProfilePath, self.Tree.invisibleRootItem())
        
        self.apply_button.released.connect(self.OkClicked)
        self.Tree.itemChanged.connect(self.on_item_changed)
        self._updating = False

    def update_children_state(self, item):
        """Recursively updates all children to match parent's check state."""
        if self._updating:  # Skip if already updating
            return
            
        self._updating = True
        state = item.checkState(0)
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)
            self.update_children_state(child)  # Recursively update descendants
        self._updating = False

    def update_parent_state(self, item):
        """Updates parent check state when child checkboxes change."""
        if self._updating:  # Skip if already updating
            return
            
        parent = item.parent()
        if not parent:
            return  # Root-level items have no parent

        self._updating = True
        checked = 0
        unchecked = 0
        total = parent.childCount()

        for i in range(total):
            child = parent.child(i)
            if child.checkState(0) == Qt.CheckState.Checked:
                checked += 1
            elif child.checkState(0) == Qt.CheckState.Unchecked:
                unchecked += 1

        if checked == total:
            parent.setCheckState(0, Qt.CheckState.Checked)  # All checked ✅
        elif unchecked == total:
            parent.setCheckState(0, Qt.CheckState.Unchecked)  # All unchecked ⬜
        else:
            parent.setCheckState(0, Qt.CheckState.PartiallyChecked)  # Partially checked ◩

        self.update_parent_state(parent)  # Recursively update ancestors
        self._updating = False

    def on_item_changed(self, item, column):
        """Handle item state changes."""
        if column == 0 and not self._updating:  # Only process if not already updating
            if item.childCount() > 0:  # If item has children
                self.update_children_state(item)
            else:  # If item is a child
                self.update_parent_state(item)


    def populate_tree(self, folder_path, parent_item):
        """ Recursively scans a folder and builds the QTreeWidget structure. """
        for entry in sorted(os.listdir(folder_path)):  
            full_path = os.path.join(folder_path, entry)

            if os.path.isdir(full_path):
                item = QtWidgets.QTreeWidgetItem(parent_item, [entry])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(0, Qt.CheckState.Unchecked) 
                self.populate_tree(full_path, item)
            elif entry.endswith(".json"):
                print(entry, parent_item)
                item = QtWidgets.QTreeWidgetItem(parent_item, [entry.replace('.json', '')])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(0, Qt.CheckState.Unchecked)  # Default unchecked
                execPath = sys.argv[0]
                command = f'{execPath} "{full_path}" %1'
                item.setData(0, Qt.ItemDataRole.UserRole, command)


    def setProfilePath(self):
        self.Tree.clear()
        self.ProfilePath = QtWidgets.QFileDialog.getExistingDirectory(None, "Select Directory", self.ProfilePath)
        self.getFiles()

    def delete_sub_key(self, root, sub):
        try:
            open_key = winreg.OpenKey(root, sub, 0, winreg.KEY_ALL_ACCESS)
            num, _, _ = winreg.QueryInfoKey(open_key)

            for i in range(num):
                child = winreg.EnumKey(open_key, 0)
                self.delete_sub_key(open_key, child)
            try:
                winreg.DeleteKey(open_key, '')
            except Exception:
                print(Exception)# log deletion failure
            finally:
                winreg.CloseKey(open_key)
        except Exception:
            print(Exception)
            
    def ScanTreeDir(self, item):
        """ Recursively scans checked items and updates the Windows Registry. """
        if item.checkState(0) == Qt.CheckState.Checked or item.checkState(0) == Qt.CheckState.PartiallyChecked:  # Only process checked items
            if item.childCount() > 0:  # If it's a folder
                self.activeDir = self.activeDir + r'\\' + item.text(0)
                ROOTKEY = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, self.activeDir)
                winreg.SetValueEx(ROOTKEY, 'MUIVerb', 0, winreg.REG_SZ, item.text(0))
                winreg.SetValueEx(ROOTKEY, 'subcommands', 0, winreg.REG_SZ, '')
                winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, self.activeDir + r'\\shell')
                self.activeDir = self.activeDir + r'\\shell'
                # Recursively scan child items
                for i in range(item.childCount()):
                    self.ScanTreeDir(item.child(i))

            else:  # If it's a file
                file_path = item.data(0, Qt.ItemDataRole.UserRole)  # Retrieve stored file path
                execute_command = item.data(0, Qt.ItemDataRole.UserRole)  # Fetch stored command
                
                if file_path and execute_command:
                    registry_path = f"{self.activeDir}\\{item.text(0)}"
                    winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, registry_path)
                    winreg.SetValue(winreg.HKEY_CLASSES_ROOT, f"{registry_path}\\command", winreg.REG_SZ, execute_command)


    def setname(self):
        self.apply_button.setText('APPLY')

    def showOkAnim(self):
        self.apply_button.setText('APPLIED !!!')
        Timer(3, self.setname).start()

    def OkClicked(self):
        """ Clears and re-registers checked files in the Windows Registry. """
        self.activeDir = self.ROOTKEY
        self.delete_sub_key(winreg.HKEY_CLASSES_ROOT, self.ROOTKEY)

        ROOTKEY = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, self.ROOTKEY)
        winreg.SetValueEx(ROOTKEY, 'MUIVerb', 0, winreg.REG_SZ, 'MassieVFX - Open Encoder')
        winreg.SetValueEx(ROOTKEY, 'subcommands', 0, winreg.REG_SZ, '')

        winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, self.activeDir + r'\\shell')

        for i in range(self.Tree.topLevelItemCount()):
            self.activeDir = self.ROOTKEY + r'\\shell'
            self.ScanTreeDir(self.Tree.topLevelItem(i))  # Process all top-level checked items

        self.showOkAnim()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    if len(sys.argv) < 2:
        if is_admin():
            main = MASSIEVFX_OPEN_MEDIA_ENCODER()
            main.show()
            sys.exit(app.exec())
        else:
            QtWidgets.QMessageBox.information(None, "Not Admin", "Please run as administrator.")
            
    else:
        main = MVFX_FFMPEG_ENCODER(sys.argv[2], sys.argv[1])
        sys.exit(app.exec())
