"""
REST API endpoint'ы для запросов информации от ККТ (queryData)
"""
from fastapi import APIRouter, Depends

from ..api.redis_client import RedisClient, get_redis_client
from ..api.libfptr10 import IFptr

router = APIRouter(prefix="/query", tags=["Query"])


# ========== БАЗОВЫЕ ЗАПРОСЫ СТАТУСА ==========

@router.get("/status")
async def get_status(redis: RedisClient = Depends(get_redis_client)):
    """
    Запрос общей информации и статуса ККТ (LIBFPTR_DT_STATUS)
    """
    return redis.execute_command('query_data', {'data_type': IFptr.LIBFPTR_DT_STATUS})


@router.get("/short-status")
async def get_short_status(redis: RedisClient = Depends(get_redis_client)):
    """Короткий запрос статуса ККТ (LIBFPTR_DT_SHORT_STATUS)"""
    return redis.execute_command('query_data', {'data_type': IFptr.LIBFPTR_DT_SHORT_STATUS})


@router.get("/cash-sum")
async def get_cash_sum(redis: RedisClient = Depends(get_redis_client)):
    """Запрос суммы наличных в денежном ящике (LIBFPTR_DT_CASH_SUM)"""
    return redis.execute_command('query_data', {'data_type': IFptr.LIBFPTR_DT_CASH_SUM})


@router.get("/shift-state")
async def get_shift_state(redis: RedisClient = Depends(get_redis_client)):
    """Запрос состояния смены (LIBFPTR_DT_SHIFT_STATE)"""
    return redis.execute_command('query_data', {'data_type': IFptr.LIBFPTR_DT_SHIFT_STATE})


@router.get("/receipt-state")
async def get_receipt_state(redis: RedisClient = Depends(get_redis_client)):
    """Запрос состояния чека (LIBFPTR_DT_RECEIPT_STATE)"""
    return redis.execute_command('query_data', {'data_type': IFptr.LIBFPTR_DT_RECEIPT_STATE})

