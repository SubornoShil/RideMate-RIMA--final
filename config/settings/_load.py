"""Copy the upper-case names from base into a settings module's namespace."""
from . import base


def load_base(namespace: dict) -> None:
    namespace.update({key: value for key, value in vars(base).items() if key.isupper()})
