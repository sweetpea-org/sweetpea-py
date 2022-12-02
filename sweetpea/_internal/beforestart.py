
class BeforeStart:
    def __init__(self, ready_at: int) -> None:
        self.ready_at = ready_at # 0-based

    def __str__(self) -> str:
        return f"BeforeStart<{self.ready_at}>"

    def __repr__(self) -> str:
        return self.__str__()
