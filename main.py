# -*- coding: utf-8 -*-

import asyncio
import configparser
import os

from alibabacloud_alidns20150109 import models as alidns_20150109_models
from alibabacloud_alidns20150109.client import Client as Alidns20150109Client
from alibabacloud_alidns20150109.models import DescribeDomainRecordsResponseBodyDomainRecordsRecord
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from netifaces import ifaddresses, interfaces, AF_INET6


class Config:
    def __init__(self):
        pass

    # 读取配置文件
    @staticmethod
    def get_config(section, option):
        # 获取当前目录路径
        pro_dir = os.path.split(os.path.realpath(__file__))[0]
        # 拼接路径获取完整路径
        config_path = os.path.join(pro_dir, 'ddns.ini')
        # 创建ConfigParser对象
        conf = configparser.ConfigParser()
        # 读取文件内容
        conf.read(config_path)
        config = conf.get(section, option)
        return config


class Sample:
    def __init__(self):
        pass

    # 构造请求参数
    @staticmethod
    def create_client() -> Alidns20150109Client:
        config = open_api_models.Config(
            access_key_id=Config.get_config("ddns", 'access_key_id'),
            access_key_secret=Config.get_config("ddns", 'access_key_secret')
        )
        # 访问的域名
        config.endpoint = Config.get_config("ddns", 'endpoint')
        return Alidns20150109Client(config)

    # 获得 record 对象 为了获得 record_id
    @staticmethod
    async def get_ddns_record() -> DescribeDomainRecordsResponseBodyDomainRecordsRecord:
        client = Sample.create_client()
        describe_domain_records_request = alidns_20150109_models.DescribeDomainRecordsRequest(
            domain_name=Config.get_config("ddns", 'domain_name'),
            key_word=Config.get_config("ddns", 'key_word')
        )
        runtime = util_models.RuntimeOptions()
        try:
            data = await client.describe_domain_records_with_options_async(describe_domain_records_request, runtime)
            record = data.body.domain_records.record[0]
            return record
        except Exception as error:
            UtilClient.assert_as_string(error.message)

    # 更新
    @staticmethod
    async def update_ddns(
            record_id: str,
    ) -> None:
        client = Sample.create_client()
        update_domain_record_request = alidns_20150109_models.UpdateDomainRecordRequest(
            lang=Config.get_config("ddns", 'lang'),
            value=Sample.get_current_ip(),
            type=Config.get_config("ddns", 'type'),
            rr=Config.get_config("ddns", 'key_word'),
            record_id=record_id
        )
        runtime = util_models.RuntimeOptions()
        try:
            record = await client.update_domain_record_with_options_async(update_domain_record_request, runtime)
            if record.status_code == "200":
                print('update success')
            else:
                print('update fail')
        except Exception as error:
            UtilClient.assert_as_string(error.message)

    # 获得本地ipv6
    @staticmethod
    def get_current_ip():
        header = Config.get_config("ddns", 'ipv6_header')
        for ifaceName in interfaces():
            for i in ifaddresses(ifaceName).setdefault(AF_INET6):
                if i['addr'].find(header) >= 0 and len(i['addr']) > 36:
                    return i['addr']

    @staticmethod
    async def main() -> None:
        try:
            record = await Sample.get_ddns_record()
            ip = Sample.get_current_ip()
            print("current ipv6:", ip, " | | ", "remote ipv6:", record.value)
            if ip != record.value:
                await Sample.update_ddns(record.record_id)
            else:
                print("Local and remote are not required at all times")
        except Exception as error:
            UtilClient.assert_as_string(error.message)


if __name__ == '__main__':
    asyncio.run(Sample.main())
