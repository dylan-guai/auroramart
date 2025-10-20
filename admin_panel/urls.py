from django.urls import path, include
from . import views
from . import customer_views
from . import inventory_views
from . import product_views
from . import association_views
from . import security_views
from . import return_views
from . import order_views

app_name = 'admin_panel'

urlpatterns = [
    # Authentication
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    path('reset-password/', views.admin_password_reset_request, name='password_reset_request'),
    path('reset-password/<uuid:token>/', views.admin_password_reset_confirm, name='password_reset_confirm'),
    path('change-password/', security_views.change_password, name='password_change'),
    
    # Dashboard
    path('', views.admin_dashboard, name='dashboard'),
    
    # User Management (Super Admin/Admin only)
    path('users/', views.admin_user_list, name='user_list'),
    path('users/create/', views.admin_user_create, name='user_create'),
    path('users/<int:user_id>/', views.admin_user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', views.admin_user_edit, name='user_edit'),
    path('users/<int:user_id>/toggle/', views.admin_user_toggle, name='user_toggle'),
    
    # Role Management (Super Admin/Admin only)
    path('roles/', views.admin_role_list, name='role_list'),
    path('roles/create/', views.admin_role_create, name='role_create'),
    path('roles/<int:role_id>/edit/', views.admin_role_edit, name='role_edit'),
    
    # Audit Logs (Super Admin/Admin only)
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    path('audit-logs/export/', views.audit_logs_export, name='audit_logs_export'),
    
    # Customer Management (CRM/Admin)
    path('customers/', customer_views.customer_list, name='customer_list'),
    path('customers/<int:customer_id>/', customer_views.customer_detail, name='customer_detail'),
    path('customers/<int:customer_id>/orders/', customer_views.customer_orders, name='customer_orders'),
    path('customers/<int:customer_id>/rescore/', customer_views.rescore_customer, name='customer_rescore'),
    path('customers/export/', customer_views.export_customers, name='customer_export'),
    
    # AI Predictions (CRM/Analyst/Admin)
    path('ai-predictions/', customer_views.ai_predictions_dashboard, name='ai_predictions'),
    path('ai-predictions/batch-rescore/', customer_views.batch_rescore_customers, name='batch_rescore'),
    
    # Order Management (Admin/CRM/Inventory)
    path('orders/', order_views.order_management, name='order_management'),
    path('orders/<int:order_id>/', order_views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/update-status/', order_views.update_order_status, name='update_order_status'),
    path('orders/<int:order_id>/update-payment/', order_views.update_payment_status, name='update_payment_status'),
    path('orders/analytics/', order_views.order_analytics, name='order_analytics'),
    
    # Return Management (CRM/Admin)
    path('returns/', return_views.return_management, name='return_management'),
    path('returns/<int:return_id>/', return_views.return_detail, name='return_detail'),
    path('returns/<int:return_id>/approve/', return_views.approve_return, name='approve_return'),
    path('returns/<int:return_id>/reject/', return_views.reject_return, name='reject_return'),
    path('returns/<int:return_id>/shipped/', return_views.mark_return_shipped, name='mark_return_shipped'),
    path('returns/<int:return_id>/received/', return_views.mark_return_received, name='mark_return_received'),
    path('returns/<int:return_id>/refund/', return_views.process_refund, name='process_refund'),
    path('returns/<int:return_id>/close/', return_views.close_return, name='close_return'),
    
    # Product Management (Merchandiser/Admin)
    path('products/', product_views.product_list, name='product_list'),
    path('products/create/', product_views.product_create, name='product_create'),
    path('products/bulk-import/', product_views.product_bulk_import, name='product_bulk_import'),
    path('products/bulk-export/', product_views.product_bulk_export, name='product_bulk_export'),
    path('products/performance/', product_views.product_performance_dashboard, name='product_performance'),
    path('products/<int:product_id>/', product_views.product_detail, name='product_detail'),
    path('products/<int:product_id>/edit/', product_views.product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', product_views.product_delete, name='product_delete'),
    
    # Category Management (Merchandiser/Admin)
    path('categories/', product_views.category_list, name='category_list'),
    path('categories/create/', product_views.category_create, name='category_create'),
    path('categories/<int:category_id>/edit/', product_views.category_edit, name='category_edit'),
    
    # Price Management (Merchandiser/Admin)
    path('prices/', product_views.price_history, name='price_history'),
    path('prices/<int:product_id>/change/', product_views.price_change, name='price_change'),
    
    # Inventory Management (Inventory/Admin)
    path('inventory/', inventory_views.inventory_overview, name='inventory_overview'),
    path('inventory/low-stock/', inventory_views.low_stock_alerts, name='low_stock_alerts'),
    path('inventory/adjustments/', inventory_views.stock_adjustments, name='stock_adjustments'),
    path('inventory/adjustments/create/', inventory_views.stock_adjustment_create, name='stock_adjustment_create'),
    path('inventory/receiving/', inventory_views.receiving_management, name='receiving_management'),
    path('inventory/reorder-suggestions/', inventory_views.reorder_suggestions, name='reorder_suggestions'),
    path('inventory/export/', inventory_views.export_inventory, name='inventory_export'),
    
    # Association Rules Management (Analyst/Admin)
    path('association-rules/', association_views.association_rules_dashboard, name='association_rules_dashboard'),
    path('association-rules/<str:rule_id>/', association_views.association_rule_detail, name='association_rule_detail'),
    path('association-rules/<str:rule_id>/approve/', association_views.approve_association_rule, name='approve_association_rule'),
    path('association-rules/<str:rule_id>/reject/', association_views.reject_association_rule, name='reject_association_rule'),
    path('association-rules/export/', association_views.association_rules_export, name='association_rules_export'),
    path('association-rules/retrain/', association_views.retrain_association_rules, name='retrain_association_rules'),
    path('ai-analytics/', association_views.ai_recommendations_analytics, name='ai_recommendations_analytics'),
    
    # Reports (Analyst/Admin)
    # path('reports/', views.reports_dashboard, name='reports'),
    # path('reports/export/', views.reports_export, name='reports_export'),
    
    # Analytics Dashboard (Analyst/Admin)
    path('analytics/', views.admin_analytics_dashboard, name='analytics_dashboard'),
    
    # Loyalty Management (Analyst/Admin)
    path('loyalty/', views.loyalty_management, name='loyalty_management'),
    
    # Security & Session Management
    path('security/', security_views.security_settings, name='security_settings'),
    path('logout-all/', security_views.logout_all_sessions, name='logout_all_sessions'),
    path('extend-session/', security_views.extend_session, name='extend_session'),
    path('session-status/', security_views.session_status, name='session_status'),
    path('heartbeat/', security_views.heartbeat, name='heartbeat'),
]
