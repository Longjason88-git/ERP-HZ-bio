# ERP系统说明书（供AI阅读理解）

> 生成日期：2025-01-XX
> 用途：让任何AI大模型快速理解本系统的架构和功能，便于后续维护和开发。

---

## 1. 系统概述

这是一个**生物医药试剂耗材销售公司的ERP/CRM系统**。

核心业务流程：
- 销售人员管理客户（课题组、医院、公司）
- 根据客户等级和品牌给出不同折扣
- 创建销售订单（含产品明细、发票、物流信息）
- 记录回款、管理开票流程
- 从供应商处采购产品（Excel导入产品目录）

---

## 2. 技术栈

| 层级 | 技术 |
|------|------|
| Web框架 | Django 5.2 |
| 数据库 | PostgreSQL（Docker容器内） |
| 反向代理 | Nginx |
| 部署 | Docker Compose |
| Excel处理 | openpyxl |
| 前端 | Django模板（服务端渲染） |

---

## 3. 目录结构
/home/erp/
├── docker-compose.yml # 容器编排
├── .env # 环境变量（数据库密码等）
├── nginx/
│ └── default.conf # Nginx配置
└── django/
├── Dockerfile # Python镜像构建
├── requirements.txt # Python依赖
└── app/ # Django项目根目录
├── manage.py # Django管理入口
├── config/ # 项目配置
│ ├── settings.py # Django设置
│ ├── urls.py # 根路由
│ ├── wsgi.py
│ └── asgi.py
└── crm/ # 核心应用
├── models.py # 数据模型（重要）
├── views.py # 视图函数（重要）
├── urls.py # 路由配置
├── admin.py # 后台管理
└── templates/crm/ # HTML模板


---

## 4. 数据库模型关系（ER图）

### 核心表关系：
CustomerGroup (客户分组)
│ 1:N
▼
Customer (客户) ──── 1:N ──── Order (销售订单)
│ │
│ 1:N │ 1:N
▼ ▼
FollowUp (跟进记录) OrderItem (订单明细)
│ N:1
▼
Product (产品) ──── N:1 ──── Brand (品牌)
│ 1:N
▼
BrandDiscount (品牌折扣)

Order (订单) ──── 1:N ──── Payment (回款记录)
DiscountLevel (折扣等级) —— 独立配置表


### 各表字段说明：

#### CustomerGroup（客户分组）
- name: 分组名称
- group_type: 类型（课题组/公司/医院/其他）
- institution: 所属单位
- pi_name/pi_phone/pi_email: 负责人信息

#### Customer（客户）
- 基本信息：name, institution, lab_group, phone, email, birthday
- 分组：customer_group (FK → CustomerGroup)
- 分类等级：customer_type(科研/工业/经销商), level(A-E)
- 折扣：custom_discount(自定义折扣，覆盖默认)
- 业务信息：status(潜在/活跃/沉睡/流失), source(来源渠道)
- 发票信息：invoice_title, invoice_tax_id, invoice_bank等
- 收货信息：default_shipping_address等
- 关键方法：get_discount_for_brand() → 三级折扣优先级

#### DiscountLevel（折扣等级）
- customer_type + level → 唯一
- default_discount: 默认折扣百分比（100=无折扣，90=九折）

#### BrandDiscount（品牌专属折扣）
- brand + customer_type + level → 唯一
- 优先级高于 DiscountLevel 的默认折扣

#### Brand（品牌）
- name, name_en, country

#### Product（产品）
- brand (FK → Brand)
- category: 试剂/耗材/试剂盒/抗体/仪器/其他
- catalog_number: 货号（唯一）
- 价格体系：dealer_price(经销商价), list_price(目录价), terminal_price(终端价)
- storage: 存储条件（室温/4°C/-20°C/-80°C/液氮）
- lead_time: 货期

#### Order（销售订单）
- order_no: 编号（格式：HZ-20250101-001）
- customer (FK → Customer), sales_rep (FK → User)
- status: draft/confirmed/purchasing/shipped/completed/cancelled
- 物流：shipping_contact/phone/address, shipping_method, tracking_number
- 发票：invoice_type/ status/title/tax_id等
- 付款：payment_term(款到发货/月结等), payment_status
- 金额：shipping_fee, discount_amount, final_amount, paid_amount
- 关键方法：generate_order_no(), recalculate_amount()

#### OrderItem（订单明细）
- 冗余存储了品牌、货号、产品名（即使产品被删除，订单记录保留）
- quantity, list_price, discount, unit_price, cost_price
- 计算属性：subtotal, profit, profit_rate

#### Payment（回款记录）
- order (FK → Order), amount, method, payment_date
- save()方法自动更新订单的paid_amount和payment_status

