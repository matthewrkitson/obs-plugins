import os
import shutil
import subprocess

from . import obs

class Backup:
    def __init__(self, backups_folder, obs_folder):
        self.backups_folder = backups_folder.rstrip("/")
        self.obs_folder = obs_folder.rstrip("/")
        self.obs_foldername = os.path.basename(self.obs_folder)

        if not os.path.isdir(self.backups_folder):
            os.makedirs(self.backups_folder)

    def backup(self, backup_name, confirm_continue=None):
        # The confirm_continue callback will be passed the backup name and
        # destination path if the destination backup already exists.
        # Return True to confirm that the overwrite should continue. 
        safe_backup_name = self._sanitise(backup_name)
        destination = os.path.join(self.backups_folder, safe_backup_name)

        if os.path.isdir(destination) and confirm_continue and not confirm_continue(backup_name, destination):
            return False

        process = subprocess.run(
            ["rsync", "-avP", self.obs_folder, destination],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)

        if process.returncode != 0:
            raise ChildProcessError(f"rsync exit code: {process.returncode}\n\n{process.stdout}\n\n{process.stderr}")

        return True

    def get_backup_DirEntries(self):
        return [ f for f in os.scandir(self.backups_folder) if f.is_dir() ]

    def restore(self, backup_name):
        # Backup name is expected to be the name of the folder only (not the full path to the backup)
        backup_folder = os.path.join(self.backups_folder, backup_name).rstrip("/")
        process = subprocess.run(
            ["rsync", "-avP", f"{backup_folder}/{self.obs_foldername}/", self.obs_folder],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)

        if process.returncode != 0:
            raise ChildProcessError(f"rsync exit code: {process.returncode}\n\n{process.stdout}\n\n{process.stderr}")
        pass

    def delete(self, backup_name):
        destination = os.path.join(self.backups_folder, backup_name)
        shutil.rmtree(destination)

    def _sanitise(self, backup_name):
        # TODO: implement some kind of sanitisation... 
        # https://github.com/matthewrkitson/obs-plugins/issues/3
        return backup_name

