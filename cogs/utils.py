import requests

# pylint: disable=no-member
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning)


class AstroRequests():
    proxies = None
    fiddlerProxies = {
        "http": "http://127.0.0.1:8888",
        "https": "http://127.0.0.1:8888"
    }

    @classmethod
    def checkProxies(cls):
        try:
            x = requests.get(cls.fiddlerProxies['http'], timeout=0.3)
            if x.status_code == 200:
                cls.proxies = cls.fiddlerProxies.copy()
        except:
            cls.proxies = None

    @classmethod
    def get(cls, url, timeout=5):
        # cls.checkProxies()
        # return requests.get(url, verify=False, proxies=cls.proxies, timeout=5)
        return requests.get(url, verify=False, timeout=timeout)

    @classmethod
    def post(cls, url, headers=None, json=None, files=None, data=None, timeout=5):
        # cls.checkProxies()
        # return requests.post(url, verify=False, proxies=cls.proxies, headers=headers, json=json, timeout=5)
        return requests.post(url, verify=False, headers=headers, json=json, files=files, data=data, timeout=timeout)
