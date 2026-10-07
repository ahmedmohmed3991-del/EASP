"""Authenticate and bound internal requests before multipart parsing or inference."""
import hmac
import ipaddress
import os
from fastapi import HTTPException
from starlette.responses import JSONResponse

MAX_UPLOAD = 25 * 1024 * 1024
MAX_REQUEST = MAX_UPLOAD + 1024 * 1024
MAX_JSON = 256 * 1024


class InternalBoundary:
    def __init__(self, app, token=None):
        self.app = app
        self.token = os.getenv('AI_SERVICE_TOKEN', '') if token is None else token

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = dict(scope.get('headers', []))
        if scope['path'] not in ('/health', '/'):
            if self.token:
                authorized = hmac.compare_digest(headers.get(b'x-service-token', b''), self.token.encode())
            else:
                try:
                    authorized = ipaddress.ip_address(scope.get('client', ('', 0))[0]).is_loopback
                except ValueError:
                    authorized = False
            if not authorized:
                return await JSONResponse({'detail': 'Internal service access required'}, status_code=403)(scope, receive, send)
        limit = MAX_REQUEST if scope['path'].startswith('/audio/') else MAX_JSON
        try:
            length = int(headers.get(b'content-length', b'0'))
            if length < 0: raise ValueError()
        except ValueError:
            return await JSONResponse({'detail': 'Invalid content length'}, status_code=400)(scope, receive, send)
        if length > limit:
            return await JSONResponse({'detail': 'Request too large'}, status_code=413)(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect': return
            body.extend(message.get('body', b''))
            if len(body) > limit:
                return await JSONResponse({'detail': 'Request too large'}, status_code=413)(scope, receive, send)
            if not message.get('more_body', False): break
        delivered = False
        async def bounded_receive():
            nonlocal delivered
            if delivered: return await receive()
            delivered = True
            return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
        await self.app(scope, bounded_receive, send)


async def read_upload(file):
    contents = await file.read(MAX_UPLOAD + 1)
    if len(contents) > MAX_UPLOAD:
        raise HTTPException(413, 'Audio upload exceeds 25 MiB')
    if not contents:
        raise HTTPException(400, 'Audio upload is empty')
    return contents
