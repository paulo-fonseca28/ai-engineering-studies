"""Optional shared operator token for local deployments; required in production mode."""
import hmac
import os
from starlette.responses import JSONResponse


def validate_configuration():
    if os.environ.get('SUPPORTOPS_ENV', 'local') == 'production' and len(os.environ.get('SUPPORTOPS_API_KEY', '')) < 32:
        raise RuntimeError('Production requires SUPPORTOPS_API_KEY with at least 32 characters')


async def access_control(request, call_next):
    public = request.url.path in {'/', '/ui.js', '/ui.css', '/health', '/docs', '/openapi.json', '/docs/oauth2-redirect'}
    key = os.environ.get('SUPPORTOPS_API_KEY', '')
    if key and not public:
        supplied = request.headers.get('authorization', '').removeprefix('Bearer ')
        if not hmac.compare_digest(supplied.encode(), key.encode()):
            return JSONResponse({'detail': 'authentication_required'}, status_code=401)
    if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        origin = request.headers.get('origin')
        if origin and origin.rstrip('/') != str(request.base_url).rstrip('/'):
            return JSONResponse({'detail': 'cross_origin_request_rejected'}, status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['X-Frame-Options'] = 'DENY'
    if request.url.path in {'/', '/ui.js', '/ui.css'}:
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
    response.headers['Cache-Control'] = 'no-store'
    return response
