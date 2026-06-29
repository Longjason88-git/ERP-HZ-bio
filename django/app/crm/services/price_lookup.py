"""
产品查价服务：本地库查询 + 官网链接生成 + 官网价格抓取
"""
import re
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

from django.db.models import Q

from crm.models import Brand, Product

# 常见品牌默认搜索模板（品牌名关键词 → URL模板）
DEFAULT_SEARCH_TEMPLATES = [
    (['默克', 'merck', 'sigma', '西格玛'], 'https://www.sigmaaldrich.com/CN/zh/search/{catalog_number}'),
    (['赛默飞', 'thermo', 'invitrogen', 'life technologies'], 'https://www.thermofisher.cn/search/browse/category/featured?q={catalog_number}'),
    (['abcam'], 'https://www.abcam.cn/products?keywords={catalog_number}'),
    (['cst', 'cell signaling', '细胞信号'], 'https://www.cellsignal.cn/products/primary-antibodies?Ntt={catalog_number}'),
    (['碧云天', 'beyotime'], 'https://www.beyotime.com/search.htm?keyword={catalog_number}'),
    (['索莱宝', 'solarbio'], 'https://www.solarbio.com/goods-search?keywords={catalog_number}'),
    (['生工', 'sangon', 'bbI'], 'https://www.sangon.com/search?keyword={catalog_number}'),
    (['promega'], 'https://www.promega.com.cn/products/?query={catalog_number}'),
    (['roche', '罗氏'], 'https://lifescience.roche.com/en_cn/products/search?q={catalog_number}'),
    (['qiagen', '凯杰'], 'https://www.qiagen.com/cn/search/results?q={catalog_number}'),
    (['bio-rad', '伯乐'], 'https://www.bio-rad.com/zh-cn/search?query={catalog_number}'),
    (['medchemexpress', 'mce'], 'https://www.medchemexpress.cn/search.html?q={catalog_number}'),
    (['aladdin', '阿拉丁'], 'https://www.aladdin-e.com/zh_cn/catalogsearch/result/?q={catalog_number}'),
    (['takara', '宝生物'], 'https://www.takara.com.cn/search/?q={catalog_number}'),
]

PRICE_PATTERNS = [
    re.compile(r'¥\s*([\d,]+(?:\.\d{1,2})?)'),
    re.compile(r'CNY\s*([\d,]+(?:\.\d{1,2})?)', re.I),
    re.compile(r'RMB\s*([\d,]+(?:\.\d{1,2})?)', re.I),
    re.compile(r'price["\']?\s*[:=]\s*["\']?([\d,]+(?:\.\d{1,2})?)', re.I),
    re.compile(r'listPrice["\']?\s*[:=]\s*["\']?([\d,]+(?:\.\d{1,2})?)', re.I),
    re.compile(r'目录价[^0-9]{0,20}([\d,]+(?:\.\d{1,2})?)'),
    re.compile(r'官网价[^0-9]{0,20}([\d,]+(?:\.\d{1,2})?)'),
]


def _normalize_catalog_number(catalog_number):
    return (catalog_number or '').strip()


def _match_default_template(brand):
    """根据品牌名称匹配内置搜索模板"""
    if not brand:
        return ''
    names = [
        (brand.name or '').lower(),
        (brand.name_en or '').lower(),
    ]
    for keywords, template in DEFAULT_SEARCH_TEMPLATES:
        for name in names:
            if not name:
                continue
            for kw in keywords:
                if kw in name:
                    return template
    return ''


def get_website_search_url(brand, catalog_number):
    """生成品牌官网产品搜索链接"""
    catalog_number = _normalize_catalog_number(catalog_number)
    if not catalog_number:
        return ''

    encoded = urllib.parse.quote(catalog_number)
    if brand and brand.search_url_template:
        return brand.search_url_template.replace(
            '{catalog_number}', encoded
        )

    template = _match_default_template(brand)
    if template:
        return template.replace('{catalog_number}', encoded)

    if brand and brand.website_url:
        base = brand.website_url.rstrip('/')
        return '{}/search?q={}'.format(base, encoded)

    return ''


