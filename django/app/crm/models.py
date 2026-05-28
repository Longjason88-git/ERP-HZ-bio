from django.db import models
from django.contrib.auth.models import User
from datetime import date


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

    # 基本信息
    name = models.CharField('姓名', max_length=100)
    institution = models.CharField('单位', max_length=255, blank=True)
    lab_group = models.CharField('课题组', max_length=255, blank=True)
    phone = models.CharField('电话', max_length=50, blank=True)
    email = models.EmailField('邮箱', blank=True)
    birthday = models.DateField('生日', null=True, blank=True)
    research_direction = models.CharField('研究方向', max_length=500, blank=True)

    # 业务信息
    status = models.CharField('客户状态', max_length=20,
                               choices=STATUS_CHOICES, default='potential')
    source = models.CharField('客户来源', max_length=20,
                               choices=SOURCE_CHOICES, default='other')

    # 备注
    notes = models.TextField('备注', blank=True)

    # 负责人
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL,
                                     null=True, blank=True, verbose_name='负责人')

    # 时间
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '客户'
        verbose_name_plural = '客户列表'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.institution}"

    @property
    def birthday_this_year(self):
        """今年的生日日期（用于排序和判断）"""
        if not self.birthday:
            return None
        today = date.today()
        try:
            return self.birthday.replace(year=today.year)
        except ValueError:
            # 处理2月29日
            return self.birthday.replace(year=today.year, day=28)

    @property
    def days_until_birthday(self):
        """距离生日还有几天（负数表示已过）"""
        if not self.birthday:
            return None
        today = date.today()
        bday = self.birthday_this_year
        delta = (bday - today).days
        # 如果今年已过，计算到明年
        if delta < 0:
            try:
                bday_next = self.birthday.replace(year=today.year + 1)
            except ValueError:
                bday_next = self.birthday.replace(year=today.year + 1, day=28)
            delta = (bday_next - today).days
        return delta

    @property
    def is_birthday_week(self):
        """是否在一周内过生日"""
        days = self.days_until_birthday
        if days is None:
            return False
        return 0 <= days <= 7

    @property
    def is_birthday_today(self):
        """今天是否生日"""
        if not self.birthday:
            return False
        today = date.today()
        return self.birthday.month == today.month and self.birthday.day == today.day


class FollowUp(models.Model):
    """跟进记录"""

    TYPE_CHOICES = [
        ('wechat', '微信'),
        ('phone', '电话'),
        ('email', '邮件'),
        ('visit', '上门拜访'),
        ('other', '其他'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE,
                                  related_name='followups', verbose_name='客户')
    follow_type = models.CharField('跟进方式', max_length=20, choices=TYPE_CHOICES)
    content = models.TextField('跟进内容')
    next_action = models.CharField('下次行动', max_length=500, blank=True)
    next_date = models.DateField('下次跟进日期', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    null=True, verbose_name='记录人')
    created_at = models.DateTimeField('记录时间', auto_now_add=True)

    class Meta:
        verbose_name = '跟进记录'
        verbose_name_plural = '跟进记录'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.name} - {self.get_follow_type_display()}"
