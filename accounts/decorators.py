from django.shortcuts import render
from functools import wraps

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return render(request, 'account/login.html') # Login pe bhej do
            
            # User ke roles check karo
            user_roles = request.user.get_roles()
            
            # Agar user ke paas allowed roles mein se koi bhi hai, toh allow karo
            if any(role in allowed_roles for role in user_roles):
                return view_func(request, *args, **kwargs)
            
            # Varna Access Denied (403)
            return render(request, '403.html', status=403)
        return _wrapped_view
    return decorator