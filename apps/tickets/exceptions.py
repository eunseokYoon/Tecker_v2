class SeatsUnavailable(Exception):
    """요청한 좌석 중 하나 이상이 이미 예매됐거나 존재하지 않을 때 발생."""

    def __init__(self, seat_ids: list[int]):
        self.seat_ids = seat_ids
        super().__init__(f"좌석을 예매할 수 없습니다: {seat_ids}")


class AlreadyPaid(Exception):
    """이미 결제 완료된 Purchase에 다시 결제를 시도할 때 발생."""


class FaceAlreadyRegistered(Exception):
    """티켓에 이미 얼굴이 등록돼 있을 때 발생."""

    def __init__(self, ticket_id: int):
        self.ticket_id = ticket_id
        super().__init__(f"티켓 {ticket_id}에 얼굴이 이미 등록되어 있습니다.")


class FaceMismatch(Exception):
    """얼굴 인증 시 일치하는 Face가 없거나 유사도가 임계값 미만일 때 발생."""


class AntiSpoofUnavailable(RuntimeError):
    """안티스푸핑 서버에 연결할 수 없을 때 발생."""


class TicketNotCancelable(Exception):
    """이미 입장했거나 취소된 티켓을 다시 취소하려 할 때 발생."""

    def __init__(self, ticket_id: int, ticket_status: str):
        self.ticket_id = ticket_id
        self.ticket_status = ticket_status
        super().__init__(f"티켓 {ticket_id}는 취소할 수 없는 상태입니다: {ticket_status}")


class ShareCountMismatch(Exception):
    """공유 대상 이메일 수가 양도 가능한 티켓 수와 일치하지 않을 때 발생."""

    def __init__(self, expected: int, given: int):
        self.expected = expected
        self.given = given
        super().__init__(f"양도 가능한 티켓은 {expected}장인데 {given}명이 지정되었습니다.")


class TicketAlreadyCheckedIn(Exception):
    """이미 입장 처리된 티켓에 다시 입장 처리를 시도할 때 발생."""
