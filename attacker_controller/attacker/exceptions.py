class AttackerNotFound(Exception):
    """Attacker with provided phone number doesn't exist."""

    def __init__(self):
        self.message = 'اتکری با این شماره یافت نشد.'
        super().__init__(self.message)
