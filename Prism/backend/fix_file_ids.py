
import json
import os
from pathlib import Path
import shutil

def fix_file_ids():
    data_dir = Path("data")
    processed_dir = data_dir / "processed"
    folders_file = data_dir / "folders.json"
    
    if not folders_file.exists():
        print("folders.json not found!")
        return

    # 1. Load Folder DB
    with open(folders_file, "r", encoding="utf-8") as f:
        folder_data = json.load(f)
    
    file_map = folder_data.get("file_map", {})
    folders = folder_data.get("folders", {})
    
    print(f"Loaded {len(file_map)} file mappings.")

    # 2. Scan Processed Directory
    # We look for files with content (num_chunks > 0)
    valid_processed = {} # { original_filename_suffix: full_uuid_filename }
    
    print("\nScanning processed directory...")
    for file_path in processed_dir.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                chunks = data.get("chunks", [])
                
                if chunks:
                    # This is a valid file with content
                    # Filename format is usually: UUID_OriginalName.json
                    # We want to match this back to the OriginalName used in folders.json
                    
                    # Heuristic: The file_map keys are likely the "OriginalName" (without extension usually, or with)
                    # Let's verify what the keys look like in file_map first.
                    valid_processed[file_path.stem] = {
                        "path": file_path,
                        "chunks": len(chunks)
                    }
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    print(f"Found {len(valid_processed)} processed files with existing chunks.")

    # 3. Reconcile
    updates_made = 0
    deletions = []
    
    # Create a reverse lookup for valid processed files based on suffix (original name)
    # The file_map keys seem to be strictly filenames (sometimes without extension, sometimes with?)
    # Based on previous inspection: 
    # file_map key: "EPI Supplier Questionnaire - Wayte Travel"
    # processed file: "7ab6761f..._EPI Supplier Questionnaire - Wayte Travel.json"
    
    # Let's build a map of { clean_name: uuid_stem }
    uuid_map = {} 
    for stem in valid_processed.keys():
        # strict split might be dangerous if filename has underscores, but the UUID is standard format.
        # UUID is 36 chars + 1 underscore = 37 chars prefix
        if len(stem) > 37 and stem[8] == '-': # Basic UUID check
             original_part = stem[37:] # 36 chars uuid + 1 underscore
             uuid_map[original_part] = stem
             
             # Also try matching without extension if the key in file_map is no-extension
             # but we don't know the extension here easily without parsing original string.
             # Actually, the stem doesn't have .json, but might have .pdf embedded if the filename was "doc.pdf"
             # processed file: "..._doc.pdf.json" -> stem "..._doc.pdf"
             
    new_file_map = file_map.copy()
    
    for simple_id, folder_id in file_map.items():
        # Check if this simple_id points to an empty processed file
        simple_json_path = processed_dir / f"{simple_id}.json"
        
        # We only care if:
        # 1. The simple file exists and is empty/invalid (0 chunks)
        # 2. OR the simple file doesn't exist but we have a UUID version
        
        needs_update = False
        target_uuid_id = None
        
        # Check if we have a uuid replacement
        if simple_id in uuid_map:
            target_uuid_id = uuid_map[simple_id]
            needs_update = True
        else:
            # Try to find semi-fuzzy match? 
            # e.g. simple_id = "DocName", uuid_entry = "UUID_DocName.pdf"
            for orig_part, full_id in uuid_map.items():
                 if orig_part.startswith(simple_id): # risky?
                     pass
        
        if needs_update and target_uuid_id:
            # Check if current simple file is actually empty/useless
             is_empty = True
             if simple_json_path.exists():
                 try:
                     with open(simple_json_path, 'r', encoding='utf-8') as f:
                         d = json.load(f)
                         if d.get("chunks"):
                             is_empty = False
                 except: 
                     is_empty = True
            
             if is_empty:
                 print(f"Migrating: '{simple_id}' -> '{target_uuid_id}'")
                 new_file_map[target_uuid_id] = folder_id
                 if simple_id in new_file_map:
                     del new_file_map[simple_id]
                 
                 updates_made += 1
                 if simple_json_path.exists():
                     deletions.append(simple_json_path)

    # 4. Save Changes
    if updates_made > 0:
        print(f"\nApplying {updates_made} updates to folders.json...")
        
        folder_data["file_map"] = new_file_map
        # Backup first
        shutil.copy(folders_file, folders_file.with_suffix(".json.bak"))
        
        with open(folders_file, "w", encoding="utf-8") as f:
            json.dump(folder_data, f, indent=2)
            
        print("Updated folders.json")
        
        print(f"Deleting {len(deletions)} obsolete empty files...")
        for p in deletions:
            try:
                os.remove(p)
                print(f"Deleted: {p.name}")
            except Exception as e:
                print(f"Failed to delete {p.name}: {e}")
                
    else:
        print("\nNo updates needed. All mappings appear consistent or no matching UUID files found.")

if __name__ == "__main__":
    fix_file_ids()
