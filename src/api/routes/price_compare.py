"""
拍机堂比价 API 路由
支持触发比价、查询结果、比价历史管理
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query

from src.services.paijitang_scraper import (
    run_comparison,
    load_compare_results,
    list_compare_keywords,
    MAX_COMPARE_ITEMS,
)

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.get("/history")
async def get_compare_history():
    """获取所有已比价的关键词列表"""
    return {"entries": list_compare_keywords()}


@router.get("/search")
async def search_compare(
    keyword: str = Query(..., description="搜索关键词"),
    force: bool = Query(False, description="强制重新搜索（忽略缓存）"),
    limit: int = Query(MAX_COMPARE_ITEMS, ge=1, le=50, description="最大返回数量"),
):
    """
    搜索拍机堂比价数据
    默认优先返回缓存，force=true 时强制实时搜索
    """
    try:
        result = await run_comparison(
            keyword=keyword,
            max_items=limit,
            force_refresh=force,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"拍机堂比价搜索失败: {e}",
        )


@router.get("/cached/{keyword:path}")
async def get_cached_compare(keyword: str):
    """获取已缓存的比价数据（不触发实时搜索）"""
    cached = load_compare_results(keyword)
    if cached is None:
        raise HTTPException(
            status_code=404,
            detail=f"未找到关键词 '{keyword}' 的比价缓存",
        )
    return {
        "keyword": keyword,
        "results": cached,
        "cached": True,
        "result_count": len(cached),
    }


@router.post("/trigger")
async def trigger_compare(
    keyword: str = Query(..., description="触发比价的关键词"),
    background_tasks: BackgroundTasks = None,
):
    """
    手动触发比价（后台执行，立即返回）
    用于在闲鱼结果页手动触发某个商品的拍机堂比价
    """
    async def _run():
        await run_comparison(keyword=keyword, force_refresh=True)

    background_tasks.add_task(_run)
    return {
        "message": f"已触发关键词 '{keyword}' 的拍机堂比价，请稍后查询结果",
        "keyword": keyword,
    }


@router.post("/auto-compare")
async def auto_compare_batch(
    keywords: list[str],
    limit: int = Query(MAX_COMPARE_ITEMS, ge=1, le=20),
):
    """
    批量自动比价（供爬虫完成后调用）
    按顺序对多个关键词执行比价，返回汇总结果
    """
    results = []
    for kw in keywords:
        try:
            r = await run_comparison(keyword=kw, max_items=limit, force_refresh=True)
            results.append({
                "keyword": kw,
                "result_count": r.get("result_count", 0),
                "error": None,
            })
        except Exception as e:
            results.append({
                "keyword": kw,
                "result_count": 0,
                "error": str(e),
            })
    return {"compared": len(keywords), "results": results}


@router.delete("/cache/{keyword:path}")
async def delete_compare_cache(keyword: str):
    """删除指定关键词的比价缓存"""
    import os
    from src.services.paijitang_scraper import _build_compare_storage_path

    path = _build_compare_storage_path(keyword)
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail=f"未找到关键词 '{keyword}' 的比价缓存",
        )
    os.remove(path)
    return {"message": f"已删除关键词 '{keyword}' 的比价缓存"}