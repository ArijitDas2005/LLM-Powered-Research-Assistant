from usage.models import UsageLog


class UsageLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith('/api/') and getattr(request, 'user', None) and request.user.is_authenticated:
            UsageLog.objects.create(
                user=request.user,
                usage_type=UsageLog.TYPE_API_REQUEST,
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                metadata={'query_params': dict(request.GET.items())},
            )

        return response
