import datetime
from sqlalchemy.orm import Session
from app.models import Server, OSType, ServerStatus, UpdateLog
from app.ssh_manager import SSHManager

class UpdateManager:
    @staticmethod
    def check_updates(db: Session, server: Server) -> dict:
        server.status = ServerStatus.CHECKING
        db.commit()

        log_entry = UpdateLog(server_id=server.id, action="check", status="running", output="")
        db.add(log_entry)
        db.commit()

        try:
            updates_list = []
            output_text = ""
            
            if server.os_type == OSType.DEBIAN:
                cmd = "export DEBIAN_FRONTEND=noninteractive && apt-get update -q && apt list --upgradable 2>/dev/null"
                code, stdout, stderr = SSHManager.execute_command(server, cmd, timeout=120)
                output_text = stdout + "\n" + stderr
                
                # Parse apt output lines (skip "Listing...")
                lines = stdout.splitlines()
                for line in lines:
                    if "/" in line and "Listing..." not in line and "Auflistung..." not in line:
                        updates_list.append(line.strip())

            elif server.os_type == OSType.ROCKY:
                # dnf check-update returns exit code 100 when updates exist, 0 when no updates
                cmd = "dnf check-update --quiet || true"
                code, stdout, stderr = SSHManager.execute_command(server, cmd, timeout=120)
                output_text = stdout + "\n" + stderr

                lines = stdout.splitlines()
                for line in lines:
                    line_s = line.strip()
                    if line_s and not line_s.startswith("Obsoleting") and not line_s.startswith("Security"):
                        parts = line_s.split()
                        if len(parts) >= 2:
                            updates_list.append(line_s)

            elif server.os_type == OSType.ALPINE:
                cmd = "apk update >/dev/null && apk version -v -l '<'"
                code, stdout, stderr = SSHManager.execute_command(server, cmd, timeout=120)
                output_text = stdout + "\n" + stderr

                lines = stdout.splitlines()
                for line in lines:
                    if "<" in line:
                        updates_list.append(line.strip())

            server.pending_updates_count = len(updates_list)
            server.pending_updates_list = "\n".join(updates_list)
            server.last_checked = datetime.datetime.utcnow()
            
            if len(updates_list) > 0:
                server.status = ServerStatus.UPDATES_AVAILABLE
            else:
                server.status = ServerStatus.OK

            log_entry.status = "success"
            log_entry.output = f"Gefundene Updates: {len(updates_list)}\n\n{output_text}"
            db.commit()

            return {
                "success": True,
                "count": len(updates_list),
                "updates": updates_list,
                "output": output_text
            }

        except Exception as e:
            server.status = ServerStatus.ERROR
            log_entry.status = "failed"
            log_entry.output = f"Fehler bei Aktualisierungsprüfung: {str(e)}"
            db.commit()
            return {"success": False, "error": str(e)}

    @staticmethod
    def run_updates(db: Session, server: Server) -> dict:
        server.status = ServerStatus.UPDATING
        db.commit()

        log_entry = UpdateLog(server_id=server.id, action="upgrade", status="running", output="")
        db.add(log_entry)
        db.commit()

        try:
            if server.os_type == OSType.DEBIAN:
                cmd = "export DEBIAN_FRONTEND=noninteractive && apt-get update -y && apt-get dist-upgrade -y"
            elif server.os_type == OSType.ROCKY:
                cmd = "dnf update -y"
            elif server.os_type == OSType.ALPINE:
                cmd = "apk update && apk upgrade"
            else:
                cmd = "echo Unknown OS"

            code, stdout, stderr = SSHManager.execute_command(server, cmd, timeout=600)
            combined_output = stdout + "\n" + stderr

            if code == 0:
                server.status = ServerStatus.OK
                server.pending_updates_count = 0
                server.pending_updates_list = ""
                server.last_checked = datetime.datetime.utcnow()
                
                log_entry.status = "success"
                log_entry.output = combined_output
                db.commit()
                return {"success": True, "output": combined_output}
            else:
                server.status = ServerStatus.ERROR
                log_entry.status = "failed"
                log_entry.output = f"Befehl beendet mit Statuscode {code}:\n{combined_output}"
                db.commit()
                return {"success": False, "error": f"Exit Code {code}", "output": combined_output}

        except Exception as e:
            server.status = ServerStatus.ERROR
            log_entry.status = "failed"
            log_entry.output = f"Fehler bei Update-Durchführung: {str(e)}"
            db.commit()
            return {"success": False, "error": str(e)}
