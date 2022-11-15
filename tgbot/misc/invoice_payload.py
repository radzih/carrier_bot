import typing

from aiogram import types
from aiogram.dispatcher.filters import Filter


class InvoicePayload:
    """
    Invoice payload factory
    """

    def __init__(self, prefix, *parts, sep=':'):
        if not isinstance(prefix, str):
            raise TypeError(f'Prefix must be instance of str not {type(prefix).__name__}')
        if not prefix:
            raise ValueError("Prefix can't be empty")
        if sep in prefix:
            raise ValueError(f"Separator {sep!r} can't be used in prefix")

        self.prefix = prefix
        self.sep = sep

        self._part_names = parts

    def new(self, *args, **kwargs) -> str:
        """
        Generate invoice payload

        :param args:
        :param kwargs:
        :return:
        """
        args = list(args)

        data = [self.prefix]

        for part in self._part_names:
            value = kwargs.pop(part, None)
            if value is None:
                if args:
                    value = args.pop(0)
                else:
                    raise ValueError(f'Value for {part!r} was not passed!')

            if value is not None and not isinstance(value, str):
                value = str(value)

            if self.sep in value:
                raise ValueError(f"Symbol {self.sep!r} is defined as the separator and can't be used in parts' values")

            data.append(value)

        if args or kwargs:
            raise TypeError('Too many arguments were passed!')

        invoice_payload = self.sep.join(data)
        if len(invoice_payload.encode()) > 128:
            raise ValueError('Resulted invoice payload is too long!')

        return invoice_payload

    def parse(self, invoice_payload: str) -> typing.Dict[str, str]:
        """
        Parse data from the invoice payload

        :param invoice_payload:
        :return:
        """
        prefix, *parts = invoice_payload.split(self.sep)
        if prefix != self.prefix:
            raise ValueError("Passed invoice payload can't be parsed with that prefix.")
        elif len(parts) != len(self._part_names):
            raise ValueError('Invalid parts count!')

        result = {'@': prefix}
        result.update(zip(self._part_names, parts))
        return result

    def filter(self, **config) -> 'InvoicePayloadFilter':
        """
        Generate filter

        :param config:
        :return:
        """
        for key in config.keys():
            if key not in self._part_names:
                raise ValueError(f'Invalid field name {key!r}')
        return InvoicePayloadFilter(self, config)


class InvoicePayloadFilter(Filter):

    def __init__(self, factory: InvoicePayload, config: typing.Dict[str, str]):
        self.config = config
        self.factory = factory

    @classmethod
    def validate(cls, full_config: typing.Dict[str, typing.Any]):
        raise ValueError("That filter can't be used in filters factory!")

    async def check(self, obj: types.Message | types.PreCheckoutQuery) -> bool:
        if isinstance(obj, types.Message):
            invoice_payload = obj.successful_payment.invoice_payload
        elif isinstance(obj, types.PreCheckoutQuery):
            invoice_payload = obj.invoice_payload
        else:
            return False
        try:
            data = self.factory.parse(invoice_payload)
        except ValueError:
            return False

        for key, value in self.config.items():
            if isinstance(value, (list, tuple, set, frozenset)):
                if data.get(key) not in value:
                    return False
            elif data.get(key) != value:
                return False
        return {'invoice_payload': data}