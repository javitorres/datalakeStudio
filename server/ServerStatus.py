from config import Config
from services import databaseService
from services import mapsService
from services import authService
from services import mailService

class ServerStatus:
    _instance = None
    config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServerStatus, cls).__new__(cls)
            print("Initializing server...")

            cls.config = Config.get_instance()

            # Initialize databaseService (stores config/secrets, creates base dirs)
            databaseService.init(cls.config.get_secrets, cls.config.get_config)

            # Initialize mail service (before auth, since auth checks mail config)
            mailService.init(cls.config.get_secrets)

            # Initialize auth service
            authService.init(cls.config.get_config, cls.config.get_secrets)

            # Initialize maps service
            try:
                mapsService.init(cls.config.get_secrets)
            except Exception as e:
                print(f"Maps service init warning: {e}")

            cls._instance.serverStatus = {"databaseReady": True}

        return cls._instance

    def get(self):
        return self.serverStatus

    def getConfig(self):
        return self.config.get_config
