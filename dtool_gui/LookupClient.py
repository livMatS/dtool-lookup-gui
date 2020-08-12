#
# Copyright 2020 Lars Pastewka
#
# ### MIT license
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import requests
import yaml

class LookupClient:
    def __init__(self, username, password,
                 auth_url='https://simdata.vm.uni-freiburg.de:5001/token',
                 lookup_url='https://simdata.vm.uni-freiburg.de:5000'):
        self.auth_url = auth_url
        self.lookup_url = lookup_url
        self._authenticate(username, password)

    def _authenticate(self, username, password):
        r = requests.post(
            self.auth_url,
            json={
                'username': username,
                'password': password
            },
            verify=False)
        if r.status_code == 200:
            self.token = r.json()['token']
            self.header = {'Authorization': f'Bearer {self.token}'}
        else:
            raise RuntimeError('Authentication failed')

    def all(self):
        r = requests.get(
            f'{self.lookup_url}/dataset/list',
            headers=self.header,
            verify=False)
        return r.json()

    def search(self, keyword):
        """Free text search"""
        r = requests.post(
            f'{self.lookup_url}/dataset/search',
            headers=self.header,
            json={
                     'free_text': keyword
            },
            verify=False)
        return r.json()

    def readme(self, uri):
        r = requests.post(
            f'{self.lookup_url}/dataset/readme',
            headers=self.header,
            json={
                'uri': uri
            },
            verify=False)
        return yaml.load(r.text)