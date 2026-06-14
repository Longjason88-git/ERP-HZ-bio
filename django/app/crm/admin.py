from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CustomerGroup, DiscountLevel, BrandDiscount,
    Customer, FollowUp,
    Brand, Product,
    Order, OrderItem, Payment
)


# ==================== 客户分组 ====================

@admin.register(CustomerGroup)
class CustomerGroupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'group_type', 'institution',
        'pi_name', 'pi_phone', 'member_count'
    ]
    list_filter = ['group_type']
    search_fields = ['name', 'institution', 'pi_name']


# ==================== 折扣等级 ====================

@admin.register(DiscountLevel)
class DiscountLevelAdmin(admin.ModelAdmin):
    list_display = [
        'customer_type', 'level',
        'default_discount', 'description'
    ]
    list_editable = ['default_discount', 'description']
    ordering = ['customer_type', 'level']


# ==================== 客户模块 ====================

class FollowUpInline(admin.TabularInline):
    model = FollowUp
    extra = 0
    fields = [
        'follow_type', 'content', 'next_action',
        'next_date', 'created_by'
    ]
    readonly_fields = ['created_by']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'institution', 'lab_group',
        'customer_type', 'level',
        'phone', 'status',
        'customer_group',
        'assigned_to', 'birthday_reminder',
    ]
    list_filter = [
        'status', 'source',
        'customer_type', 'level',
        'customer_group', 'assigned_to'
    ]
    search_fields = ['name', 'institution', 'lab_group', 'phone']
    inlines = [FollowUpInline]
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = [
        ('基本信息', {
            'fields': [
                'name', 'institution', 'lab_group',
                'phone', 'email', 'birthday',
                'research_direction'
            ]
        }),
        ('分组与等级', {
            'fields': [
                'customer_group',
                'customer_type', 'level',
                'custom_discount',
            ]
        }),
        ('业务信息', {
            'fields': ['status', 'source', 'assigned_to', 'notes']
        }),
        ('常用收货信息', {
            'fields': [
                'default_shipping_address',
                'default_shipping_contact',
                'default_shipping_phone'
            ],
            'classes': ['collapse']
        }),
        ('发票信息', {
            'fields': [
                'invoice_title', 'invoice_tax_id',
                'invoice_bank', 'invoice_bank_account',
                'invoice_address', 'invoice_phone'
            ],
            'classes': ['collapse']
        }),
        ('时间记录', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def birthday_reminder(self, obj):
        if obj.is_birthday_today:
            return format_html(
                '<span style="color:red;font-weight:bold">🎂 今天!</span>'
            )
        elif obj.is_birthday_week:
            days = obj.days_until_birthday
            return format_html(
                '<span style="color:orange">🎁 {}天</span>', days
            )
        return '-'
    birthday_reminder.short_description = '生日'


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = [
        'customer', 'follow_type', 'content_preview',
        'next_date', 'created_by', 'created_at'
    ]
    list_filter = ['follow_type', 'created_by']
    search_fields = ['customer__name', 'content']

    def content_preview(self, obj):
        return obj.content[:30] + '...' if len(obj.content) > 30 else obj.content
    content_preview.short_description = '跟进内容'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ==================== 品牌模块 ====================

class BrandDiscountInline(admin.TabularInline):
    """品牌折扣内嵌在品牌页面"""
    model = BrandDiscount
    extra = 0
    fields = ['customer_type', 'level', 'discount', 'notes']

    def get_extra(self, request, obj=None, **kwargs):
        if obj is None:
            return 15  # 新建品牌时预填15行（3类型×5等级）
        return 0


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'country', 'discount_summary']
    search_fields = ['name', 'name_en']
    ordering = ['name']
    inlines = [BrandDiscountInline]

    def discount_summary(self, obj):
        """显示折扣概要"""
        discounts = obj.discounts.all()
        if not discounts:
            return '使用默认折扣'
        summary = []
        for d in discounts[:3]:
            summary.append(
                '{}{}: {}%'.format(
                    d.get_customer_type_display(),
                    d.level,
                    d.discount
                )
            )
        text = ' | '.join(summary)
        if discounts.count() > 3:
            text += ' ...'
        return text
    discount_summary.short_description = '折扣设置'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'catalog_number', 'brand', 'name', 'spec', 'unit',
        'dealer_price', 'terminal_price', 'gross_margin_display',
        'storage', 'is_active'
    ]
    list_filter = ['brand', 'category', 'storage', 'is_active']
    search_fields = ['name', 'catalog_number', 'name_en', 'cas_number']
    list_editable = ['dealer_price', 'terminal_price', 'is_active']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = [
        ('基本信息', {
            'fields': [
                'brand', 'category',
                'name', 'name_en',
                'catalog_number', 'cas_number',
                'spec', 'unit',
            ]
        }),
        ('价格信息', {
            'fields': ['dealer_price', 'list_price', 'terminal_price']
        }),
        ('产品属性', {
            'fields': ['storage', 'lead_time', 'is_active', 'description']
        }),
        ('时间记录', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def gross_margin_display(self, obj):
        gm = obj.gross_margin
        if gm is None:
            return '-'
        color = 'green' if gm >= 30 else ('orange' if gm >= 15 else 'red')
        gm_str = '{:.1f}%'.format(float(gm))
        return format_html(
            '<span style="color:{};font-weight:bold">{}</span>',
            color, gm_str
        )
    gross_margin_display.short_description = '毛利率'


# ==================== 订单模块 ====================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = [
        'brand_name', 'catalog_number', 'product_name',
        'spec', 'unit', 'quantity',
        'list_price', 'discount', 'unit_price',
        'cost_price', 'remark'
    ]


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ['amount', 'method', 'payment_date', 'remark', 'recorded_by']
    readonly_fields = ['recorded_by']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_no', 'order_date',
        'customer', 'sales_rep',
        'status_badge',
        'invoice_type', 'invoice_status_badge',
        'final_amount', 'paid_amount', 'unpaid_display',
        'payment_status'
    ]
    list_filter = [
        'status', 'invoice_type',
        'invoice_status', 'payment_status',
        'order_date', 'sales_rep'
    ]
    search_fields = [
        'order_no', 'customer__name',
        'customer__institution', 'tracking_number'
    ]
    readonly_fields = ['order_no', 'created_at', 'updated_at']
    inlines = [OrderItemInline, PaymentInline]

    fieldsets = [
        ('订单基本信息', {
            'fields': [
                'order_no', 'order_date',
                'customer', 'sales_rep', 'status'
            ]
        }),
        ('收货信息', {
            'fields': [
                'shipping_contact', 'shipping_phone', 'shipping_address',
                'shipping_method', 'tracking_number', 'shipped_date'
            ]
        }),
        ('发票信息', {
            'fields': [
                'invoice_type', 'invoice_status',
                'invoice_title', 'invoice_tax_id',
                'invoice_bank', 'invoice_bank_account',
                'invoice_address', 'invoice_phone',
                'invoice_email', 'invoice_remark'
            ]
        }),
        ('付款信息', {
            'fields': [
                'payment_term', 'payment_method', 'payment_status',
                'shipping_fee', 'discount_amount',
                'final_amount', 'paid_amount'
            ]
        }),
        ('备注', {'fields': ['remark']}),
        ('时间记录', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def status_badge(self, obj):
        colors = {
            'draft': '#999', 'confirmed': '#2196F3',
            'purchasing': '#FF9800', 'shipped': '#9C27B0',
            'completed': '#4CAF50', 'cancelled': '#F44336',
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:3px;font-size:12px">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = '状态'

    def invoice_status_badge(self, obj):
        colors = {
            'pending': '#FF9800', 'submitted': '#2196F3',
            'issued': '#4CAF50', 'not_required': '#999',
        }
        color = colors.get(obj.invoice_status, '#999')
        return format_html(
            '<span style="color:{};font-weight:bold">{}</span>',
            color, obj.get_invoice_status_display()
        )
    invoice_status_badge.short_description = '开票状态'

    def unpaid_display(self, obj):
        amount = obj.unpaid_amount
        if amount > 0:
            return format_html(
                '<span style="color:red;font-weight:bold">¥{}</span>',
                amount
            )
        return format_html('<span style="color:green">已结清</span>')
    unpaid_display.short_description = '待付'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.recalculate_amount()

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Payment):
                if not instance.recorded_by_id:
                    instance.recorded_by = request.user
            instance.save()
        formset.save_m2m()
        if formset.model == OrderItem:
            form.instance.recalculate_amount()


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'amount', 'method',
        'payment_date', 'recorded_by'
    ]
    list_filter = ['method', 'payment_date']
    search_fields = ['order__order_no', 'order__customer__name']
