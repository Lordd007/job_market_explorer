from .greenhouse import Greenhouse
from .lever import Lever

REGISTRY = {
    Greenhouse.name: Greenhouse,
    Lever.name: Lever,
}
__all__ = ["REGISTRY", "Greenhouse", "Lever"]
