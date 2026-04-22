def theme_colors(request):
    """
    Context processor to provide primary, secondary and background colors from the session.
    """
    return {
        'primary_color': request.session.get('primary_color', '#004f00'),
        'secondary_color': request.session.get('secondary_color', '#00591c'),
        'background_color': request.session.get('background_color', '#deffea'),
    }
