def user_profile(request):
    """
    Adds the user's profile to the template context if the user is authenticated.
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        return {
            'user_profile': getattr(request.user, 'profile', None)
        }
    return {'user_profile': None}
