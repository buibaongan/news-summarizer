import asyncio
import httpx


class ASGITestClient:
    def __init__(self, app):
        self.app = app

    def get(self, path, **kwargs):
        return asyncio.run(self._request('GET', path, None, kwargs))

    def post(self, path, json=None, **kwargs):
        return asyncio.run(self._request('POST', path, json, kwargs))

    async def _request(self, method, path, json, kwargs):
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url='http://testserver') as client:
            if json is None:
                return await client.request(method, path, **kwargs)
            return await client.request(method, path, json=json, **kwargs)
