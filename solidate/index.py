# -*- coding: utf8 -*-
import json
import subprocess

import settings
import os.path

import os
import sys
import requests
from urllib.request import urlopen
import cos_utils


def return_message(message, status=200, base64=True):
    if message["res"] == "False":
        return {
            "isBase64Encoded": False,
            "statusCode": 400,
            "headers": {'Content-Type': 'application/json'},
            "body": json.dumps(message)
        }
    return {
        "isBase64Encoded": False,
        "statusCode": status,
        "headers": {'Content-Type': 'application/json'},
        "body": json.dumps(message)
    }


def download_from_url(url, base_folder):
    name = url.split('/')[-1]
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)
    dest_path = os.path.join(base_folder, name)

    # 检查URL是否为404
    try:
        with urlopen(url) as response:
            if response.status == 404:
                raise Exception(f"URL {url} is a 404 error.")
    except Exception as e:

        raise Exception(f"Error get url file: {e}")

    # 下载文件
    try:
        with requests.get(url, stream=True) as r:
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"File {dest_path} has been downloaded successfully.")
        return dest_path
    except Exception as e:
        raise Exception(f"Error downloading file: {e}")


def execute_command(command):
    try:
        # 使用subprocess.run执行命令，并捕获stdout和stderr
        result = subprocess.run(command.split(), check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # 返回stdout和stderr的内容
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        # 当命令返回非零退出状态时，捕获异常
        # 返回空字符串和stderr的内容
        return "", e.stderr
    except Exception as e:
        # 处理其他可能的异常
        return "", str(e)


def check_file(file):
    if os.path.exists(file):
        return True
    return False


def list_files_in_directory(directory_path):
    # 确保目录路径存在
    if not os.path.isdir(directory_path):
        raise ValueError(f"The specified directory does not exist: {directory_path}")

    # 列出目录下的所有文件和子目录
    entries = os.listdir(directory_path)

    # 过滤出所有文件，忽略子目录
    files = [entry for entry in entries if os.path.isfile(os.path.join(directory_path, entry))]

    return files


def main_handler(event, context):
    print("Received event: %s" % event)
    #print("Received context: %s" % context)

    params = json.loads(event["body"])
    print("current param is")
    print(params)

    # need param cos_url, minigame, tsv, symbol, className
    required_param = ["apk", "gameId", "accessKey", "secretKey"]
    for param in required_param:
        if param not in params:
            return_message({"res": f"Parameter {param} is needed"}, 400)
            return

    output, err = execute_command("uname -a")
    print(output)
    print(err)


    try:
        local_prefix = "/app/solidate/tmp/"
        #
        apk = download_from_url(params["apk"], local_prefix)
        print('download finished')
        if not check_file(apk):
            raise Exception("source apk file is not exist")
        # check_argument
        output_file = apk.replace(".apk", '_pro.apk')
        cmd = "/app/solidate/shield_launcher_linux  android --appid %s --ak %s --sk %s %s %s" % (
            params["gameId"], params["accessKey"], params["secretKey"], apk, output_file)
        print('start exec protection ' + cmd)

        output, err = execute_command(cmd)
        print("solid result: " + str(output) + "    err: " + str(err))
        if output == "":
            files = list_files_in_directory("/app/solidate/tmp/")
            for file in files:
                print(file)
            #got error
            tmp_file = "/app/solidate/tmp/ilxpp_pro.apk"
            if not check_file("/app/solidate/tmp/ilxpp_pro.apk"):
                raise Exception("/app/solidate/tmp/ilxpp_pro.apk.tmp not exist")
            output_file = output_file.replace("pro", "prok")
            cmd = "/app/shieldClient_10058033/client_tool/tools/client/linux/zipalign -v 4 %s %s" %(tmp_file, output_file)
            output, err = execute_command(cmd)
            if output == "":
                print("zipalign error with result " + str(err))
            # raise Exception("shield error with result " + str(err))

        if not check_file(output_file):
            raise Exception("dest file is not exist")

        # upload to cos
        # upload_path = settings.COS_PUBLIC_FOLDER + apk.split('/')[-1].replace('.apk', '_prok.apk')
        # cos_utils.upload_bin_file(output_file, upload_path)
        # print("All job done.")

        print('upload apk finished')
        return return_message({"res": "success",
                               "url": settings.COS_SESSION_DOWNLOAD_URL_PREFIX + upload_path})
    except Exception as e:
        # 获取异常信息
        exc_type, exc_obj, exc_tb = sys.exc_info()
        # 获取出问题的文件名
        file_name = exc_tb.tb_frame.f_code.co_filename
        # 获取出问题的行号
        line_number = exc_tb.tb_lineno
        # 打印异常信息和出问题的行
        print(f"异常类型: {exc_type}")
        print(f"异常信息: {e}")
        print(f"出问题的文件: {file_name}")
        print(f"出问题的行号: {line_number}")
        return return_message({
            "res": f"异常类型: {exc_type} \n  异常信息: {e}\n 出问题的文件: {file_name} \n 出问题的行号: {line_number}"},
            404)


if __name__ == "__main__":
    # params = {
    #     "apk": "https://upr-ui-image-int-1314001756.cos.ap-shanghai.myqcloud.com/public-apk/monos.apk",
    #     "gameId": "10058033",
    #     "accessKey": "8ced2c4764c045a9921c53830cac",
    #     "secretKey": "bf1579ad761b40b4b76e914c2913"
    # }
    # event = {"queryString": params}
    event = os.getenv('SCF_CUSTOM_CONTAINER_EVENT')
    print(main_handler(json.loads(event), None))
