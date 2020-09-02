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

import aiohttp
import yaml
import json


class LookupClient:
    def __init__(self, lookup_url, auth_url, username, password):
        self.session = aiohttp.ClientSession()
        self.lookup_url = lookup_url
        self.auth_url = auth_url
        self.username = username
        self.password = password

    async def connect(self):
        await self._authenticate(self.username, self.password)

    async def _authenticate(self, username, password):
        async with self.session.post(
                self.auth_url,
                json={
                    'username': username,
                    'password': password
                }, verify_ssl=False) as r:
            if r.status == 200:
                json = await r.json()
                self.token = json['token']
                self.header = {'Authorization': f'Bearer {self.token}'}
            else:
                raise RuntimeError('Authentication failed')

    async def all(self):
        async with self.session.get(
                f'{self.lookup_url}/dataset/list',
                headers=self.header, verify_ssl=False) as r:
            return await r.json()

    async def search(self, keyword):
        """Free text search"""
        async with self.session.post(
                f'{self.lookup_url}/dataset/search',
                headers=self.header,
                json={
                    'free_text': keyword
                }, verify_ssl=False) as r:
            return await r.json()

    async def by_uuid(self, uuid):
        """Search for a specific uuid"""
        async with self.session.get(
                f'{self.lookup_url}/dataset/lookup/{uuid}',
                headers=self.header,
                verify_ssl=False) as r:
            return await r.json()

    async def by_query(self, query):
        """Search by arbitrary NoSQL mongo query."""
        async with self.session.post(
                f'{self.lookup_url}/dataset/search',
                headers=self.header,
                json=json.loads(query), verify_ssl=False) as r:
            return await r.json()

    async def readme(self, uri):
        async with self.session.post(
                f'{self.lookup_url}/dataset/readme',
                headers=self.header,
                json={
                    'uri': uri
                }, verify_ssl=False) as r:
            text = await r.text()
            return yaml.load(text)

    async def manifest(self, uri):
        async with self.session.post(
                f'{self.lookup_url}/dataset/manifest',
                headers=self.header,
                json={
                    'uri': uri
                }, verify_ssl=False) as r:
            text = await r.text()
            return yaml.load(text)
