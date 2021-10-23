#import requests
import json
import urllib
import urllib.error
from urllib import request
import ssl

# pylint: disable=no-member

ALVERSION = "v1.8.2.3"


class AstroRequests():
    @classmethod
    def get(cls, url, timeout=5):
        proxies = request.getproxies()
        proxy_handler = request.ProxyHandler(proxies)
        opener = request.build_opener(proxy_handler)
        gcontext = ssl.SSLContext()
        request.install_opener(opener)
        #print(f"get: {proxies}")
        resp = request.urlopen(url, timeout=timeout, context=gcontext)
        # print(resp)
        return resp  # cls.session.get(url, verify=False, timeout=timeout)

    @classmethod
    def post(cls, url, headers=None, jsonD=None, timeout=5):
        if not headers:
            headers = {}
        if not jsonD:
            jsonD = {}
        req = request.Request(url)
        if jsonD != {}:
            jsonD = json.dumps(jsonD).encode('utf-8')
            req.add_header('Content-Type', 'application/json; charset=utf-8')
        gcontext = ssl.SSLContext()

        # print(f"data: {jsonD}")
        # print(f"headers:{headers}")
        for header, value in headers.items():
            req.add_header(header, value)

        proxies = request.getproxies()
        proxy_handler = request.ProxyHandler(proxies)
        opener = request.build_opener(proxy_handler)
        request.install_opener(opener)
        # print(f"post: {proxies}")
        # print(f"url: {url}")
        try:
            resp = request.urlopen(
                req, data=jsonD, timeout=timeout, context=gcontext)
        except urllib.error.HTTPError as e:
            resp = e
        return resp
