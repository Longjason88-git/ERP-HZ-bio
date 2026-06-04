from django.db import models
from django.contrib.auth.models import User
from datetime import date
from decimal import Decimal


# ==================== 客户分组模块 ====================

class CustomerGroup(models.Model):
    """
    课题组 / 公司 分组
    便于对同一课题组的多个客户进行统一管理
    """
    GROUP_TYPE_CHOICES = [
        ('lab', '课题组'),
        ('company', '公司/企业'),
        ('hospital', '医院'),
        ('other', '其他'),
    ]

    name = models.CharField('分组名称', max_length=200, unique=True)
    group_type = models.CharField(
        '分组类型', max_length=20,
        choices=GROUP_TYPE_CHOICES, default='lab'
    )
    institution = models.CharField('所属单位', max_length=255, blank=True)
    pi_name = models.CharField('负责人/PI', max_length=100, blank=True)
    pi_phone = models.CharField('负责人电话', max_length=50, blank=True)
    pi_email = models.EmailField('负责人邮箱', blank=True)
    address = models.TextField('地址', blank=True)
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '客户分组'
        verbose_name_plural = '客户分组管理'
        ordering = ['group_type', 'name']

    def __str__(self):
        return '{} [{}]'.format(self.name, self.get_group_type_display())

    def member_count(self):
        return self.customers.count()
    member_count.short_description = '成员数'


# ==================== 折扣等级模块 ====================

class DiscountLevel(models.Model):
    """
    折扣等级（A-E，可在后台自由配置）
    A最优，E最差（或无折扣）
    """
    CUSTOMER_TYPE_CHOICES = [
        ('research', '科研终端'),
        ('industrial', '工业终端'),
        ('dealer', '经销商'),
    ]

    LEVEL_CHOICES = [
        ('A', 'A级'),
        ('B', 'B级'),
        ('C', 'C级'),
        ('D', 'D级'),
        ('E', 'E级'),
    ]

    customer_type = models.CharField(
        '客户类型', max_length=20,
        choices=CUSTOMER_TYPE_CHOICES
    )
    level = models.CharField(
        '等级', max_length=1,
        choices=LEVEL_CHOICES
    )
    description = models.CharField(
        '等级说明', max_length=200, blank=True,
        help_text='如：回款周期30天内、年采购额5万以上等'
    )
    default_discount = models.DecimalField(
        '默认折扣(%)', max_digits=5, decimal_places=1,
        default=100,
        help_text='100=无折扣，90=九折，85=八五折'
    )

    class Meta:
        verbose_name = '折扣等级'
        verbose_name_plural = '折扣等级管理'
        unique_together = [('customer_type', 'level')]
        ordering = ['customer_type', 'level']

    def __str__(self):
        return '{} {} 级 ({}%)'.format(
            self.get_customer_type_display(),
            self.level,
            self.default_discount
        )


class BrandDiscount(models.Model):
    """
    品牌专属折扣
    针对不同客户类型+等级，设置该品牌的特殊折扣
    优先级高于 DiscountLevel 的默认折扣
    """
    brand = models.ForeignKey(
        'Brand', on_delete=models.CASCADE,
        related_name='discounts', verbose_name='品牌'
    )
    customer_type = models.CharField(
        '客户类型', max_length=20,
        choices=DiscountLevel.CUSTOMER_TYPE_CHOICES
    )
    level = models.CharField(
        '等级', max_length=1,
        choices=DiscountLevel.LEVEL_CHOICES
    )
    discount = models.DecimalField(
        '折扣(%)', max_digits=5, decimal_places=1,
        default=100
    )
    notes = models.CharField('备注', max_length=200, blank=True)

    class Meta:
        verbose_name = '品牌折扣'
        verbose_name_plural = '品牌折扣设置'
        unique_together = [('brand', 'customer_type', 'level')]
        ordering = ['brand', 'customer_type', 'level']

    def __str__(self):
        return '{} - {} {} 级: {}%'.format(
            self.brand.name,
            self.get_customer_type_display(),
            self.level,
            self.discount
        )


