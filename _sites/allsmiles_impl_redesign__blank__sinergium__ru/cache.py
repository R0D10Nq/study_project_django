def get_cache_salt(request):
    """Контекстная соль"""
    salt_type = request.GET.get('type', '')
    success_types = ('quiz')

    if salt_type not in success_types:
        salt_type = ''

    return f'{salt_type}'
