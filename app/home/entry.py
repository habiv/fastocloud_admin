from flask import session

from pyfastocloud_models.provider.login.entry import ProviderUser


class ProviderAdminUser(ProviderUser):
    SERVER_POSITION_SESSION_FIELD = 'server_position'

    def login(self):
        self.set_current_server_position(0)
        super(ProviderAdminUser, self).login()

    def logout(self):
        session.pop(ProviderAdminUser.SERVER_POSITION_SESSION_FIELD)
        super(ProviderAdminUser, self).logout()

    def set_current_server_position(self, pos: int):
        session[ProviderAdminUser.SERVER_POSITION_SESSION_FIELD] = pos

    def get_current_server(self):
        if not self.servers:
            return None

        server_settings = self.servers[session[ProviderAdminUser.SERVER_POSITION_SESSION_FIELD]]
        if server_settings:
            from app import servers_manager
            return servers_manager.find_or_create_server(server_settings)

        return None