# ==================== 客户模块 ====================

class Customer(models.Model):
    """客户档案 - 生物医药试剂耗材"""

    STATUS_CHOICES = [
        ('potential', '潜在客户'),
        ('active', '活跃客户'),
        ('inactive', '沉睡客户'),
        ('lost', '流失客户'),
    ]

    SOURCE_CHOICES = [
        ('wechat', '微信介绍'),
        ('xiaohongshu', '小红书'),
        ('xianyu', '咸鱼'),
        ('taobao', '淘宝'),
        ('dealer', '经销商介绍'),
        ('other', '其他'),
    ]

    CUSTOMER_TYPE_CHOICES = [
        ('research', '科研终端'),
        ('industrial', '工业终端'),
        ('dealer', '经销商'),
    ]

    LEVEL_CHOICES = [
        ('A', 'A级'),
        ('B', 'B级'),
        ('C', 'C级'),
        ('D', 'D级'),
        ('E', 'E级'),
    ]

    # 基本信息
    name = models.CharField('姓名', max_length=100)
    institution = models.CharField('单位', max_length=255, blank=True)
    lab_group = models.CharField('课题组', max_length=255, blank=True)
    phone = models.CharField('电话', max_length=50, blank=True)
    email = models.EmailField('邮箱', blank=True)
    birthday = models.DateField('生日', null=True, blank=True)
    research_direction = models.CharField('研究方向', max_length=500, blank=True)

    # 分组关联
    customer_group = models.ForeignKey(
        CustomerGroup, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='customers',
        verbose_name='所属分组'
    )

    # 客户分类与等级
    customer_type = models.CharField(
        '客户类型', max_length=20,
        choices=CUSTOMER_TYPE_CHOICES,
        default='research'
    )
    level = models.CharField(
        '客户等级', max_length=1,
        choices=LEVEL_CHOICES,
        default='C'
    )
    # 自定义折扣（覆盖等级默认折扣，为空则使用等级默认）
    custom_discount = models.DecimalField(
        '自定义折扣(%)', max_digits=5, decimal_places=1,
        null=True, blank=True,
        help_text='留空则使用等级默认折扣，填写则覆盖'
    )

    # 业务信息
    status = models.CharField(
        '客户状态', max_length=20,
        choices=STATUS_CHOICES, default='potential'
    )
    source = models.CharField(
        '客户来源', max_length=20,
        choices=SOURCE_CHOICES, default='other'
    )

    # 发票信息
    invoice_title = models.CharField('发票抬头', max_length=200, blank=True)
    invoice_tax_id = models.CharField('纳税人识别号', max_length=50, blank=True)
    invoice_bank = models.CharField('开户行', max_length=100, blank=True)
    invoice_bank_account = models.CharField('银行账号', max_length=100, blank=True)
    invoice_address = models.CharField('注册地址', max_length=200, blank=True)
    invoice_phone = models.CharField('注册电话', max_length=50, blank=True)

    # 常用收货地址
    default_shipping_address = models.TextField('常用收货地址', blank=True)
    default_shipping_contact = models.CharField('收货联系人', max_length=50, blank=True)
    default_shipping_phone = models.CharField('收货电话', max_length=50, blank=True)

    # 备注 & 负责人
    notes = models.TextField('备注', blank=True)
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='负责人'
    )

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '客户'
        verbose_name_plural = '客户列表'
        ordering = ['-created_at']

    def __str__(self):
        return '{} - {}'.format(self.name, self.institution)

    # ---- 生日相关 ----
    @property
    def birthday_this_year(self):
        if not self.birthday:
            return None
        today = date.today()
        try:
            return self.birthday.replace(year=today.year)
        except ValueError:
            return self.birthday.replace(year=today.year, day=28)

    @property
    def days_until_birthday(self):
        if not self.birthday:
            return None
        today = date.today()
        bday = self.birthday_this_year
        delta = (bday - today).days
        if delta < 0:
            try:
                bday_next = self.birthday.replace(year=today.year + 1)
            except ValueError:
                bday_next = self.birthday.replace(year=today.year + 1, day=28)
            delta = (bday_next - today).days
        return delta

    @property
    def is_birthday_week(self):
        days = self.days_until_birthday
        return False if days is None else 0 <= days <= 7

    @property
    def is_birthday_today(self):
        if not self.birthday:
            return False
        today = date.today()
        return (
            self.birthday.month == today.month
            and self.birthday.day == today.day
        )

    # ---- 折扣相关 ----
    def get_discount_for_brand(self, brand=None):
        """
        获取该客户对某品牌的折扣率
        优先级：客户自定义 > 品牌专属折扣 > 等级默认折扣 > 100
        """
        # 1. 客户有自定义折扣
        if self.custom_discount is not None:
            return self.custom_discount

        # 2. 品牌专属折扣
        if brand is not None:
            try:
                bd = BrandDiscount.objects.get(
                    brand=brand,
                    customer_type=self.customer_type,
                    level=self.level
                )
                return bd.discount
            except BrandDiscount.DoesNotExist:
                pass

        # 3. 等级默认折扣
        try:
            dl = DiscountLevel.objects.get(
                customer_type=self.customer_type,
                level=self.level
            )
            return dl.default_discount
        except DiscountLevel.DoesNotExist:
            pass

        return Decimal('100')

    def get_discount_display_text(self):
        """折扣显示文字"""
        rate = self.get_discount_for_brand()
        if rate >= 100:
            return '无折扣'
        discount_val = rate / 10
        return '{}折 ({}%)'.format(
            '{:.4g}'.format(float(discount_val)),
            rate
        )

    def get_last_order_info(self):
        """获取最近一次订单的地址、发票、付款信息"""
        last_order = self.orders.exclude(
            status='cancelled'
        ).order_by('-created_at').first()
        if not last_order:
            return {}
        return {
            'shipping_contact': last_order.shipping_contact,
            'shipping_phone': last_order.shipping_phone,
            'shipping_address': last_order.shipping_address,
            'shipping_method': last_order.shipping_method,
            'invoice_type': last_order.invoice_type,
            'invoice_title': last_order.invoice_title,
            'invoice_tax_id': last_order.invoice_tax_id,
            'invoice_bank': last_order.invoice_bank,
            'invoice_bank_account': last_order.invoice_bank_account,
            'invoice_address': last_order.invoice_address,
            'invoice_phone': last_order.invoice_phone,
            'invoice_email': last_order.invoice_email,
            'payment_term': last_order.payment_term,
            'payment_method': last_order.payment_method,
        }

    @property
    def total_order_amount(self):
        from django.db.models import Sum
        result = self.orders.filter(
            status__in=['confirmed', 'shipped', 'completed']
        ).aggregate(total=Sum('final_amount'))
        return result['total'] or Decimal('0')


