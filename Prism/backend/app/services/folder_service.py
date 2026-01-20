
import json
import uuid
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class FolderService:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "folders.json"
        self._lock = threading.Lock()
        
        # Structure:
        # {
        #   "folders": { "id": { "name": "...", "created_at": "..." } },
        #   "file_map": { "file_id": "folder_id" }
        # }
        self.folders = {}
        self.file_map = {}
        
        self._load_db()

    def _load_db(self):
        if self.db_path.exists():
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.folders = data.get("folders", {})
                    self.file_map = data.get("file_map", {})
            except Exception as e:
                logger.error(f"Error loading folders DB: {e}")
                self.folders = {}
                self.file_map = {}
        else:
            self._save_db()

    def _save_db(self):
        try:
            with self._lock:
                with open(self.db_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "folders": self.folders,
                        "file_map": self.file_map
                    }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving folders DB: {e}")

    # --- Folder Operations ---

    def create_folder(self, name: str) -> Dict:
        folder_id = str(uuid.uuid4())
        self.folders[folder_id] = {
            "id": folder_id,
            "name": name,
            "created_at": datetime.now().isoformat()
        }
        self._save_db()
        return self.folders[folder_id]

    def rename_folder(self, folder_id: str, new_name: str) -> Optional[Dict]:
        if folder_id in self.folders:
            self.folders[folder_id]["name"] = new_name
            self._save_db()
            return self.folders[folder_id]
        return None

    def list_folders(self) -> List[Dict]:
        # Return list of folders with file counts
        result = []
        folder_counts = {}
        for folder_id in self.file_map.values():
            folder_counts[folder_id] = folder_counts.get(folder_id, 0) + 1
            
        for f_id, f_data in self.folders.items():
            result.append({
                **f_data,
                "file_count": folder_counts.get(f_id, 0)
            })
        return result

    def get_folder(self, folder_id: str) -> Optional[Dict]:
        return self.folders.get(folder_id)

    def delete_folder(self, folder_id: str):
        if folder_id in self.folders:
            del self.folders[folder_id]
            # Unassign files
            files_to_update = [fid for fid, fid_map in self.file_map.items() if fid_map == folder_id]
            for fid in files_to_update:
                del self.file_map[fid]
            self._save_db()

    # --- File Operations ---

    def assign_file(self, file_id: str, folder_id: str):
        if folder_id not in self.folders:
            raise ValueError("Folder does not exist")
        self.file_map[file_id] = folder_id
        self._save_db()

    def unassign_file(self, file_id: str):
        if file_id in self.file_map:
            del self.file_map[file_id]
            self._save_db()

    def get_folder_for_file(self, file_id: str) -> Optional[str]:
        return self.file_map.get(file_id)

    def get_files_in_folder(self, folder_id: str) -> List[str]:
        return [fid for fid, fid_map in self.file_map.items() if fid_map == folder_id]

# Singleton
folder_service = FolderService()
