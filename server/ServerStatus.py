from config import Config
from services import databaseService

class ServerStatus:
    _instance = None
    config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServerStatus, cls).__new__(cls)
            print("Initializing server...")

            # Check if data folder exists in filesystem and create if not
            cls.config = Config.get_instance()
            database_path = cls.config.get_config.get("database")
            if database_path is not None:
                print("Checking data folder...")
                import os
                if not os.path.exists(database_path):
                    os.makedirs(database_path)
                    print("Data folder created")

            print("Connecting to default database..." + cls.config.get_config.get("defaultDatabase"))
            databaseService.init(cls.config.get_secrets, cls.config.get_config)
            currentDatabase = cls.config.get_config.get("defaultDatabase")[:-3]
            cls._instance.serverStatus = {"databaseReady": True, "currentDatabase": currentDatabase}

        return cls._instance

    def get(self):
        return self.serverStatus

    def getConfig(self):
        return self.config.get_config

    def setCurrentDatabase(self, databaseName):
        self.serverStatus["currentDatabase"] = databaseName

