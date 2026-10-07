import unittest
from unittest.mock import patch
from boundary import InternalBoundary, read_upload
from fastapi import HTTPException


class BoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def request(self, headers, chunks, client='203.0.113.1'):
        called, sent = [], []
        async def app(scope, receive, send):
            called.append(await receive())
            await send({'type': 'http.response.start', 'status': 200})
        async def receive():
            return {'type': 'http.request', 'body': chunks.pop(0), 'more_body': bool(chunks)}
        async def send(message): sent.append(message)
        await InternalBoundary(app, token='test-key')(
            {'type': 'http', 'path': '/audio/analyze', 'headers': headers, 'client': (client, 1)}, receive, send)
        return sent[0]['status'], called

    async def test_auth_and_chunked_limits_before_application(self):
        self.assertEqual((await self.request([], [b'private']))[0], 403)
        auth = [(b'x-service-token', b'test-key')]
        self.assertEqual((await self.request(auth, [b'a', b'b']))[0], 200)
        with patch('boundary.MAX_REQUEST', 3):
            status, called = await self.request(auth, [b'aa', b'bb'])
            self.assertEqual((status, called), (413, []))
            self.assertEqual((await self.request(auth + [(b'content-length', b'4')], [b'']))[0], 413)

    async def test_upload_limit(self):
        class File:
            async def read(self, size): return b'x' * size
        with patch('boundary.MAX_UPLOAD', 3):
            with self.assertRaises(HTTPException) as error: await read_upload(File())
            self.assertEqual(error.exception.status_code, 413)


if __name__ == '__main__': unittest.main()
