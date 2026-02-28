import base64
import os


class ContentSecurityPolicyMiddleware:
    """
    Sets a Content-Security-Policy header on every response.

    A fresh cryptographic nonce is generated for each request and stored on
    ``request.csp_nonce`` so that Django templates can stamp it onto inline
    ``<script>`` tags with ``nonce="{{ request.csp_nonce }}"``.  The nonce is
    included in the ``script-src`` directive, which means *only* script tags
    that carry the matching nonce attribute are allowed to execute — all other
    inline scripts are blocked.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        nonce = base64.b64encode(os.urandom(16)).decode('ascii')
        request.csp_nonce = nonce

        response = self.get_response(request)

        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' ajax.googleapis.com; "
            "style-src 'self' ajax.googleapis.com cdn.jsdelivr.net fonts.googleapis.com; "
            "font-src fonts.gstatic.com cdn.jsdelivr.net; "
            "img-src 'self' https: data:; "
            "frame-ancestors 'none'"
        )
        return response
