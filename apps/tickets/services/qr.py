import base64
import io

import qrcode
from django.conf import settings

from apps.tickets.models import Ticket


def checkin_url(ticket: Ticket) -> str:
    """티켓 체크인 페이지의 절대 URL."""
    return f"{settings.API_BASE_URL.rstrip('/')}/api/v1/tickets/{ticket.pk}/checkin/"


def generate_ticket_qr(ticket: Ticket) -> str:
    """
    티켓 체크인 URL을 담은 QR 코드를 base64(PNG) 문자열로 반환한다.

    QR을 스캔하면 체크인 페이지로 진입하는 입장 플로우를 구성한다.
    """
    img = qrcode.make(checkin_url(ticket))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()
