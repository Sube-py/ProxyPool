from pathlib import Path
from environs import Env
from hydra.compose import compose
from hydra.initialize import initialize
from hydra.core.global_hydra import GlobalHydra

env = Env()
env.read_env()

ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT_DIR / env.str('LOG_DIR', 'logs')

DEV_MODE, TEST_MODE, PROD_MODE = 'dev', 'test', 'prod'
app_env: str = env.str('APP_ENV', DEV_MODE).lower()

GlobalHydra.instance().clear()
initialize(config_path='.', version_base=None)

config = compose(config_name=f'config-{app_env}')