class FollowUp(models.Model):
    """跟进记录"""

    TYPE_CHOICES = [
        ('wechat', '微信'),
        ('phone', '电话'),
        ('email', '邮件'),
        ('visit', '上门拜访'),
        ('other', '其他'),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE,
        related_name='followups', verbose_name='客户'
    )
    follow_type = models.CharField(
        '跟进方式', max_length=20, choices=TYPE_CHOICES
    )
    content = models.TextField('跟进内容')
    next_action = models.CharField('下次行动', max_length=500, blank=True)
    next_date = models.DateField('下次跟进日期', null=True, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, verbose_name='记录人'
    )
    created_at = models.DateTimeField('记录时间', auto_now_add=True)

    class Meta:
        verbose_name = '跟进记录'
        verbose_name_plural = '跟进记录'
        ordering = ['-created_at']

    def __str__(self):
        return '{} - {}'.format(
            self.customer.name, self.get_follow_type_display()
        )


# ==================== 产品模块 ====================

class Brand(models.Model):
    """品牌管理"""

    name = models.CharField('品牌名称', max_length=100, unique=True)
    name_en = models.CharField('英文名', max_length=100, blank=True)
    country = models.CharField('产地', max_length=50, blank=True)
    remark = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '品牌'
        verbose_name_plural = '品牌管理'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_discount(self, customer_type, level):
        """获取该品牌对指定客户类型和等级的折扣"""
        try:
            bd = self.discounts.get(
                customer_type=customer_type,
                level=level
            )
            return bd.discount
        except BrandDiscount.DoesNotExist:
            try:
                dl = DiscountLevel.objects.get(
                    customer_type=customer_type,
                    level=level
                )
                return dl.default_discount
            except DiscountLevel.DoesNotExist:
                return Decimal('100')


