import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class OSType(str, enum.Enum):
    DEBIAN = "debian"
    ROCKY = "rocky"
    ALPINE = "alpine"

class AuthType(str, enum.Enum):
    PASSWORD = "password"
    KEY = "key"

class ServerStatus(str, enum.Enum):
    OK = "ok"
    UPDATES_AVAILABLE = "updates_available"
    CHECKING = "checking"
    UPDATING = "updating"
    ERROR = "error"
    UNREACHABLE = "unreachable"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    hostname = Column(String(255), nullable=False)
    port = Column(Integer, default=22)
    os_type = Column(SQLEnum(OSType), nullable=False, default=OSType.DEBIAN)
    
    username = Column(String(100), nullable=False, default="root")
    auth_type = Column(SQLEnum(AuthType), nullable=False, default=AuthType.PASSWORD)
    password = Column(Text, nullable=True)      # Stored host credentials (encrypted/plain)
    ssh_key = Column(Text, nullable=True)       # Stored host private key
    
    status = Column(SQLEnum(ServerStatus), default=ServerStatus.OK)
    pending_updates_count = Column(Integer, default=0)
    pending_updates_list = Column(Text, nullable=True) # JSON / newline separated list of updates
    last_checked = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    logs = relationship("UpdateLog", back_populates="server", cascade="all, delete-orphan")

class UpdateLog(Base):
    __tablename__ = "update_logs"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False) # 'check' or 'upgrade'
    status = Column(String(20), nullable=False) # 'success', 'failed', 'running'
    output = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    server = relationship("Server", back_populates="logs")
