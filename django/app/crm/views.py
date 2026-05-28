from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import date, timedelta
from .models import Customer, FollowUp


# ==================== 登录/登出 ====================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, '用户名或密码错误，请重试')

    return render(request, 'crm/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ==================== 首页仪表盘 ====================

@login_required(login_url='/crm/login/')
def dashboard(request):
    today = date.today()

    # 统计数据
    total_customers = Customer.objects.count()
    active_customers = Customer.objects.filter(status='active').count()
    potential_customers = Customer.objects.filter(status='potential').count()

    # 最近添加的客户
    recent_customers = Customer.objects.all()[:5]

    # 最近跟进记录
    recent_followups = FollowUp.objects.all()[:5]

    # ========== 一周内过生日的客户 ==========
    birthday_customers = []
    all_customers_with_birthday = Customer.objects.exclude(birthday__isnull=True)

    for customer in all_customers_with_birthday:
        days = customer.days_until_birthday
        if days is not None and 0 <= days <= 7:
            birthday_customers.append({
                'customer': customer,
                'days': days,
                'is_today': days == 0,
            })

    # 按天数排序（今天的排最前）
    birthday_customers.sort(key=lambda x: x['days'])

    context = {
        'total_customers': total_customers,
        'active_customers': active_customers,
        'potential_customers': potential_customers,
        'recent_customers': recent_customers,
        'recent_followups': recent_followups,
        'birthday_customers': birthday_customers,
        'today': today,
    }
    return render(request, 'crm/dashboard.html', context)


# ==================== 客户管理 ====================

@login_required(login_url='/crm/login/')
def customer_list(request):
    customers = Customer.objects.all()

    search = request.GET.get('search', '')
    if search:
        customers = customers.filter(
            name__icontains=search
        ) | customers.filter(
            institution__icontains=search
        ) | customers.filter(
            lab_group__icontains=search
        ) | customers.filter(
            research_direction__icontains=search
        ) | customers.filter(
            phone__icontains=search
        )

    status = request.GET.get('status', '')
    if status:
        customers = customers.filter(status=status)

    source = request.GET.get('source', '')
    if source:
        customers = customers.filter(source=source)

    context = {
        'customers': customers,
        'search': search,
        'status': status,
        'source': source,
    }
    return render(request, 'crm/customer_list.html', context)


@login_required(login_url='/crm/login/')
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    followups = customer.followups.all()

    return render(request, 'crm/customer_detail.html', {
        'customer': customer,
        'followups': followups,
    })


@login_required(login_url='/crm/login/')
def customer_add(request):
    if request.method == 'POST':
        birthday_str = request.POST.get('birthday', '')
        birthday = birthday_str if birthday_str else None

        customer = Customer.objects.create(
            name=request.POST.get('name'),
            institution=request.POST.get('institution', ''),
            lab_group=request.POST.get('lab_group', ''),
            phone=request.POST.get('phone', ''),
            email=request.POST.get('email', ''),
            birthday=birthday,
            research_direction=request.POST.get('research_direction', ''),
            status=request.POST.get('status', 'potential'),
            source=request.POST.get('source', 'other'),
            notes=request.POST.get('notes', ''),
            assigned_to=request.user,
        )
        messages.success(request, f'客户 {customer.name} 已成功添加')
        return redirect('customer_detail', pk=customer.pk)

    return render(request, 'crm/customer_form.html')


@login_required(login_url='/crm/login/')
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        birthday_str = request.POST.get('birthday', '')
        customer.name = request.POST.get('name')
        customer.institution = request.POST.get('institution', '')
        customer.lab_group = request.POST.get('lab_group', '')
        customer.phone = request.POST.get('phone', '')
        customer.email = request.POST.get('email', '')
        customer.birthday = birthday_str if birthday_str else None
        customer.research_direction = request.POST.get('research_direction', '')
        customer.status = request.POST.get('status', 'potential')
        customer.source = request.POST.get('source', 'other')
        customer.notes = request.POST.get('notes', '')
        customer.save()
        messages.success(request, f'客户 {customer.name} 信息已更新')
        return redirect('customer_detail', pk=customer.pk)

    return render(request, 'crm/customer_form.html', {'customer': customer})


@login_required(login_url='/crm/login/')
def followup_add(request, customer_pk):
    customer = get_object_or_404(Customer, pk=customer_pk)

    if request.method == 'POST':
        FollowUp.objects.create(
            customer=customer,
            follow_type=request.POST.get('follow_type'),
            content=request.POST.get('content'),
            next_action=request.POST.get('next_action', ''),
            next_date=request.POST.get('next_date') or None,
            created_by=request.user,
        )
        messages.success(request, '跟进记录已保存')
        return redirect('customer_detail', pk=customer_pk)

    return render(request, 'crm/followup_form.html', {'customer': customer})
