# -*- coding:utf-8 -*-
#@Auhor : Agam
#@Time  : 2018-10-08
#@Email : agamgn@163.com

from qiniu import Auth, put_file, etag, put_data
import qiniu.config

# 需要填写你的 Access Key 和 Secret Key
access_key = ''
secret_key = ''

def storage(file_data):

    q = Auth(access_key, secret_key)

    bucket_name = ''


    token = q.upload_token(bucket_name, None, 3600)

    ret, info = put_data(token, None, file_data)

    if info.status_code==200:
        return ret.get("key")
    else:
        raise Exception("上传七牛失败")
