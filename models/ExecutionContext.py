class ExecutionContext:
    def __init__(self, cmd, args, msg, author, send_message, choice_callback, loading_callback, isadmin):
        self.cmd = cmd
        self.args = args
        self.msg = msg
        self.author = author
        self.send_message = send_message
        self.choice_callback = choice_callback
        self.loading_callback = loading_callback
        self.isadmin = isadmin

    def voice_channel(self):
        return self.author.voice and self.author.voice.channel