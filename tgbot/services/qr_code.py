from tgbot.misc.request import request

QR_CODE_API_URL = 'https://api.qrserver.com/v1/create-qr-code/?size={size}&data={data}'

async def generate_qr_code(info: str, size: tuple = (900, 900)) -> bytes:
    response = await request(
        method='get',
        url=QR_CODE_API_URL.format(size='x'.join(map(str, size)), data=info),
    )
    return response
