from adapters.base import BaseAdapter
from adapters.stdout import StdoutAdapter

def _get_adapter_types():
    types = {'stdout': StdoutAdapter}
    try:
        from adapters.http import HttpAdapter
        types['http'] = HttpAdapter
    except ImportError:
        pass
    try:
        from adapters.mongodb import MongoDBAdapter
        types['mongodb'] = MongoDBAdapter
    except ImportError:
        pass
    try:
        from adapters.rabbitmq import RabbitMQAdapter
        types['rabbitmq'] = RabbitMQAdapter
    except ImportError:
        pass
    return types

ADAPTER_TYPES = _get_adapter_types()
