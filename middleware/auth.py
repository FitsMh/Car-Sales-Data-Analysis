from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect

class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.method == "OPTIONS":
            return None
        exempt_paths = ['/app/login/', '/app/register/', '/admin/']
        for path in exempt_paths:
            if request.path_info.startswith(path):
                return None
        if not request.session.get('username'):
            return redirect('/app/login/')

        return None