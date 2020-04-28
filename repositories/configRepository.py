class ConfigRepository:
    config = None
    _update_config = None
    
    def __init__(self, config, update_config):
        self.config = config
        self._update_config = update_config

    def update_config(self, new_cfg):
        self._update_config(new_cfg)
        self.config = new_cfg