class Product(models.Model):
    """产品目录"""

    CATEGORY_CHOICES = [
        ('reagent', '试剂'),
        ('consumable', '耗材'),
        ('kit', '试剂盒'),
        ('antibody', '抗体'),
        ('instrument', '仪器设备'),
        ('other', '其他'),
    ]

    STORAGE_CHOICES = [
        ('rt', '室温'),
        ('4', '4°C'),
        ('-20', '-20°C'),
        ('-80', '-80°C'),
        ('ln2', '液氮'),
    ]

    brand = models.ForeignKey(
        Brand, on_delete=models.PROTECT,
        verbose_name='品牌', null=True, blank=True
    )
    category = models.CharField(
        '产品类别', max_length=20,
        choices=CATEGORY_CHOICES, default='reagent'
    )
    name = models.CharField('产品名称', max_length=200)
    name_en = models.CharField('英文名称', max_length=200, blank=True)
    catalog_number = models.CharField('货号', max_length=100, unique=True)
    cas_number = models.CharField('CAS号', max_length=50, blank=True)
    spec = models.CharField('规格/包装', max_length=100)
    unit = models.CharField('销售单位', max_length=20, default='个')

    # 价格体系
    dealer_price = models.DecimalField(
        '经销商价(元)', max_digits=10, decimal_places=2,
        null=True, blank=True
    )
    list_price = models.DecimalField(
        '目录价(元)', max_digits=10, decimal_places=2,
        null=True, blank=True
    )
    terminal_price = models.DecimalField(
        '终端价(元)', max_digits=10, decimal_places=2,
        null=True, blank=True
    )

    storage = models.CharField(
        '存储条件', max_length=10,
        choices=STORAGE_CHOICES, default='4'
    )
    lead_time = models.IntegerField('货期(工作日)', default=7)
    is_active = models.BooleanField('在售', default=True)
    description = models.TextField('产品描述', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '产品'
        verbose_name_plural = '产品目录'
        ordering = ['brand__name', 'catalog_number']

    def __str__(self):
        brand_name = self.brand.name if self.brand else '未知品牌'
        return '[{}] {} {} {}'.format(
            brand_name, self.catalog_number, self.name, self.spec
        )

    @property
    def gross_margin(self):
        if (
            self.dealer_price
            and self.terminal_price
            and self.terminal_price > 0
        ):
            return round(
                float(self.terminal_price - self.dealer_price)
                / float(self.terminal_price) * 100,
                1
            )
        return None


# ==================== 订单模块 ====================

class Order(models.Model):
    """销售订单主表"""

    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('confirmed', '已确认'),
        ('purchasing', '采购中'),
        ('shipped', '已发货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    INVOICE_TYPE_CHOICES = [
        ('none', '不开票'),
        ('normal', '普通发票'),
        ('vat', '增值税专用发票'),
    ]

    INVOICE_STATUS_CHOICES = [
        ('pending', '待开票'),
        ('submitted', '已递交财务'),
        ('issued', '已开票'),
        ('not_required', '无需开票'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', '未付款'),
        ('partial', '部分付款'),
        ('paid', '已付款'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('transfer', '银行转账'),
        ('alipay', '支付宝'),
        ('wechat', '微信'),
        ('cash', '现金'),
        ('monthly', '月结'),
        ('other', '其他'),
    ]

    SHIPPING_METHOD_CHOICES = [
        ('sf_normal', '顺丰普通'),
        ('sf_reagent', '顺丰试剂'),
        ('sf_cold', '顺丰冷链'),
        ('ems', 'EMS'),
        ('jd', '京东快递'),
        ('zto', '中通快递'),
        ('pickup', '自提'),
        ('other', '其他'),
    ]

    PAYMENT_TERM_CHOICES = [
        ('prepay', '款到发货'),
        ('cod', '货到付款'),
        ('monthly_30', '月结30天'),
        ('monthly_60', '月结60天'),
        ('other', '其他'),
    ]

    order_no = models.CharField('订单编号', max_length=30, unique=True)
    order_date = models.DateField('订单日期', default=date.today)
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT,
        related_name='orders', verbose_name='客户'
    )
    sales_rep = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='orders', verbose_name='业务员'
    )
    status = models.CharField(
        '订单状态', max_length=20,
        choices=STATUS_CHOICES, default='draft'
    )

    shipping_contact = models.CharField('收货联系人', max_length=50, blank=True)
    shipping_phone = models.CharField('收货电话', max_length=50, blank=True)
    shipping_address = models.TextField('收货地址', blank=True)
    shipping_method = models.CharField(
        '发货方式', max_length=20,
        choices=SHIPPING_METHOD_CHOICES,
        default='sf_normal', blank=True
    )
    tracking_number = models.CharField('快递单号', max_length=100, blank=True)
    shipped_date = models.DateField('发货日期', null=True, blank=True)

    invoice_type = models.CharField(
        '发票类型', max_length=20,
        choices=INVOICE_TYPE_CHOICES, default='normal'
    )
    invoice_status = models.CharField(
        '开票状态', max_length=20,
        choices=INVOICE_STATUS_CHOICES, default='pending'
    )
    invoice_title = models.CharField('发票抬头', max_length=200, blank=True)
    invoice_tax_id = models.CharField('纳税人识别号', max_length=50, blank=True)
    invoice_bank = models.CharField('开户行', max_length=100, blank=True)
    invoice_bank_account = models.CharField('银行账号', max_length=100, blank=True)
    invoice_address = models.CharField('注册地址', max_length=200, blank=True)
    invoice_phone = models.CharField('注册电话', max_length=50, blank=True)
    invoice_email = models.EmailField('发票邮箱', blank=True)
    invoice_remark = models.CharField('开票备注', max_length=200, blank=True)

    payment_term = models.CharField(
        '付款方式', max_length=20,
        choices=PAYMENT_TERM_CHOICES, default='prepay'
    )
    payment_method = models.CharField(
        '结算方式', max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='transfer', blank=True
    )
    payment_status = models.CharField(
        '付款状态', max_length=20,
        choices=PAYMENT_STATUS_CHOICES, default='unpaid'
    )

    shipping_fee = models.DecimalField(
        '运费(元)', max_digits=8, decimal_places=2, default=0
    )
    discount_amount = models.DecimalField(
        '优惠金额(元)', max_digits=10, decimal_places=2, default=0
    )
    final_amount = models.DecimalField(
        '实际金额(元)', max_digits=12, decimal_places=2, default=0
    )
    paid_amount = models.DecimalField(
        '已付金额(元)', max_digits=12, decimal_places=2, default=0
    )

    remark = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '销售订单'
        verbose_name_plural = '订单管理'
        ordering = ['-created_at']

    def __str__(self):
        return '{} | {}'.format(self.order_no, self.customer.name)

    @classmethod
    def generate_order_no(cls):
        today = date.today().strftime('%Y%m%d')
        prefix = 'HZ-{}-'.format(today)
        last = cls.objects.filter(
            order_no__startswith=prefix
        ).order_by('order_no').last()
        num = int(last.order_no.split('-')[-1]) + 1 if last else 1
        return '{}{}'.format(prefix, str(num).zfill(3))

    def recalculate_amount(self):
        items_total = sum(item.subtotal for item in self.items.all())
        self.final_amount = (
            items_total + self.shipping_fee - self.discount_amount
        )
        self.save(update_fields=['final_amount'])

    @property
    def unpaid_amount(self):
        return self.final_amount - self.paid_amount

    @property
    def items_total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_profit(self):
        profits = [
            item.profit for item in self.items.all()
            if item.profit is not None
        ]
        return sum(profits) if profits else None

    def save(self, *args, **kwargs):
        if not self.order_no:
            self.order_no = self.generate_order_no()
        if self.invoice_type == 'none':
            self.invoice_status = 'not_required'
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """订单明细行"""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='items', verbose_name='订单'
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='产品'
    )

    brand_name = models.CharField('品牌', max_length=100, blank=True)
    catalog_number = models.CharField('货号', max_length=100)
    product_name = models.CharField('产品名称', max_length=200)
    spec = models.CharField('规格', max_length=100, blank=True)
    unit = models.CharField('单位', max_length=20, default='个')

    quantity = models.DecimalField(
        '数量', max_digits=10, decimal_places=2, default=1
    )
    list_price = models.DecimalField(
        '目录价(元)', max_digits=10, decimal_places=2,
        null=True, blank=True
    )
    discount = models.DecimalField(
        '折扣(%)', max_digits=5, decimal_places=1, default=100
    )
    unit_price = models.DecimalField(
        '成交单价(元)', max_digits=10, decimal_places=2
    )
    cost_price = models.DecimalField(
        '经销商价(元)', max_digits=10, decimal_places=2,
        null=True, blank=True
    )
    tax_rate = models.DecimalField(
        '税率(%)', max_digits=5, decimal_places=2, default=13
    )
    remark = models.CharField('备注', max_length=200, blank=True)

    class Meta:
        verbose_name = '订单明细'
        verbose_name_plural = '订单明细'

    def __str__(self):
        return '{} {}'.format(self.catalog_number, self.product_name)

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    @property
    def profit(self):
        if self.cost_price is not None:
            return (self.unit_price - self.cost_price) * self.quantity
        return None

    @property
    def profit_rate(self):
        if self.profit is not None and self.unit_price > 0:
            return round(
                float(self.profit) / float(self.subtotal) * 100, 1
            )
        return None


class Payment(models.Model):
    """回款记录"""

    METHOD_CHOICES = [
        ('transfer', '银行转账'),
        ('alipay', '支付宝'),
        ('wechat', '微信'),
        ('cash', '现金'),
        ('other', '其他'),
    ]

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='payments', verbose_name='订单'
    )
    amount = models.DecimalField(
        '回款金额(元)', max_digits=12, decimal_places=2
    )
    method = models.CharField(
        '付款方式', max_length=20,
        choices=METHOD_CHOICES, default='transfer'
    )
    payment_date = models.DateField('回款日期')
    remark = models.CharField('备注', max_length=200, blank=True)
    recorded_by = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name='记录人'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '回款记录'
        verbose_name_plural = '回款记录'
        ordering = ['-payment_date']

    def __str__(self):
        return '{} 回款 ¥{}'.format(self.order.order_no, self.amount)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        order = self.order
        total_paid = sum(p.amount for p in order.payments.all())
        order.paid_amount = total_paid
        if total_paid >= order.final_amount:
            order.payment_status = 'paid'
        elif total_paid > 0:
            order.payment_status = 'partial'
        else:
            order.payment_status = 'unpaid'
        order.save(update_fields=['paid_amount', 'payment_status'])
