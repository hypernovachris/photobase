import os
import ctypes
from ctypes import wintypes
from PyQt6.QtCore import QThread, pyqtSignal

class SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("wFunc", wintypes.UINT),
        ("pFrom", ctypes.c_wchar_p),
        ("pTo", ctypes.c_wchar_p),
        ("fFlags", wintypes.WORD),
        ("fAnyOperationsAborted", wintypes.BOOL),
        ("hNameMappings", ctypes.c_void_p),
        ("lpszProgressTitle", ctypes.c_wchar_p),
    ]

FO_DELETE = 0x0003
FOF_ALLOWUNDO = 0x0040
FOF_NOCONFIRMATION = 0x0010
FOF_SILENT = 0x0004
FOF_NOERRORUI = 0x0400

class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64),
    ]

def can_recycle_path(path):
    try:
        abspath = os.path.abspath(path)
        drive, _ = os.path.splitdrive(abspath)
        if not drive:
            return False
        if drive.startswith('\\\\'):
            return False
        
        root_path = drive + '\\'
        
        kernel32 = ctypes.windll.kernel32
        drive_type = kernel32.GetDriveTypeW(root_path)
        # DRIVE_REMOVABLE = 2, DRIVE_FIXED = 3
        if drive_type not in (2, 3):
            return False
            
        shell32 = ctypes.windll.shell32
        info = SHQUERYRBINFO()
        info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
        hr = shell32.SHQueryRecycleBinW(root_path, ctypes.byref(info))
        return hr == 0
    except Exception:
        return False

def win_recycle_file(path):
    full_path = os.path.abspath(path) + '\0\0'
    file_op = SHFILEOPSTRUCTW()
    file_op.hwnd = None
    file_op.wFunc = FO_DELETE
    file_op.pFrom = full_path
    file_op.pTo = None
    file_op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI
    
    shell32 = ctypes.windll.shell32
    result = shell32.SHFileOperationW(ctypes.byref(file_op))
    if result != 0 or file_op.fAnyOperationsAborted:
        raise OSError(f"Failed to recycle file {path}. Windows error code: {result}")

def win_delete_file(path):
    try:
        import stat
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass
    os.remove(path)

class RecycleWorker(QThread):
    progress = pyqtSignal(int, int) # current, total
    fileRemoved = pyqtSignal(str) # path
    finished = pyqtSignal(int) # total_succeeded
    error = pyqtSignal(str, int, int) # error message, succeeded, total

    def __init__(self, paths, permanent_mode=False):
        super().__init__()
        self.paths = paths
        self.permanent_mode = permanent_mode

    def run(self):
        succeeded = 0
        total = len(self.paths)
        try:
            for path in self.paths:
                if not os.path.exists(path):
                    self.fileRemoved.emit(path)
                    succeeded += 1
                    self.progress.emit(succeeded, total)
                    continue

                if self.permanent_mode or not can_recycle_path(path):
                    win_delete_file(path)
                else:
                    win_recycle_file(path)

                self.fileRemoved.emit(path)
                succeeded += 1
                self.progress.emit(succeeded, total)
                
            self.finished.emit(succeeded)
        except Exception as e:
            self.error.emit(str(e), succeeded, total)
