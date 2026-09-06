import io
import paramiko
from app.models import Server, AuthType

class SSHManager:
    @staticmethod
    def get_ssh_client(server: Server, timeout: int = 10) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        kwargs = {
            "hostname": server.hostname,
            "port": server.port or 22,
            "username": server.username or "root",
            "timeout": timeout,
            "banner_timeout": timeout,
            "auth_timeout": timeout,
        }

        if server.auth_type == AuthType.PASSWORD:
            kwargs["password"] = server.password
        elif server.auth_type == AuthType.KEY:
            if not server.ssh_key:
                raise ValueError("SSH Key is missing")
            key_file_obj = io.StringIO(server.ssh_key.strip())
            # Try RSA, Ed25519, ECDSA, DSA
            pkey = None
            for key_class in [paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey, paramiko.DSSKey]:
                try:
                    key_file_obj.seek(0)
                    pkey = key_class.from_private_key(key_file_obj, password=server.password if server.password else None)
                    break
                except Exception:
                    continue
            if pkey is None:
                raise ValueError("Could not parse SSH private key format")
            kwargs["pkey"] = pkey

        client.connect(**kwargs)
        return client

    @classmethod
    def test_connection(cls, server: Server) -> tuple[bool, str]:
        try:
            client = cls.get_ssh_client(server, timeout=8)
            stdin, stdout, stderr = client.exec_command("echo connection_successful", timeout=5)
            output = stdout.read().decode('utf-8').strip()
            client.close()
            if output == "connection_successful":
                return True, "SSH Verfindung erfolgreich hergestellt!"
            return False, f"Unerwartete Antwort: {output}"
        except Exception as e:
            return False, f"SSH Fehler: {str(e)}"

    @classmethod
    def execute_command(cls, server: Server, command: str, timeout: int = 300) -> tuple[int, str, str]:
        """
        Executes command on host and returns (exit_code, stdout, stderr).
        """
        client = cls.get_ssh_client(server, timeout=15)
        try:
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            out_str = stdout.read().decode('utf-8', errors='replace')
            err_str = stderr.read().decode('utf-8', errors='replace')
            return exit_code, out_str, err_str
        finally:
            client.close()
