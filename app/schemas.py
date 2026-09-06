from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models import OSType, AuthType, ServerStatus

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

# Server Schemas
class ServerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    hostname: str = Field(..., min_length=1, max_length=255)
    port: int = Field(22, ge=1, le=65535)
    os_type: OSType
    username: str = Field("root", min_length=1)
    auth_type: AuthType = AuthType.PASSWORD
    password: Optional[str] = None
    ssh_key: Optional[str] = None

class ServerUpdate(BaseModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    port: Optional[int] = None
    os_type: Optional[OSType] = None
    username: Optional[str] = None
    auth_type: Optional[AuthType] = None
    password: Optional[str] = None
    ssh_key: Optional[str] = None

class ServerResponse(BaseModel):
    id: int
    name: str
    hostname: str
    port: int
    os_type: OSType
    username: str
    auth_type: AuthType
    status: ServerStatus
    pending_updates_count: int
    pending_updates_list: Optional[str] = None
    last_checked: Optional[datetime] = None
    created_at: datetime
    # Note: password and ssh_key are omitted for security in general list/views, or masked

    class Config:
        from_attributes = True

# Log Schema
class LogResponse(BaseModel):
    id: int
    server_id: int
    action: str
    status: str
    output: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
