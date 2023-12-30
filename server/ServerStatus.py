from config import Config
from services import duckDbService

class ServerStatus:
    def __init__(self):
        print("Initializing server...")

        # Check if data folder existsin filesistem and create if not
        if (Config.get_instance().get_config.get("database") is not None):
            print("Checking data folder...")
            import os
            if not os.path.exists(Config.get_instance().get_config.get("database")):
                os.makedirs("data")
                print("Data folder created")

        print("Connecting to database..." + Config.get_instance().get_config.get("database"))
        duckDbService.init(Config.get_instance().get_secrets, Config.get_instance().get_config)

        self.serverStatus = {}
        self.serverStatus["databaseReady"] = True
    
    '''def _load_config(self):
        try:
            with open('config.yml', 'r') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.config = {}
            '''

    def get(self):
        return self.serverStatus