"""バックアップ・復元モジュール"""
import shutil
import json
from datetime import datetime
from pathlib import Path
from config.settings import DB_PATH, BACKUP_DIR

META_FILE = BACKUP_DIR / "backup_meta.json"


def _load_meta() -> list[dict]:
    if META_FILE.exists():
        try:
            return json.loads(META_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_meta(meta: list[dict]) -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def create_backup(description: str = "") -> str:
    """現在のDBをバックアップし、ファイル名を返す"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{ts}.db"
    dest = BACKUP_DIR / filename
    shutil.copy2(str(DB_PATH), str(dest))

    meta = _load_meta()
    meta.insert(0, {
        "filename": filename,
        "created_at": datetime.now().isoformat(),
        "description": description,
        "size_kb": round(dest.stat().st_size / 1024, 1),
    })
    # 最大20件まで保持
    meta = meta[:20]
    _save_meta(meta)
    return filename


def list_backups() -> list[dict]:
    """バックアップ一覧を返す（新しい順）"""
    meta = _load_meta()
    # ファイルが実際に存在するものだけ返す
    result = []
    for m in meta:
        fp = BACKUP_DIR / m["filename"]
        if fp.exists():
            result.append(m)
    return result


def restore_backup(filename: str) -> bool:
    """指定バックアップを復元する"""
    src = BACKUP_DIR / filename
    if not src.exists():
        return False
    # 現在のDBを自動バックアップ
    if DB_PATH.exists():
        create_backup("復元前自動バックアップ")
    shutil.copy2(str(src), str(DB_PATH))
    return True


def delete_backup(filename: str) -> bool:
    """指定バックアップを削除する"""
    fp = BACKUP_DIR / filename
    if fp.exists():
        fp.unlink()
    meta = _load_meta()
    meta = [m for m in meta if m["filename"] != filename]
    _save_meta(meta)
    return True


def get_backup_size_total() -> float:
    """全バックアップの合計サイズ（MB）"""
    total = sum(f.stat().st_size for f in BACKUP_DIR.glob("*.db") if f.exists())
    return round(total / (1024 * 1024), 2)
