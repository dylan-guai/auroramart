from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.db.models import Avg, Count
import logging

from item.models import Product, Category
from profiles.models import Profile
from checkout.models import Cart, CartItem
from .ml_service import ml_service

logger = logging.getLogger(__name__)

def transfer_session_cart_to_user(request, user):
    """Transfer session cart items to user's database cart after login"""
    try:
        session_cart = request.session.get('cart', {})
        if not session_cart:
            return
        
        # Get or create user's profile and cart
        profile = user.profile
        cart, created = Cart.objects.get_or_create(buyer=profile)
        
        items_transferred = 0
        
        for product_id_str, quantity in session_cart.items():
            try:
                product_id = int(product_id_str)
                product = Product.objects.get(id=product_id, is_active=True)
                
                # Check if product already exists in user's cart
                existing_item = CartItem.objects.filter(cart=cart, product=product).first()
                
                if existing_item:
                    # Add to existing quantity, but don't exceed stock
                    new_quantity = min(existing_item.quantity + quantity, product.stock_quantity)
                    if new_quantity > existing_item.quantity:
                        existing_item.quantity = new_quantity
                        existing_item.save()
                        items_transferred += 1
                else:
                    # Create new cart item
                    actual_quantity = min(quantity, product.stock_quantity)
                    if actual_quantity > 0:
                        CartItem.objects.create(
                            cart=cart,
                            product=product,
                            quantity=actual_quantity
                        )
                        items_transferred += 1
                        
            except (ValueError, Product.DoesNotExist):
                logger.warning(f"Invalid product ID in session cart: {product_id_str}")
                continue
        
        # Clear session cart after successful transfer
        if items_transferred > 0:
            del request.session['cart']
            request.session.modified = True
            messages.success(request, f"Added {items_transferred} item(s) from your session to your cart!")
            logger.info(f"Transferred {items_transferred} items from session cart to user {user.username}")
        
    except Exception as e:
        logger.error(f"Error transferring session cart for user {user.username}: {e}")
        # Don't show error to user as this is a background process

