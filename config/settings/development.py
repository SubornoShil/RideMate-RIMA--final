from config.env import env, env_bool, env_list

from ._load import load_base

load_base(globals())

DEBUG = env_bool("DEBUG", True)
SECRET_KEY = env("SECRET_KEY", "dev-only-insecure-key-never-use-in-production")
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")
