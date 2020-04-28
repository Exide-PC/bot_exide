class ExecutionContext:
    def __init__(self, cmd, args, msg, author, author_vc, msg_callback, choice_callback, loading_callback, execute_blocking):
        self.cmd = cmd
        self.args = args
        self.msg = msg
        self.author = author
        self.author_vc = author_vc
        self.msg_callback = msg_callback
        self.choice_callback = choice_callback
        self.loading_callback = loading_callback
        self.execute_blocking = execute_blocking