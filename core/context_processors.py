from django.conf import settings

def contact_info(request):
    """
    Returns site contact information from settings to all templates.
    """
    return {
        'contact': getattr(settings, 'SITE_CONTACT', {})
    }
