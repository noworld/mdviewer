class ContentSecurityPolicyMiddleware:
    CSP_VALUE = (
        "default-src 'self'; "
        "script-src 'self' ajax.googleapis.com; "
        "style-src 'self' ajax.googleapis.com cdn.jsdelivr.net fonts.googleapis.com; "
        "font-src fonts.gstatic.com cdn.jsdelivr.net; "
        "img-src 'self' https: data:; "
        "frame-ancestors 'none'"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = self.CSP_VALUE
        return response
