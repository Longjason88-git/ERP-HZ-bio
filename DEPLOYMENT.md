# ERP系统部署指南

## 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 2GB 可用内存
- 至少 5GB 可用磁盘空间

---

## 快速开始

### Linux/Mac 用户

```bash
# 克隆项目后，在项目根目录执行：
chmod +x start.sh
./start.sh
```

### Windows 用户

```bash
# 克隆项目后，在项目根目录双击运行：
start.bat
```

---

## 手动部署

### 1. 克隆项目

```bash
git clone <你的仓库地址>
cd <项目目录>
```

### 2. 创建必要目录

```bash
mkdir -p static
```

### 3. 启动服务

```bash
docker compose up -d --build
```

### 4. 等待服务启动

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f web
```

### 5. 访问系统

打开浏览器访问：
- **应用地址**: http://localhost:8080
- **管理后台**: http://localhost:8080/admin/

---

## 默认账号

### 管理员账号
- 用户名: `admin`
- 密码: `admin123`

### 数据库账号
- 数据库: `erpdb`
- 用户名: `erpuser`
- 密码: `erp123456`

> ⚠️ **安全提示**: 请在首次登录后修改默认密码！

---

## 常用命令

### 服务管理

```bash
# 查看所有容器状态
docker compose ps

# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 重启单个服务
docker compose restart web
docker compose restart db
docker compose restart nginx
```

### 日志查看

```bash
# 查看所有日志
docker compose logs -f

# 查看Web服务日志
docker compose logs -f web

# 查看数据库日志
docker compose logs -f db

# 查看Nginx日志
docker compose logs -f nginx
```

### 数据库操作

```bash
# 进入数据库容器
docker compose exec db psql -U erpuser erpdb

# 备份数据库
docker compose exec db pg_dump -U erpuser erpdb > backup.sql

# 恢复数据库
docker compose exec -T db psql -U erpuser erpdb < backup.sql
```

### Django操作

```bash
# 进入Web容器
docker compose exec web bash

# 执行Django管理命令
docker compose exec web python manage.py <command>

# 创建超级用户
docker compose exec web python manage.py createsuperuser

# 执行数据库迁移
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# 收集静态文件
docker compose exec web python manage.py collectstatic --noinput
```

---

## 项目结构

```
项目根目录/
├── .env                  # 环境变量配置
├── .gitignore            # Git忽略文件
├── CLAUDE.md             # Claude开发指南
├── DEPLOYMENT.md         # 部署指南（本文件）
├── SYSTEM_OVERVIEW.md    # 系统概述
├── docker-compose.yml    # Docker编排文件
├── start.sh              # Linux/Mac启动脚本
├── start.bat             # Windows启动脚本
├── nginx/
│   └── default.conf      # Nginx配置
├── django/
│   ├── Dockerfile        # Django镜像构建
│   ├── requirements.txt  # Python依赖
│   └── app/              # Django应用代码
│       ├── manage.py
│       ├── config/       # 项目配置
│       └── crm/          # CRM应用
├── static/               # 静态文件目录
└── postgres_data/        # 数据库数据（自动创建）
```

---

## 环境变量

系统使用 `.env` 文件管理环境变量：

```env
POSTGRES_DB=erpdb
POSTGRES_USER=erpuser
POSTGRES_PASSWORD=erp123456
DB_HOST=db
DB_PORT=5432
```

如需修改，编辑项目根目录的 `.env` 文件。

---

## 端口说明

| 服务 | 内部端口 | 外部端口 | 说明 |
|------|---------|--------|------|
| Nginx | 80 | 8080 | Web入口 |
| Django | 8000 | - | 应用服务 |
| PostgreSQL | 5432 | 5432 | 数据库 |

---

## 故障排除

### 问题：服务无法启动

```bash
# 检查Docker是否运行
docker info

# 查看日志
docker compose logs

# 重新构建并启动
docker compose up -d --build
```

### 问题：无法访问8080端口

```bash
# 检查端口是否被占用
# Linux/Mac:
lsof -i :8080
# Windows:
netstat -ano | findstr :8080

# 检查Nginx日志
docker compose logs nginx
```

### 问题：数据库连接失败

```bash
# 检查数据库容器状态
docker compose ps db

# 查看数据库日志
docker compose logs db

# 进入数据库检查
docker compose exec db psql -U erpuser erpdb -c "\l"
```

### 问题：静态文件无法加载

```bash
# 重新收集静态文件
docker compose exec web python manage.py collectstatic --noinput

# 检查Nginx配置
docker compose exec nginx nginx -t
```

---

## 从其他项目迁移

如果你是从旧版本迁移，请注意：

1. **容器名称变更**: 旧版本使用 `django` 作为容器名，新版本使用 `web`
   - 所有 `docker compose exec django` 命令需要改为 `docker compose exec web`

2. **路径变更**: 所有路径现在都是相对的，不再依赖 `/home/erp` 目录

3. **启动方式**: 新增了一键启动脚本 `start.sh` 和 `start.bat`

---

## 安全建议

生产环境部署时，请务必：

1. [ ] 修改默认的 `SECRET_KEY`
2. [ ] 设置 `DEBUG = False`
3. [ ] 限制 `ALLOWED_HOSTS`
4. [ ] 修改数据库密码
5. [ ] 修改管理员密码
6. [ ] 配置HTTPS
7. [ ] 定期备份数据库

---

## 技术支持

如有问题，请查看：
- 项目文档：`SYSTEM_OVERVIEW.md`
- 功能说明：`新功能使用说明_品牌货号自动查价.md`
- 实现总结：`实现总结_品牌货号自动查价.md`
