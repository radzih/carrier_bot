import io
from pathlib import Path

from PIL import Image, ImageFont, ImageDraw, ImageFile # type: ignore
from PIL.ImageFont import FreeTypeFont # type: ignore
from tgbot.misc import schemas
from tgbot.services.qr_code import generate_qr_code

CURRENT_DIR = Path(__file__)

MONTHS = {
    1: 'січня',
    2: 'лютого',
    3: 'березня',
    4: 'квітня',
    5: 'травня',
    6: 'червня',
    7: 'липня',
    8: 'серпня',
    9: 'вересня',
    10: 'жовтня',
    11: 'листопада',
    12: 'грудня',
}

WEEK_DAYS = {
    1: 'Пн',
    2: 'Вт',
    3: 'Ср',
    4: 'Чт',
    5: 'Пт',
    6: 'Сб',
    7: 'Нд',
}

class TicketGenerator:
    def __init__(
        self,
        template_path: str='tgbot/services/ticket_generator/templates/ticket_template.jpg',
        package_template_path: str='tgbot/services/ticket_generator/templates/package_template.jpg',
        bold_font_path: str='tgbot/services/ticket_generator/fonts/bold.ttf',
        italic_font_path: str='tgbot/services/ticket_generator/fonts/italic.ttf',
        simple_font_path: str='tgbot/services/ticket_generator/fonts/simple.ttf',
        italic_bold_font_path: str='tgbot/services/ticket_generator/fonts/italic-bold.ttf',
    ) -> None:
        self._template_path = template_path
        self._bold_font = ImageFont.truetype(bold_font_path)
        self._italic_font = ImageFont.truetype(italic_font_path)
        self._simple_font = ImageFont.truetype(simple_font_path)
        self._italic_bold_font = ImageFont.truetype(italic_bold_font_path)
        self._template_img = Image.open(self._template_path)
        self._package_img = Image.open(package_template_path)


    async def generate_ticket(
        self,
        ticket: schemas.Ticket,
    ) -> bytes:
        copied_img = self._template_img.copy()
        draw = ImageDraw.Draw(copied_img)
        # town from
        self._draw_text(
            text=ticket.start_station.town.name,
            position=(440, 670),
            font_size=51,
            font=self._bold_font,
            color=(0,0,0),
            draw=draw,
        )
        # town to
        self._draw_text(
            text=ticket.end_station.town.name,
            position=(440, 970),
            font_size=52,
            font=self._bold_font,
            color=(0,0,0),
            draw=draw,
        )
        # station from
        self._draw_text(
            text=ticket.start_station.name,
            position=(440, 727),
            font_size=30,
            font=self._italic_font,
            color=(130,130,130),
            draw=draw,
        )
        # station to
        self._draw_text(
            text=ticket.end_station.name,
            position=(440, 1027),
            font_size=30,
            font=self._italic_font,
            color=(128,128,128),
            draw=draw,
        )
        # date from
        self._draw_text(
            text=(
                f'{ticket.departure_time.day} '
                f'{MONTHS[ticket.departure_time.month]} '
                f'{ticket.departure_time.year} '
                f'{WEEK_DAYS[ticket.departure_time.weekday() + 1]}'
            ),
            position=(440, 614),
            font_size=40,
            font=self._simple_font,
            color=(0,0,0),
            draw=draw,
        )
        # date to
        self._draw_text(
            text=(
                f'{ticket.arrival_time.day} '
                f'{MONTHS[ticket.arrival_time.month]} '
                f'{ticket.arrival_time.year} '
                f'{WEEK_DAYS[ticket.arrival_time.weekday() + 1]}'
            ),
            position=(440, 914),
            font_size=40,
            font=self._simple_font,
            color=(0,0,0),
            draw=draw,
        )
        # time from
        self._draw_text(
            text=ticket.departure_time.strftime('%H:%M'),
            position=(130, 610),
            font_size=55,
            font=self._bold_font,
            color=(0,0,0),
            draw=draw,
        )
        # time to
        self._draw_text(
            text=ticket.arrival_time.strftime('%H:%M'),
            position=(130, 910),
            font_size=55,
            font=self._bold_font,
            color=(0,0,0),
            draw=draw,
        )
        # FIO
        self._draw_text(
            text=(
                f'{ticket.passenger.surname.capitalize()} '    
                f'{ticket.passenger.name[0].upper()}.'
            ),
            position=(70, 240),
            font_size=45,
            font=self._bold_font,
            color=(0,0,0),
            draw=draw,
        )
        # ticket number
        self._draw_text(
            text=str(ticket.ticket_code),
            position=(70, 350),
            font_size=30,
            font=self._italic_font,
            color=(128,128,128),
            draw=draw,
        )
        if ticket.is_paid:
            self._draw_text(
                text='ОПЛАЧЕНО',
                position=(304, 452),
                font_size=30,
                font=self._bold_font,
                color=(31,214,85),
                draw=draw,
            )
            # paid time
            self._draw_text(
                text=ticket.paid_time.strftime('%d.%m.%Y %H:%M'),
                position=(530, 452),
                font_size=25,
                font=self._simple_font,
                color=(128, 128, 128),
                draw=draw,
            )
        else:
            self._draw_text(
                text='НЕ ОПЛАЧЕНО',
                position=(304, 452),
                font_size=30,
                font=self._bold_font,
                color=(255, 0, 0),
                draw=draw,
            )
        # price
        self._draw_text(
            text=str(ticket.price) + ' грн.',
            position=(304, 417),
            font_size=30,
            font=self._italic_font,
            color=(128,128,128),
            draw=draw,
        ) 
        # qr code
        self._paste_image(
            image_bytes=(await generate_qr_code(ticket.ticket_code)),
            position=(840, 120),
            size=(400, 400),
            img=copied_img,
        )

        if ticket.type.name != 'Дорослий':
            self._draw_text(
                text=ticket.type.name.lower(),
                font=self._italic_font,
                font_size=30,
                position=(304, 485),
                color=(128,128,128),
                draw=draw,
            )
            # discounte text 
            self._draw_text(
                text='Знижка:',
                font=self._italic_font,
                position=(530, 415),
                color=(128,128,128),
                font_size=30,
                draw=draw,
            )
            self._draw_text(
                text=f'{ticket.type.discount} %',
                font=self._italic_font,
                position=(650, 415),
                color=(128,128,128),
                font_size=30,
                draw=draw,
            )

        b = io.BytesIO()
        copied_img.save(b, format='JPEG')
        return b.getvalue()
        
    async def generate_package(
        self,
        package: schemas.Package
    ):
        copied_img = self._package_img.copy()
        draw = ImageDraw.Draw(copied_img)
        # town from
        self._draw_text(
            text=package.start_station.town.name,
            position=(440, 670),
            font_size=51,
            font=self._bold_font,
            color=(0,0,0),
            draw=draw,
        )
        # town to
        self._draw_text(
            text=package.end_station.town.name,
            position=(440, 970),
            font_size=52,
            font=self._bold_font,
            color=(0,0,0),
            draw=draw,
        )
        # station from
        self._draw_text(
            text=package.start_station.name,
            position=(440, 727),
            font_size=30,
            font=self._italic_font,
            color=(130,130,130),
            draw=draw,
        )
        # station to
        self._draw_text(
            text=package.end_station.name,
            position=(440, 1027),
            font_size=30,
            font=self._italic_font,
            color=(128,128,128),
            draw=draw,
        )
        # date from
        self._draw_text(
            text=(
                f'{package.departure_time.day} '
                f'{MONTHS[package.departure_time.month]} '
                f'{package.departure_time.year} '
                f'{WEEK_DAYS[package.departure_time.weekday() + 1]}'
            ),
            position=(440, 614),
            font_size=40,
            font=self._simple_font,
            color=(0,0,0),
            draw=draw,
        )
        # date to
        self._draw_text(
            text=(
                f'{package.arrival_time.day} '
                f'{MONTHS[package.arrival_time.month]} '
                f'{package.arrival_time.year} '
                f'{WEEK_DAYS[package.arrival_time.weekday() + 1]}'
            ),
            position=(440, 914),
            font_size=40,
            font=self._simple_font,
            color=(0,0,0),
            draw=draw,
        )
        # time from
        self._draw_text(
            text=package.departure_time.strftime('%H:%M'),
            position=(130, 610),
            font_size=55,
            font=self._bold_font,
            color=(0,0,0),
            draw=draw,
        )
        # time to
        self._draw_text(
            text=package.arrival_time.strftime('%H:%M'),
            position=(130, 910),
            font_size=55,
            font=self._bold_font,
            color=(0,0,0),
            draw=draw,
        )
        # sender fio
        self._draw_text(
            text=(
                f'{package.sender.surname.capitalize()} '    
                f'{package.sender.name[0].upper()}.'
            ),
            position=(300, 140),
            font_size=45,
            font=self._bold_font,
            color=(0,0,0),
            draw=draw,
        )
        # sender phone
        self._draw_text(
            text=package.sender.phone,
            position=(300, 198),
            font_size=40,
            font=self._simple_font,
            color=(0,0,0),
            draw=draw,
        )
        # receiver fio
        self._draw_text(
            text=(
                f'{package.receiver.surname.capitalize()} '
                f'{package.receiver.name[0].upper()}.'
            ),
            position=(300, 250),
            font_size=45,
            font=self._bold_font,
            color=(0,0,0),
            draw=draw,
        )
        # sender phone
        self._draw_text(
            text=package.receiver.phone,
            position=(300, 308),
            font_size=40,
            font=self._simple_font,
            color=(0,0,0),
            draw=draw,
        )
        # package number
        self._draw_text(
            text=str(package.package_code),
            position=(400, 58),
            font_size=50,
            font=self._bold_font,
            color=(0, 0, 0),
            draw=draw,
        )
        if package.is_paid:
            self._draw_text(
                text='ОПЛАЧЕНО',
                position=(304, 492),
                font_size=30,
                font=self._bold_font,
                color=(31,214,85),
                draw=draw,
            )
            # paid time
            self._draw_text(
                text=package.paid_time.strftime('%d.%m.%Y %H:%M'),
                position=(530, 492),
                font_size=25,
                font=self._simple_font,
                color=(128, 128, 128),
                draw=draw,
            )
        else:
            self._draw_text(
                text='НЕ ОПЛАЧЕНО',
                position=(304, 492),
                font_size=30,
                font=self._bold_font,
                color=(255, 0, 0),
                draw=draw,
            )
        # price
        self._draw_text(
            text=str(package.price) + ' грн.',
            position=(304, 452),
            font_size=30,
            font=self._italic_font,
            color=(128,128,128),
            draw=draw,
        ) 
        # qr code
        self._paste_image(
            image_bytes=(await generate_qr_code(package.package_code)),
            position=(840, 120),
            size=(400, 400),
            img=copied_img,
        )


        b = io.BytesIO()
        copied_img.save(b, format='JPEG')
        return b.getvalue()

    def _draw_text(
        self,
        text: str,
        position: tuple,
        font_size: int,
        font: FreeTypeFont,
        color: tuple,
        draw: ImageDraw,
    ) -> None:
        font = font.font_variant(size=font_size)
        draw.text(position, text, fill=color, font=font)


    def _paste_image(
        self,
        image_bytes: bytes,
        position: tuple,
        size: tuple,
        img: ImageFile,
    ) -> None:
        qr_img = Image.open(io.BytesIO(image_bytes))
        qr_img = qr_img.resize(size)
        img.paste(qr_img, position)
    

        
        