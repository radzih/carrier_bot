from tgbot.misc.invoice_payload import InvoicePayload


package_payment_payload = InvoicePayload(
    'package_payment',
    'redis_key',
    sep='|',
)