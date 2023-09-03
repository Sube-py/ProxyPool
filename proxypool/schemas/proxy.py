from typing import List

from pydantic import BaseModel


class ProxySchema(BaseModel):
    host: str
    port: str
    
    def __str__(self) -> str:
        return f'{self.host}:{self.port}'
    
    def string(self) -> str:
        return self.__str__()

    @staticmethod
    def __is_auth_proxy(data: str) -> bool:
        return '@' in data

    @staticmethod
    def extract_auth_proxy(data: str) -> (str, str):
        auth, ip_port = data.split('@')
        ip, port = ip_port.split(':')
        host = f'{auth}@{ip}'
        return host, port

    @classmethod
    def is_ip_valid(cls, ip: str) -> bool:
        if cls.__is_auth_proxy(ip):
            ip = ip.split('@')[1]
        a = ip.split('.')
        if len(a) != 4:
            return False
        for x in a:
            if not x.isdigit():
                return False
            i = int(x)
            if i < 0 or i > 255:
                return False
        return True

    @staticmethod
    def is_port_valid(port: str) -> bool:
        return port.isdigit() and 0 < int(port) < 65536

    @classmethod
    def is_valid_proxy(cls, proxy: str):
        if cls.__is_auth_proxy(proxy):
            host, port = cls.extract_auth_proxy(proxy)
            return cls.is_ip_valid(host) and cls.is_port_valid(port)
        elif proxy.__contains__(':'):
            ip, port = proxy.split(':')
            return cls.is_ip_valid(ip) and cls.is_port_valid(port)
        else:
            return cls.is_ip_valid(proxy)

    @classmethod
    def convert_proxy_or_proxies(cls, data: str | List[str]) -> "ProxySchema" | List["ProxySchema"]:
        # TODO: data must be list
        if isinstance(data, list):
            result = []
            for item in data:
                item: str
                item = item.strip()
                if not cls.is_valid_proxy(item):
                    continue
                if cls.__is_auth_proxy(item):
                    host, port = cls.extract_auth_proxy(item)
                else:
                    host, port = item.split(':')
                result.append(ProxySchema(host=host, port=port))
            return result
        if isinstance(data, str) and cls.is_valid_proxy(data):  # type: ignore
            if cls.__is_auth_proxy(data):
                host, port = cls.extract_auth_proxy(data)
            else:
                host, port = data.split(':')
            return ProxySchema(host=host, port=port)
