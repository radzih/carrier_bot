import json
import typing
import logging
import aiohttp

async def request(
    method: typing.Literal['get', 'post'], 
    url: str, 
    excpected_status: int = 200,
    **kwargs
    ) -> dict | str | bytes:
    logger = logging.getLogger(__name__)
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, **kwargs) as response:
            if response.status != excpected_status and response.status != 200:
                logger.error(
                    f'{response.status} {response.reason}\n'
                    f'{await response.text()}\n {url}{kwargs}'
                    )
                await session.close()
            try:
                response_data = await response.text()
            except UnicodeDecodeError:
                return await response.read()
            try:
                response_data = json.loads(response_data)
            except json.JSONDecodeError:
                pass
    return response_data
