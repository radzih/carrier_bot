import json
from base64 import b64encode
from hashlib import sha1
from tgbot.misc import schemas

from tgbot.misc.request import request


async def refund_money(
    order_id: str,
    public_key: str,
    private_key: str,
    amount: int
):
    encoded_data = json.dumps(
        {
            'action': 'refund',
            'version': '3',
            'order_id': order_id,
            'public_key': public_key,
            'amount': amount,
        }
    )
    signature = create_signature(encoded_data, private_key)
    request_data = {
        'data': encoded_data,
        'signature': signature,
    }
    response = await request(
        method='POST',
        url='https://www.liqpay.ua/api/request',
        data=request_data,
    )
    return response


async def get_payment(
    payment_id: str,
    public_key: str,
    private_key: str,
) -> schemas.Payment:
    encoded_data = json.dumps(
        {
            'action': 'status',
            'version': '3',
            'payment_id': payment_id,
            'public_key': public_key,
        }
    )
    signature = create_signature(encoded_data, private_key)
    request_data = {
        'data': encoded_data,
        'signature': signature,
    }
    response = await request(
        method='POST',
        url='https://www.liqpay.ua/api/request',
        data=request_data,
    )
    return schemas.Payment(**response)


def create_signature(
    data: str,
    private_key: str,
):
    joined_fields = (private_key + data + private_key).encode()
    return b64encode(sha1(joined_fields).digest()).decode()