def _parse_price(text):
    """从网页文本中提取价格"""
    if not text:
        return None
    for pattern in PRICE_PATTERNS:
        match = pattern.search(text)
        if match:
            try:
                value = Decimal(match.group(1).replace(',', ''))
                if value > 0:
                    return value
            except (InvalidOperation, ValueError):
                continue
    return None


def _fetch_page_text(url, timeout=8):
    """抓取网页内容（仅用于公开页面）"""
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        charset = 'utf-8'
        content_type = resp.headers.get_content_charset()
        if content_type:
            charset = content_type
        return raw.decode(charset, errors='replace')


def fetch_website_price(brand, catalog_number):
    """
    尝试从官网抓取价格。
    注意：部分品牌网站为动态渲染，可能无法抓取，此时返回 None。
    """
    url = get_website_search_url(brand, catalog_number)
    if not url:
        return None, ''

    try:
        html = _fetch_page_text(url)
        price = _parse_price(html)
        return price, url
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None, url


def lookup_local_products(brand_id=None, catalog_number='', query=''):
    """在本地产品库中查询"""
    catalog_number = _normalize_catalog_number(catalog_number)
    query = (query or '').strip()

    qs = Product.objects.filter(is_active=True).select_related('brand')

    if brand_id:
        qs = qs.filter(brand_id=brand_id)

    if catalog_number:
        qs = qs.filter(
            Q(catalog_number__iexact=catalog_number) |
            Q(catalog_number__icontains=catalog_number)
        )
    elif query:
        qs = qs.filter(
            Q(name__icontains=query) |
            Q(catalog_number__icontains=query) |
            Q(name_en__icontains=query) |
            Q(brand__name__icontains=query)
        )
    else:
        return []

    return list(qs[:20])


def product_to_dict(product, customer=None):
    """将产品转为 API 响应格式"""
    discount = Decimal('100')
    if customer and product.brand:
        discount = customer.get_discount_for_brand(product.brand)

    terminal_price = float(product.terminal_price) if product.terminal_price else 0
    list_price = float(product.list_price) if product.list_price else 0
    discounted_price = round(terminal_price * float(discount) / 100, 2)

    return {
        'id': product.id,
        'brand_name': product.brand.name if product.brand else '',
        'brand_id': product.brand.id if product.brand else None,
        'catalog_number': product.catalog_number,
        'product_name': product.name,
        'spec': product.spec,
        'unit': product.unit,
        'terminal_price': str(product.terminal_price) if product.terminal_price else '',
        'list_price': str(product.list_price) if product.list_price else '',
        'dealer_price': str(product.dealer_price) if product.dealer_price else '',
        'discount': str(discount),
        'discounted_price': str(discounted_price) if terminal_price > 0 else '',
        'source': 'local',
        'display': str(product),
    }


def lookup_product(brand_id=None, catalog_number='', customer=None):
    """
    综合查价：先查本地库，再生成官网链接并尝试抓取价格。
    返回 dict 包含 local_products, website_url, website_price, source 等。
    """
    catalog_number = _normalize_catalog_number(catalog_number)
    brand = None
    if brand_id:
        try:
            brand = Brand.objects.get(pk=brand_id)
        except Brand.DoesNotExist:
            pass

    local_products = lookup_local_products(
        brand_id=brand_id,
        catalog_number=catalog_number,
    )
    local_data = [
        product_to_dict(p, customer) for p in local_products
    ]

    website_url = get_website_search_url(brand, catalog_number)
    website_price = None
    price_source = ''

    # 本地无精确匹配时尝试官网抓价
    exact_local = [
        p for p in local_products
        if p.catalog_number.lower() == catalog_number.lower()
    ] if catalog_number else []

    if catalog_number and not exact_local and website_url:
        fetched_price, _ = fetch_website_price(brand, catalog_number)
        if fetched_price:
            website_price = str(fetched_price)
            price_source = 'website'

    return {
        'catalog_number': catalog_number,
        'brand_id': brand_id,
        'brand_name': brand.name if brand else '',
        'local_products': local_data,
        'has_local': len(local_data) > 0,
        'website_url': website_url,
        'website_price': website_price,
        'price_source': price_source,
    }