def index(request):
    """Homepage view for AuroraMart with AI-powered personalization"""
    # Get user profile if logged in
    profile = None
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = None
    
    # Get cart information
    total_quantity = 0
    if profile:
        try:
            cart = Cart.objects.get(buyer=profile)
            total_quantity = cart.total_items
        except Cart.DoesNotExist:
            cart = None

    # Get featured products for homepage with optimized queries
    featured_products = Product.objects.select_related('category', 'brand').filter(
        is_featured=True, 
        is_active=True, 
        stock_quantity__gt=0
    ).prefetch_related('images')[:8]
    
    # Get categories for navigation
    categories = Category.objects.filter(is_active=True)[:6]

    # AI-Powered Personalization for logged-in users
    personalized_products = None
    predicted_category = None
    if profile and profile.demographics_complete:
        try:
            # Prepare user data for ML prediction
            user_data = {
                'age': profile.age or 30,
                'household_size': profile.household_size or 2,
                'has_children': profile.has_children or False,
                'monthly_income_sgd': profile.monthly_income_sgd or 5000,
                'gender': profile.gender or 'Male',
                'employment_status': profile.employment_status or 'Full-time',
                'occupation': profile.occupation or 'Tech',
                'education': profile.education or 'Bachelor'
            }
            
            # Get AI prediction for preferred category
            prediction_result = ml_service.predict_preferred_category(user_data)
            
            if prediction_result and prediction_result.get('success'):
                predicted_category = prediction_result
                # Get products from predicted category
                try:
                    category_obj = Category.objects.get(name__icontains=prediction_result['predicted_category'])
                    personalized_products = Product.objects.select_related('category', 'brand').filter(
                        category=category_obj,
                        is_active=True,
                        stock_quantity__gt=0
                    ).prefetch_related('images')[:12]
                except Category.DoesNotExist:
                    # Fallback to any category if exact match not found
                    personalized_products = Product.objects.select_related('category', 'brand').filter(
                        is_active=True,
                        stock_quantity__gt=0
                    ).prefetch_related('images')[:12]
        except Exception as e:
            logger.error(f"AI personalization error: {e}")
            personalized_products = None
            predicted_category = None

    return render(request, "core/index.html", {
        "profile": profile,
        "total_quantity": total_quantity,
        "featured_products": featured_products,
        "categories": categories,
        "personalized_products": personalized_products,
        "predicted_category": predicted_category,
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            
            # Transfer session cart to user's database cart
            transfer_session_cart_to_user(request, user)
            
            # Get next parameter for redirect
            next_url = request.GET.get('next', reverse("core:index"))
            return HttpResponseRedirect(next_url)
        else:
            return render(request, "core/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "core/login.html")
    
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("core:index"))

def register(request):
    """User registration view for AuroraMart"""
    if request.method == "POST":
        # Get form data safely
        username = request.POST.get("username", "")
        email = request.POST.get("email", "")
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        biography = request.POST.get("biography", "")
        profile_picture = request.FILES.get("profile_picture", 'profile_pics/placeholder.jpg')
        address = request.POST.get("address", "")

        # Username validation
        try:
            UnicodeUsernameValidator()(username)
            if len(username) < 6:
                raise ValidationError("Username must be at least 6 characters long.")
            if any(char in r"""!"#$%&'()*+,./:;<=>?@[\]^`{|}~""" for char in username):
                raise ValidationError("Username cannot contain special characters.")
        except ValidationError as e:
            return render(request, "core/register.html", {
                "message": "Invalid username format.",
                "form_data": {
                    "username": username,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "age": request.POST.get("age", ""),
                    "gender": request.POST.get("gender", ""),
                    "occupation": request.POST.get("occupation", ""),
                    "education": request.POST.get("education", ""),
                    "income_range": request.POST.get("income_range", ""),
                }
            })
        
        # Password validation - using correct field names
        password = request.POST.get("password")
        confirmation = request.POST.get("confirmation")
        
        if not password or not confirmation:
            return render(request, "core/register.html", {
                "message": "Password fields are required.",
                "form_data": {
                    "username": username,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "age": request.POST.get("age", ""),
                    "gender": request.POST.get("gender", ""),
                    "occupation": request.POST.get("occupation", ""),
                    "education": request.POST.get("education", ""),
                    "income_range": request.POST.get("income_range", ""),
                }
            })
        
        if password != confirmation:
            return render(request, "core/register.html", {
                "message": "Passwords must match.",
                "form_data": {
                    "username": username,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "age": request.POST.get("age", ""),
                    "gender": request.POST.get("gender", ""),
                    "occupation": request.POST.get("occupation", ""),
                    "education": request.POST.get("education", ""),
                    "income_range": request.POST.get("income_range", ""),
                }
            })
        
        try:
            validate_password(password)
        except ValidationError as e:
            return render(request, "core/register.html", {
                "message": "Password does not meet requirements.",
                "form_data": {
                    "username": username,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "age": request.POST.get("age", ""),
                    "gender": request.POST.get("gender", ""),
                    "occupation": request.POST.get("occupation", ""),
                    "education": request.POST.get("education", ""),
                    "income_range": request.POST.get("income_range", ""),
                }
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            # Get or create profile (signal should have created it)
            profile, created = Profile.objects.get_or_create(user=user)
            profile.first_name = first_name
            profile.last_name = last_name
            profile.biography = biography
            profile.profile_picture = profile_picture
            profile.address = address
            
            # Process demographics for AI prediction with proper mapping
            age = request.POST.get('age')
            if age and age.strip():
                try:
                    profile.age = int(age)
                except (ValueError, TypeError):
                    profile.age = None
            else:
                profile.age = None
            
            # Map form gender values to model values
            gender_mapping = {'M': 'Male', 'F': 'Female', 'O': 'Other'}
            form_gender = request.POST.get('gender', '')
            profile.gender = gender_mapping.get(form_gender, '')
            
            # Map form occupation values to model values
            occupation_mapping = {
                'student': 'Other',
                'professional': 'Tech',
                'business': 'Other',
                'retired': 'Other',
                'unemployed': 'Other',
                'other': 'Other'
            }
            form_occupation = request.POST.get('occupation', '')
            profile.occupation = occupation_mapping.get(form_occupation, '')
            
            # Map form education values to model values
            education_mapping = {
                'high_school': 'Secondary',
                'diploma': 'Diploma',
                'bachelor': 'Bachelor',
                'master': 'Master',
                'phd': 'Doctorate'
            }
            form_education = request.POST.get('education', '')
            profile.education = education_mapping.get(form_education, '')
            
            # Income range mapping (already correct)
            profile.income_range = request.POST.get('income_range', '')
            
            # Save profile with all demographic data
            profile.save()
            
        except IntegrityError:
            return render(request, "core/register.html", {
                "message": "Username already taken.",
                "form_data": {
                    "username": username,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "age": request.POST.get("age", ""),
                    "gender": request.POST.get("gender", ""),
                    "occupation": request.POST.get("occupation", ""),
                    "education": request.POST.get("education", ""),
                    "income_range": request.POST.get("income_range", ""),
                }
            })
        except Exception as e:
            return render(request, "core/register.html", {
                "message": f"Registration failed: {str(e)}",
                "form_data": {
                    "username": username,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "age": request.POST.get("age", ""),
                    "gender": request.POST.get("gender", ""),
                    "occupation": request.POST.get("occupation", ""),
                    "education": request.POST.get("education", ""),
                    "income_range": request.POST.get("income_range", ""),
                }
            })
        login(request, user)
        return HttpResponseRedirect(reverse("core:index"))
    else:
        return render(request, "core/register.html")