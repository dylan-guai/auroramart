from django import forms
from item.models import Category

class CategoryFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label="Filter by Category",
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    PRICE_CHOICES = [
        ('all', 'All Prices'),
        ('1-5', '$1-5'),
        ('6-10', '$6-10'),
        ('11-15', '$11-15'),
        ('16-20', '$16-20'),
        ('21-25', '$21-25'),
        ('26+', 'More than $26'),
    ]
    price_range = forms.ChoiceField(choices=PRICE_CHOICES, required=False, label="Price Range")

    SORT_CHOICES = [
    ('price_asc', 'Price: Low to High'),
    ('price_desc', 'Price: High to Low'),
    ('rating', 'Most Likes'),
    ]
    sort_by = forms.ChoiceField(choices=SORT_CHOICES, required=False, label="Sort By")