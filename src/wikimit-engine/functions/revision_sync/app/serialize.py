import dataclasses
import json
from typing import Any


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o: Any):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def convert_json(obj: Any) -> str:
    return json.dumps(obj, cls=EnhancedJSONEncoder, indent=4)
