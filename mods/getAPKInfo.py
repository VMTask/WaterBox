import shutil
import subprocess
import re
import tempfile
import zipfile
class getAPKInfo():
    def __init__(self,file,aapt_executable):
        self.file = file
        command = [aapt_executable, 'dump', 'badging', self.file]
        self.output = subprocess.check_output(command, text=True,encoding="utf-8")
        
    def getAppName(self):
        pattern = r'application-label-zh-CN:\s*\'(.*)\''
        match = re.search(pattern, self.output)

        if match:
            app_label_zh_CN = match.group(1)
            return app_label_zh_CN
        else:
            pattern = r'application-label:\s*\'(.*)\''
            match = re.search(pattern, self.output)
            return match.group(1)
    def getAppVersion(self):
        pattern = r'versionName=\'(\S+)\''
        match = re.search(pattern, self.output)

        if match:
            versionName = match.group(1)
            return versionName
        else:
            return "App hasn't got a version"
    def getAppPackageName(self):
        pattern = r'name=\'(\S+)\''
        match = re.search(pattern, self.output)

        if match:
            packageName = match.group(1)
            return packageName
        else:
            return "App hasn't got a packageName"
    def getAppMinSDK(self):
        pattern = r'sdkVersion:\s*\'(.*)\''
        match = re.search(pattern, self.output)

        if match:
            minSDK = match.group(1)
            return minSDK
        else:
            return "App hasn't got a minSDK"
    def getAppTargetSDK(self):
        pattern = r'targetSdkVersion:\s*\'(.*)\''
        match = re.search(pattern, self.output)

        if match:
            targetSDK = match.group(1)
            return targetSDK
        else:
            return "App hasn't got a targetSDK"
        
    def getAppIcon(self):
        pattern = r'application-icon-640:\s*\'(.*)\''
        match = re.search(pattern, self.output)
    
        if match:
            icon_resource_path = match.group(1)
            import os
            temp_dir = f"{os.getcwd()}\\cache"
            with zipfile.ZipFile(self.file, 'r') as zip_ref:
                zip_ref.extract(icon_resource_path,temp_dir)
                info_icon_resource_path = icon_resource_path.replace("/","\\")
                full_icon_path = f'{temp_dir}\\{info_icon_resource_path}'

                    # 检查图标文件是否存在并复制到目标位置
                return full_icon_path
        else:
            return None  # 如果未找到图标资源，则返回None
        
def test():
    app = getAPKInfo("E:\\下载\\iFlyIME_v13.0.7.15091.apk","E:\\WaterBox\\adb_executable\\aapt.exe")
    print(app.getAppName())
    print(app.getAppVersion())
    print(app.getAppPackageName())
    print(app.getAppMinSDK())
    print(app.getAppTargetSDK())
    print(app.getAppIcon())
    
if __name__=="__main__":
    test()