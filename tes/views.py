from django.shortcuts import render, redirect
from django.contrib import messages

def page_viewing(request):
    """
    View to allow users to change the primary, secondary, and background colors of the website.
    The choices are stored in the session.
    """
    color_options = [
        {'name': 'Sage Green', 'primary': '#5E7A4E', 'secondary': '#C1D3B8', 'background': '#F2F7F0'},
        {'name': 'Crisp White', 'primary': '#6D28D9', 'secondary': '#F3F4F6', 'background': '#FFFFFF'},
        {'name': 'Dusty Rose', 'primary': '#BE7D5B', 'secondary': '#E5D3C5', 'background': '#FDF4EF'},
    ]

# 🛒 Premium Store
# Background: #0F172A
# Primary: #F97316
# Secondary: #38BDF8
# 💼 Luxury Store
# Background: #0B0B0F
# Primary: #EAB308
# Secondary: #A1A1AA
# ⚡ Modern Tech Store
# Background: #020617
# Primary: #6366F1
# Secondary: #22C55E


    if request.method == 'POST':
        primary = request.POST.get('primary')
        secondary = request.POST.get('secondary')
        background = request.POST.get('background')

        if primary and secondary and background:
            request.session['primary_color'] = primary
            request.session['secondary_color'] = secondary
            request.session['background_color'] = background
            messages.success(request, "Theme colors updated successfully!")
            return redirect('page_viewing')

    context = {
        'color_options': color_options,
        'current_primary': request.session.get('primary_color', '#7C3AED'),
        'current_secondary': request.session.get('secondary_color', '#F3F0F0'),
        'current_background': request.session.get('background_color', '#F3F0F0'),
    }
    return render(request, 'page_viewing.html', context)
