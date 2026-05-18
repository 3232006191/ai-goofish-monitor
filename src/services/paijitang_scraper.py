"""
拍机堂比价爬虫服务
搜索拍机堂同款商品，提取价格、成色、商家等信息用于多平台比价
"""
import asyncio
import json
import os
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

from src.infrastructure.config.settings import scraper_settings

PAIJITANG_BASE = "https://www.paijitang.com"
PAIJITANG_SEARCH = f"{PAIJITANG_BASE}/search"
PRICE_COMPARE_DIR = "price_compare"
PRICE_COMPARE_FILE = "paijitang_compare.json"

MAX_COMPARE_ITEMS = 20
SEARCH_TIMEOUT = 30000
PAGE_TIMEOUT = 15000


def _ensure_compare_dir() -> str:
    os.makedirs(PRICE_COMPARE_DIR, exist_ok=True)
    return PRICE_COMPARE_DIR


def _build_compare_storage_path(keyword: str) -> str:
    slug = re.sub(r"[^\w\-]", "_", (keyword or "").strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_") or "unknown"
    return os.path.join(PRICE_COMPARE_DIR, f"paijitang_{slug}.json")


def _parse_price(text: str) -> Optional[float]:
    if not text:
        return None
    cleaned = re.sub(r"[¥￥,，\s]", "", str(text))
    try:
        return round(float(cleaned), 2)
    except (ValueError, TypeError):
        return None


def _extract_device_model(keyword: str) -> str:
    """从搜索关键词中提取设备型号关键词"""
    kw = str(keyword or "").strip()
    # 规则：优先取空格前的部分（通常是型号），然后是整体
    parts = kw.split()
    for part in parts:
        # 包含字母数字混合的通常是型号
        if re.search(r"[a-zA-Z]", part) and re.search(r"\d", part):
            return part
    return kw


async def _random_sleep(min_sec: float = 0.5, max_sec: float = 2.0):
    import random
    await asyncio.sleep(random.uniform(min_sec, max_sec))


async def search_paijitang(
    keyword: str,
    max_items: int = MAX_COMPARE_ITEMS,
    *,
    headless: Optional[bool] = None,
) -> list[dict]:
    """
    在拍机堂搜索指定关键字的商品，返回比价列表

    Args:
        keyword: 搜索关键词（通常是设备型号）
        max_items: 最大返回数量
        headless: 是否无头模式，默认取配置

    Returns:
        比价结果列表，每个元素包含：title, price, condition, link, source, images 等
    """
    if headless is None:
        headless = scraper_settings.run_headless

    device_model = _extract_device_model(keyword)
    results: list[dict] = []

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        }
        browser = await p.chromium.launch(**launch_kwargs)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Mobile Safari/537.36"
            ),
            viewport={"width": 412, "height": 915},
            device_scale_factor=2.625,
            is_mobile=True,
            has_touch=True,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )

        page = await context.new_page()

        try:
            # 步骤 1：访问首页
            await page.goto(PAIJITANG_BASE, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
            await _random_sleep(1, 2)

            # 步骤 2：尝试搜索
            # 拍机堂的搜索入口可能是一个搜索图标或输入框
            search_selectors = [
                'input[placeholder*="搜索"]',
                'input[type="search"]',
                'input[name="q"]',
                'input[name="keyword"]',
                ".search-input",
                "#search-input",
                'input[class*="search"]',
                'input[class*="Search"]',
            ]

            search_input = None
            for sel in search_selectors:
                try:
                    loc = page.locator(sel).first
                    if await loc.count() > 0 and await loc.is_visible():
                        search_input = loc
                        break
                except Exception:
                    continue

            if search_input:
                await search_input.click()
                await _random_sleep(0.3, 0.8)
                await search_input.fill(device_model)
                await _random_sleep(0.5, 1)
                await search_input.press("Enter")
            else:
                # 尝试直接导航到搜索 URL
                params = {"q": device_model, "keyword": device_model}
                search_url = f"{PAIJITANG_SEARCH}?{urlencode(params)}"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=SEARCH_TIMEOUT)

            await _random_sleep(2, 4)

            # 步骤 3：提取商品列表
            # 尝试多种可能的选择器（拍机堂页面结构可能变化）
            item_selectors = [
                ".goods-item",
                ".product-item",
                ".item-card",
                '[class*="goodsItem"]',
                '[class*="productItem"]',
                '[class*="itemCard"]',
                'a[href*="/goods/"]',
                'a[href*="/product/"]',
                'a[href*="/detail/"]',
                'a[href*="/item/"]',
                "li.product",
                "div.product",
            ]

            items = []
            for sel in item_selectors:
                items = page.locator(sel)
                count = await items.count()
                if count > 0:
                    break

            if await items.count() == 0:
                # 兜底：从页面中提取所有链接，寻找商品链接
                all_links = page.locator("a[href]")
                link_count = await all_links.count()
                items = all_links
                if link_count == 0:
                    print(f"[拍机堂] 未找到搜索结果元素，关键词: {device_model}")
                    return results

            count = min(await items.count(), max_items * 2)  # 多取一些做筛选
            for i in range(count):
                if len(results) >= max_items:
                    break
                try:
                    item = items.nth(i)
                    if not await item.is_visible():
                        continue

                    # 提取标题
                    title = ""
                    title_selectors = [
                        ".goods-title", ".product-title", ".item-title",
                        '[class*="title"]', "h3", "h4", "p", "span",
                    ]
                    for ts in title_selectors:
                        t = item.locator(ts).first
                        if await t.count() > 0:
                            text = (await t.inner_text()).strip()
                            if text and len(text) > 2:
                                title = text
                                break

                    # 提取价格
                    price_text = ""
                    price_selectors = [
                        ".goods-price", ".product-price", ".item-price",
                        '[class*="price"]', ".price", '[class*="Price"]',
                        'span[class*="red"]',
                    ]
                    for ps in price_selectors:
                        p_el = item.locator(ps).first
                        if await p_el.count() > 0:
                            price_text = (await p_el.inner_text()).strip()
                            if price_text:
                                break

                    price = _parse_price(price_text)

                    # 提取链接
                    link = ""
                    link_el = item.locator("a[href]").first
                    if await link_el.count() > 0:
                        href = await link_el.get_attribute("href")
                        if href:
                            link = href if href.startswith("http") else f"{PAIJITANG_BASE}{href}"

                    # 提取成色/状态
                    condition = ""
                    cond_selectors = [
                        '[class*="condition"]', '[class*="status"]',
                        '[class*="tag"]', ".tag",
                    ]
                    for cs in cond_selectors:
                        c_el = item.locator(cs).first
                        if await c_el.count() > 0:
                            condition = (await c_el.inner_text()).strip()
                            if condition:
                                break

                    # 提取图片
                    images = []
                    img_els = item.locator("img")
                    img_count = await img_els.count()
                    for j in range(min(img_count, 3)):
                        src = await img_els.nth(j).get_attribute("src")
                        if src and src.startswith("http"):
                            images.append(src)

                    # 筛选有效结果（至少有标题和价格）
                    if title and price and price > 0:
                        results.append({
                            "title": title,
                            "price": price,
                            "price_display": f"¥{price:.2f}",
                            "condition": condition or "未知",
                            "link": link or "",
                            "images": images,
                            "source": "拍机堂",
                            "search_keyword": device_model,
                            "search_time": datetime.now().isoformat(),
                        })

                except Exception as e:
                    print(f"[拍机堂] 解析第 {i} 个商品时出错: {e}")
                    continue

        except PlaywrightTimeoutError as e:
            print(f"[拍机堂] 搜索超时: {e}")
        except Exception as e:
            print(f"[拍机堂] 搜索异常: {e}")
        finally:
            await browser.close()

    return results


