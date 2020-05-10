from utils.linq import first

class ConfigRepository:
    config = None
    _update_config = None
    
    def __init__(self, config, update_config):
        self.config = config
        self._update_config = update_config

    def update_config(self, new_cfg):
        self._update_config(new_cfg)
        self.config = new_cfg

    def bind_vk_user(self, vk_user_id, discord_user_id):
        self.config['discord_vk_map'] = list(filter(
            lambda b: b[0] != vk_user_id, # allowed multiple vk accounts for discord user
            self.config['discord_vk_map']
        ))
        self.config['discord_vk_map'].append([vk_user_id, discord_user_id])
        self.__update_config()

    def get_discord_user_id_bound_to_vk(self, vk_user_id):
        array = self.config['discord_vk_map']
        matching = first(array, lambda b: b[0] == vk_user_id)
        return matching and matching[1]

    def get_next_vk_message_id(self):
        next_id = self.config['vk_last_message_id'] + 1
        self.config['vk_last_message_id'] = next_id
        self.__update_config()
        return next_id

    def __update_config(self):
        self.update_config(self.config)