from django.urls import path
from . import views

urlpatterns = [
    # 登录
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # 仪表盘
    path('', views.dashboard, name='dashboard'),

    # 客户
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:customer_pk>/followup/',
         views.followup_add, name='followup_add'),

    # 订单（注意：固定路径要放在变量路径前面）
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/bulk-export/', views.order_bulk_export, name='order_bulk_export'),
    path('orders/export/', views.export_orders_excel, name='export_orders_excel'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/status/',
         views.order_update_status, name='order_update_status'),
    path('orders/<int:order_pk>/payment/',
         views.payment_add, name='payment_add'),

    # 产品
    path('products/', views.product_list, name='product_list'),
    path('products/import/', views.product_import, name='product_import'),
    path('products/bulk-delete/',
         views.product_bulk_delete, name='product_bulk_delete'),
    path('products/<int:pk>/edit/',
         views.product_inline_edit, name='product_inline_edit'),

    # API
    path('api/products/search/',
         views.product_search_api, name='product_search_api'),
    path('api/customers/<int:pk>/info/',
         views.customer_info_api, name='customer_info_api'),
    path('api/brands/autocomplete/',
         views.brand_autocomplete_api, name='brand_autocomplete_api'),
    path('api/products/lookup/',
         views.product_lookup_api, name='product_lookup_api'),
]
