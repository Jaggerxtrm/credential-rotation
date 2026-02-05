
import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

QWEN_HOME = Path.home() / ".qwen"
ACCOUNTS_DIR = QWEN_HOME / "accounts"
PROFILES_ROOT = Path.home() / ".qwen_profiles"
BACKUP_DIR = Path.home() / ".qwen_backup_migration"

def migrate():
    print(f"--- Qwen Profile Migration ---")
    
    # 1. Backup totale
    if QWEN_HOME.exists():
        if BACKUP_DIR.exists():
            shutil.rmtree(BACKUP_DIR)
        shutil.copytree(QWEN_HOME, BACKUP_DIR, symlinks=True)
        print(f"✅ Backup created at {BACKUP_DIR}")
    else:
        print("❌ No .qwen directory found. Nothing to migrate.")
        return

    # 2. Setup nuova root profili
    PROFILES_ROOT.mkdir(exist_ok=True)
    
    # 3. Scopriamo gli account esistenti
    creds_files = list(ACCOUNTS_DIR.glob("oauth_creds_*.json"))
    print(f"Found {len(creds_files)} credential files to migrate.")

    for f in creds_files:
        try:
            # Estrai ID: oauth_creds_1.json -> 1
            idx = f.stem.split("_")[-1]
            profile_dir = PROFILES_ROOT / idx
            profile_dir.mkdir(exist_ok=True)
            
            # Copia le credenziali specifiche
            shutil.copy2(f, profile_dir / "oauth_creds.json")
            
            # Copia i file comuni di base (configurazione)
            # Prendiamo settings.json e altri file utili dalla root attuale
            for common in ["settings.json", "installation_id", "settings.json.orig"]:
                src = QWEN_HOME / common
                if src.exists():
                    shutil.copy2(src, profile_dir / common)
            
            # Cancelliamo installation_id per forzare rigenerazione univoca
            (profile_dir / "installation_id").unlink(missing_ok=True)
            
            print(f"✅ Migrated account {idx} to {profile_dir}")
            
        except Exception as e:
            print(f"❌ Failed to migrate {f}: {e}")

    print("\nMigration preparation complete.")
    print("Run the updated manager to activate the new profile system.")