#### FollowUp（跟进记录）
- customer (FK → Customer)
- follow_type: 微信/电话/邮件/上门/其他
- content, next_action, next_date

---

## 5. URL路由表

| URL | 方法 | 功能 | 视图函数 |
|-----|------|------|----------|
| /crm/login/ | GET/POST | 登录 | login_view |
| /crm/logout/ | GET | 登出 | logout_view |
| /crm/ | GET | 仪表盘首页 | dashboard |
| /crm/customers/ | GET | 客户列表 | customer_list |
| /crm/customers/add/ | GET/POST | 添加客户 | customer_add |
| /crm/customers/<pk>/ | GET | 客户详情 | customer_detail |
| /crm/customers/<pk>/edit/ | GET/POST | 编辑客户 | customer_edit |
| /crm/customers/<pk>/followup/ | GET/POST | 添加跟进 | followup_add |
| /crm/orders/ | GET | 订单列表 | order_list |
| /crm/orders/create/ | GET/POST | 创建订单 | order_create |
| /crm/orders/<pk>/ | GET | 订单详情 | order_detail |
| /crm/orders/<pk>/status/ | POST | 更新订单状态 | order_update_status |
| /crm/orders/<order_pk>/payment/ | POST | 添加回款 | payment_add |
| /crm/orders/bulk-export/ | POST | 批量导出开票明细 | order_bulk_export |
| /crm/orders/export/ | GET | 导出订单Excel | export_orders_excel |
| /crm/products/ | GET | 产品列表 | product_list |
| /crm/products/import/ | GET/POST | Excel导入产品 | product_import |
| /crm/products/<pk>/edit/ | POST | 产品行内编辑 | product_inline_edit |
| /crm/products/bulk-delete/ | POST | 批量删除产品 | product_bulk_delete |
| /crm/api/products/search/ | GET | 产品搜索API(JSON) | product_search_api |
| /crm/api/customers/<pk>/info/ | GET | 客户信息API(JSON) | customer_info_api |

---

## 6. 折扣计算逻辑（重要业务逻辑）

三级优先级（从高到低）：
1. **客户自定义折扣**：Customer.custom_discount（最高优先级）
2. **品牌专属折扣**：BrandDiscount表（品牌 × 客户类型 × 等级）
3. **等级默认折扣**：DiscountLevel表（客户类型 × 等级）
4. **兜底**：100%（无折扣）

折扣值含义：100=无折扣，90=九折，85=八五折

---

## 7. 已知问题和待改进项

### 严重问题：
- [ ] DEBUG = True（生产环境应设为False）
- [ ] ALLOWED_HOSTS = ["*"]（应限定域名/IP）
- [ ] SECRET_KEY 是默认生成的（应更换）
- [ ] TIME_ZONE = 'UTC'（中国应用 Asia/Shanghai）

### 性能问题：
- [ ] 仪表盘生日查询：Python循环所有客户，应改为数据库查询
- [ ] 订单列表存在N+1查询问题
- [ ] 所有列表页无分页（产品列表硬编码[:200]）

### 功能缺失：
- [ ] 订单无法编辑（创建后只能改状态）
- [ ] 客户编辑页面不完整（发票/折扣/分组字段缺失）
- [ ] 无统计报表页面
- [ ] 无用户权限分级
- [ ] 无操作日志

---

## 8. 部署信息

- 服务器系统：Ubuntu
- 部署方式：Docker Compose
- 容器：django(app) + db(PostgreSQL) + nginx
- 对外端口：8080（Nginx）→ Django
- 数据库：PostgreSQL，数据存储在Docker volume中

### 常用运维命令：
```bash
# 查看容器状态（新版本docker）
cd /home/erp && docker compose ps

# 进入Django容器
docker compose exec django bash

# 查看日志
docker compose logs django
docker compose logs db

# 数据库备份
docker compose exec db pg_dump -U erpuser erpdb > backup.sql

# 数据库恢复
docker compose exec -T db psql -U erpuser erpdb < backup.sql

# 重启服务
docker compose restart

# 重建并重启
docker compose up -d --build

## 9. 文件修改指南
修改代码后的标准流程：
cd /home/erp
# 1. 修改代码文件
nano django/app/crm/views.py

# 2. 如果修改了models.py，需要执行迁移
docker compose exec django python manage.py makemigrations
docker compose exec django python manage.py migrate

# 3. 如果修改了requirements.txt，需要重建镜像
docker compose up -d --build

# 4. 一般代码修改后重启即可
docker compose restart django


---

## 🚨 同时我发现了两个紧急问题

### 问题1：`docker-compose` 命令不存在

你的系统可能用的是新版Docker，命令变了：

```bash
# 试试这个
docker compose ps
# 注意：中间是空格，不是横杠