def save_compare_results(keyword: str, results: list[dict]) -> str:
    """保存比价结果到 JSON 文件"""
    _ensure_compare_dir()
    path = _build_compare_storage_path(keyword)
    payload = {
        "keyword": keyword,
        "updated_at": datetime.now().isoformat(),
        "result_count": len(results),
        "results": results,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def load_compare_results(keyword: str) -> Optional[list[dict]]:
    """加载已保存的比价结果"""
    path = _build_compare_storage_path(keyword)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("results", [])
    except Exception:
        return None


def list_compare_keywords() -> list[dict]:
    """列出所有已比价的关键词"""
    _ensure_compare_dir()
    entries = []
    for fname in os.listdir(PRICE_COMPARE_DIR):
        if not fname.startswith("paijitang_") or not fname.endswith(".json"):
            continue
        path = os.path.join(PRICE_COMPARE_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            entries.append({
                "keyword": data.get("keyword", ""),
                "result_count": data.get("result_count", 0),
                "updated_at": data.get("updated_at", ""),
                "file": fname,
            })
        except Exception:
            continue
    return sorted(entries, key=lambda e: e.get("updated_at", ""), reverse=True)


async def run_comparison(
    keyword: str,
    *,
    max_items: int = MAX_COMPARE_ITEMS,
    force_refresh: bool = False,
) -> dict:
    """
    执行一次完整的比价流程

    Returns:
        {"keyword": str, "results": list[dict], "cached": bool, "search_time": str}
    """
    if not force_refresh:
        cached = load_compare_results(keyword)
        if cached is not None:
            return {
                "keyword": keyword,
                "results": cached,
                "cached": True,
                "result_count": len(cached),
                "search_time": datetime.now().isoformat(),
            }

    results = await search_paijitang(keyword, max_items=max_items)
    save_compare_results(keyword, results)

    return {
        "keyword": keyword,
        "results": results,
        "cached": False,
        "result_count": len(results),
        "search_time": datetime.now().isoformat(),
    }