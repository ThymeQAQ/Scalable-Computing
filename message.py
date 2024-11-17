from enum import Enum
from dataclasses import dataclass
import json

class MessageType(Enum):
    BROADCAST = "broadcast"
    HANDOVER = "handover"

@dataclass
class Message:
    sender_id: str
    message_type: MessageType
    content: dict
    target_node: str = None
    
    def to_json(self):
        return json.dumps({
            'sender_id': self.sender_id,
            'message_type': self.message_type.value,
            'content': self.content,
            'target_node': self.target_node
        })