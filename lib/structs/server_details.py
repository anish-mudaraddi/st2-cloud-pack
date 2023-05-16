from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class ServerDetails:
    name: str
    image_identifier: str
    flavor_identifier: str
    network_identifiers: List[str]
    extra_params: Optional[Dict]
