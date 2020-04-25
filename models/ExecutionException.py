class ExecutionException(Exception):
    def __init__(self, *args):
        self.message = args[0] if args else None
        super().__init__(*args)

    def __str__(self):
        return self.message or super().__str__()