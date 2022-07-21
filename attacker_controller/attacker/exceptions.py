class AttackerNotFound(Exception):
    def __init__(self):
        self.message = 'اتکری با این شماره یافت نشد.'
        super().__init__(self.message)
