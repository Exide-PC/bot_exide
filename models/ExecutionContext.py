class ExecutionContext:
    def __init__(self, cmd, args, msg, author, author_vc, send_message, choice_callback, loading_callback, isadmin):
        self.cmd = cmd
        self.args = args
        self.msg = msg
        self.author = author
        self.author_vc = author_vc
        self.send_message = send_message
        self.choice_callback = choice_callback
        self.loading_callback = loading_callback
        self.isadmin = isadmin