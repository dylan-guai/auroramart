# ml_service.py
import joblib
import pandas as pd
from django.conf import settings
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

class MLService:
    _decision_tree_model = None
    _association_rules_model = None
    _dt_feature_columns = None  # To store the feature columns for the decision tree
    _models_loaded = False

    def __init__(self):
        self._load_models()

    def _load_models(self):
        """Load the ML models from disk"""
        try:
            # Load Decision Tree Classifier
            dt_model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'b2c_customers_100.joblib')
            if os.path.exists(dt_model_path):
                self._decision_tree_model = joblib.load(dt_model_path)
                # Feature columns based on the notebook analysis
                self._dt_feature_columns = [
                    'age', 'household_size', 'has_children', 'monthly_income_sgd',
                    'gender_Female', 'gender_Male',
                    'employment_status_Full-time', 'employment_status_Part-time', 
                    'employment_status_Retired', 'employment_status_Self-employed', 
                    'employment_status_Student',
                    'occupation_Admin', 'occupation_Education', 'occupation_Sales', 
                    'occupation_Service', 'occupation_Skilled Trades', 'occupation_Tech',
                    'education_Bachelor', 'education_Diploma', 'education_Doctorate', 
                    'education_Master', 'education_Secondary'
                ]
                logger.info(f"Decision Tree model loaded successfully from {dt_model_path}")
            else:
                logger.warning(f"Decision Tree model not found at {dt_model_path}")

            # Load Association Rules
            ar_model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'b2c_products_500_transactions_50k.joblib')
            if os.path.exists(ar_model_path):
                self._association_rules_model = joblib.load(ar_model_path)
                logger.info(f"Association Rules model loaded successfully from {ar_model_path}")
            else:
                logger.warning(f"Association Rules model not found at {ar_model_path}")
            
            self._models_loaded = True
            
        except Exception as e:
            logger.error(f"Error loading ML models: {e}")
            self._models_loaded = False

    def predict_preferred_category(self, user_profile_data):
        """
        Predict preferred category for a user based on demographics
        
        Args:
            user_profile_data (Profile or dict): User demographic data
            
        Returns:
            dict: {'success': bool, 'predicted_category': Category, 'confidence': float}
        """
        if not self._decision_tree_model or not self._dt_feature_columns:
            return {'success': False, 'error': 'Model not loaded'}

        try:
            # Convert Profile object to dictionary if needed
            if hasattr(user_profile_data, 'age'):
                # It's a Profile object
                profile_data = {
                    'age': user_profile_data.age or 0,
                    'gender': user_profile_data.gender or 'Male',
                    'employment_status': user_profile_data.employment_status or 'Full-time',
                    'occupation': user_profile_data.occupation or 'Other',
                    'education': user_profile_data.education or 'Secondary',
                    'income_range': user_profile_data.income_range or 'low',
                    'household_size': user_profile_data.household_size or 1,
                    'has_children': user_profile_data.has_children or False,
                    'monthly_income_sgd': float(user_profile_data.monthly_income_sgd or 0),
                }
            else:
                # It's already a dictionary
                profile_data = user_profile_data
            
            # Prepare input data for prediction
            input_df = pd.DataFrame([profile_data])
            
            # One-hot encode categorical variables if they exist
            categorical_columns = ['gender', 'employment_status', 'occupation', 'education']
            existing_categorical = [col for col in categorical_columns if col in input_df.columns]
            
            if existing_categorical:
                input_encoded = pd.get_dummies(input_df, columns=existing_categorical)
            else:
                input_encoded = input_df.copy()

            # Ensure all required columns are present and in the correct order
            for col in self._dt_feature_columns:
                if col not in input_encoded.columns:
                    if col.startswith('gender_') or col.startswith('employment_status_') or \
                       col.startswith('occupation_') or col.startswith('education_'):
                        input_encoded[col] = False  # For one-hot encoded boolean columns
                    else:
                        input_encoded[col] = 0  # For numeric columns
            
            input_encoded = input_encoded[self._dt_feature_columns]

            prediction = self._decision_tree_model.predict(input_encoded)
            predicted_category_name = prediction[0] if prediction else None
            
            if predicted_category_name:
                # Map predicted category names to actual database category names
                category_mapping = {
                    'Fashion - Men': 'Fashion',
                    'Fashion - Women': 'Fashion',
                    'Fashion': 'Fashion',
                    'Electronics': 'Electronics',
                    'Home & Kitchen': 'Home & Kitchen',
                    'Beauty & Personal Care': 'Beauty & Personal Care',
                    'Sports & Outdoors': 'Sports & Outdoors',
                    'Books': 'Books',
                    'Groceries & Gourmet': 'Groceries & Gourmet',
                    'Health & Wellness': 'Health & Wellness',
                }
                
                # Get the mapped category name
                mapped_category_name = category_mapping.get(predicted_category_name, predicted_category_name)
                
                # Get the actual Category object by name
                from item.models import Category
                try:
                    category = Category.objects.get(name=mapped_category_name)
                    return {
                        'success': True,
                        'predicted_category': category,
                        'confidence': 0.85  # Placeholder confidence
                    }
                except Category.DoesNotExist:
                    return {'success': False, 'error': f'Category "{mapped_category_name}" not found'}
            else:
                return {'success': False, 'error': 'No prediction generated'}
            
        except Exception as e:
            logger.error(f"Error in predict_preferred_category: {e}")
            return {'success': False, 'error': str(e)}

    def get_product_recommendations(self, product_skus, metric='confidence', top_n=5):
        """
        Get product recommendations based on association rules
        
        Args:
            product_skus (list): List of product SKUs currently in cart/viewed
            metric (str): Metric to use for ranking ('confidence', 'support', 'lift')
            top_n (int): Number of recommendations to return
            
        Returns:
            list: List of recommended product SKUs
        """
        if self._association_rules_model is None or self._association_rules_model.empty:
            return []  # Model not loaded or empty

        try:
            recommendations = set()
            for sku in product_skus:
                # Find rules where the current SKU is in the antecedents
                matched_rules = self._association_rules_model[
                    self._association_rules_model['antecedents'].apply(lambda x: sku in x)
                ]
                
                if not matched_rules.empty:
                    # Sort by the specified metric and get top rules
                    top_rules = matched_rules.sort_values(by=metric, ascending=False).head(top_n)
                    
                    # Extract consequents from top rules
                    for _, row in top_rules.iterrows():
                        recommendations.update(row['consequents'])
            
            # Remove items that are already in the input list
            recommendations.difference_update(product_skus)
            return list(recommendations)[:top_n]
            
        except Exception as e:
            logger.error(f"Error in get_product_recommendations: {e}")
            return []

    def get_frequently_bought_together(self, product_sku, top_n=3):
        """
        Get products frequently bought together with the given product
        
        Args:
            product_sku (str): SKU of the product
            top_n (int): Number of recommendations to return
            
        Returns:
            list: List of tuples (sku, confidence) for frequently bought together items
        """
        if self._association_rules_model is None or self._association_rules_model.empty:
            return []

        try:
            # Find rules where the product is in antecedents
            matched_rules = self._association_rules_model[
                self._association_rules_model['antecedents'].apply(lambda x: product_sku in x)
            ]
            
            if matched_rules.empty:
                return []
            
            # Sort by confidence and get top rules
            top_rules = matched_rules.sort_values(by='confidence', ascending=False).head(top_n)
            
            recommendations = []
            for _, row in top_rules.iterrows():
                # Get the first consequent (assuming single consequent per rule)
                consequent = list(row['consequents'])[0] if row['consequents'] else None
                if consequent and consequent != product_sku:
                    recommendations.append((consequent, row['confidence']))
            
            return recommendations[:top_n]
            
        except Exception as e:
            logger.error(f"Error in get_frequently_bought_together: {e}")
            return []

    def get_model_status(self):
        """
        Get the status of loaded models
        
        Returns:
            dict: Status information about loaded models
        """
        return {
            'models_loaded': self._models_loaded,
            'decision_tree_loaded': self._decision_tree_model is not None,
            'association_rules_loaded': self._association_rules_model is not None,
            'feature_columns_count': len(self._dt_feature_columns) if self._dt_feature_columns else 0
        }

# Initialize the MLService globally
ml_service = MLService()