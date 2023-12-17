import yaml

class Config:
    _instance = None

    @staticmethod
    def get_instance():
        if Config._instance is None:
            Config()
        return Config._instance

    def __init__(self):
        if Config._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Config._instance = self
            self._load_secrets()
            self._load_config()

    def _load_secrets(self):
        try:
            print("Loading secrets...")
            with open('secrets.yml', 'r') as file:
                self.secrets = yaml.safe_load(file)
        except Exception as e:
            print(f"No secrets.yml file found: {e}")
            self.secrets = {}
    
    def _load_config(self):
        try:
            print("Loading config...")
            with open('config.yml', 'r') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.config = {}

    @property
    def get_secrets(self):
        return self.secrets
    
    @property
    def get_config(self):
        return self.config
