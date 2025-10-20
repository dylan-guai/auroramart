from django.shortcuts import render
from django.http import HttpResponse

def about_us(request):
    """About Us page"""
    context = {
        'title': 'About AuroraMart',
        'page_title': 'About Us'
    }
    return render(request, 'pages/about_us.html', context)

def careers(request):
    """Careers page"""
    context = {
        'title': 'Careers at AuroraMart',
        'page_title': 'Careers'
    }
    return render(request, 'pages/careers.html', context)

def privacy_policy(request):
    """Privacy Policy page"""
    context = {
        'title': 'Privacy Policy',
        'page_title': 'Privacy Policy'
    }
    return render(request, 'pages/privacy_policy.html', context)

def terms_of_service(request):
    """Terms of Service page"""
    context = {
        'title': 'Terms of Service',
        'page_title': 'Terms of Service'
    }
    return render(request, 'pages/terms_of_service.html', context)

def help_center(request):
    """Help Center page"""
    context = {
        'title': 'Help Center',
        'page_title': 'Help Center'
    }
    return render(request, 'pages/help_center.html', context)

def shipping_info(request):
    """Shipping Information page"""
    context = {
        'title': 'Shipping Information',
        'page_title': 'Shipping Info'
    }
    return render(request, 'pages/shipping_info.html', context)

def returns(request):
    """Returns page"""
    context = {
        'title': 'Returns & Exchanges',
        'page_title': 'Returns'
    }
    return render(request, 'pages/returns.html', context)

def contact_us(request):
    """Contact Us page"""
    context = {
        'title': 'Contact Us',
        'page_title': 'Contact Us'
    }
    return render(request, 'pages/contact_us.html', context)