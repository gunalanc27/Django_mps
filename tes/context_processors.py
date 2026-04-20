def theme_colors(request):
    """
    Context processor to provide primary, secondary and background colors from the session.
    """
    return {
        'primary_color': request.session.get('primary_color', None),
        'secondary_color': request.session.get('secondary_color', None),
        'background_color': request.session.get('background_color', None),
    }
