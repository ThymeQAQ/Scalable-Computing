import json
import time
import base64
import os
from enum import Enum

class MessageType(Enum):
    DIRECT = "direct"
    BROADCAST = "broadcast"
    IMAGE = "image"

class Message:
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB limit for images
    
    def __init__(self, sender_id, message_type, content, target_node=None, file_info=None):
        self.sender_id = sender_id
        if isinstance(message_type, str):
            message_type = MessageType(message_type)
        self.message_type = message_type
        self.content = content
        self.target_node = target_node
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.file_info = file_info

    @classmethod
    def create_image_message(cls, sender_id, image_path, target_node=None):
        # Check if file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        # Check file size
        file_size = os.path.getsize(image_path)
        if file_size > cls.MAX_IMAGE_SIZE:
            raise ValueError(f"Image size exceeds maximum limit of {cls.MAX_IMAGE_SIZE/1024/1024}MB")
            
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
            
        file_info = {
            'filename': os.path.basename(image_path),
            'size': file_size,
            'format': os.path.splitext(image_path)[1][1:].lower()
        }
            
        return cls(
            sender_id=sender_id,
            message_type=MessageType.IMAGE,
            content=image_data,
            target_node=target_node,
            file_info=file_info
        )

    def to_json(self):
        return json.dumps({
            "sender_id": self.sender_id,
            "message_type": self.message_type.value,
            "content": self.content,
            "target_node": self.target_node,
            "timestamp": self.timestamp,
            "file_info": self.file_info
        })

    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        return Message(
            sender_id=data["sender_id"],
            message_type=MessageType(data["message_type"]),
            content=data["content"],
            target_node=data.get("target_node"),
            file_info=data.get("file_info")
        )