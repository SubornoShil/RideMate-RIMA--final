
from . import base
def load_base(namespace: dict) -> None:
    namespace.update({key: value for key, value in vars(base).items() if key.isupper()})
