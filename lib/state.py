import json
from pathlib import Path
from datetime import datetime


class StateManager:
    def __init__(self, version_dir: Path):
        self.version_dir = version_dir
        self.state_file = version_dir / '.state.json'
        self.data = self._load()

    def _load(self):
        if self.state_file.exists():
            return json.loads(self.state_file.read_text(encoding='utf-8'))
        return {}

    def init(self, version: str):
        now = datetime.now().isoformat()
        self.data = {
            'version': version,
            'status': 'initialized',
            'current_task': None,
            'architecture_confirmed': False,
            'tasks': [],
            'created_at': now,
            'updated_at': now,
            'last_error': None,
            'last_action': None,
            'last_result_format': None,
            'last_summary': '',
        }
        self.save()

    def save(self):
        import os
        self.data['updated_at'] = datetime.now().isoformat()
        tmp_file = self.state_file.with_suffix('.json.tmp')
        tmp_file.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        os.replace(str(tmp_file), str(self.state_file))

    def update_status(self, status: str):
        self.data['status'] = status
        self.save()

    def set_tasks(self, tasks: list):
        self.data['tasks'] = tasks
        self.save()

    def set_current_task(self, task_id: str | None):
        self.data['current_task'] = task_id
        self.save()

    def set_error(self, error: str | None, action: str | None = None):
        self.data['last_error'] = error
        if action is not None:
            self.data['last_action'] = action
        self.save()

    # ---- 检查点机制 ----

    def _checkpoints_dir(self) -> Path:
        """返回检查点目录，自动创建。"""
        cp_dir = self.version_dir / '.checkpoints'
        cp_dir.mkdir(parents=True, exist_ok=True)
        return cp_dir

    def checkpoint(self, label: str) -> Path:
        """
        将当前 state.data 快照保存为检查点。
        返回检查点文件路径。
        """
        cp_file = self._checkpoints_dir() / f'{label}.json'
        snapshot = {
            'label': label,
            'timestamp': datetime.now().isoformat(),
            'data': json.loads(json.dumps(self.data, ensure_ascii=False)),
        }
        cp_file.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        print(f'📸 检查点已保存：{label}')
        return cp_file

    def list_checkpoints(self) -> list[tuple[str, str]]:
        """
        返回所有检查点列表 [(label, timestamp), ...]，按时间排序。
        """
        cp_dir = self.version_dir / '.checkpoints'
        if not cp_dir.exists():
            return []
        result = []
        for cp_file in sorted(cp_dir.glob('*.json')):
            try:
                cp_data = json.loads(cp_file.read_text(encoding='utf-8'))
                label = cp_data.get('label', cp_file.stem)
                ts = cp_data.get('timestamp', '-')
                result.append((label, ts))
            except Exception:
                continue
        return result

    def restore_checkpoint(self, label: str) -> dict:
        """
        从检查点恢复状态。
        返回恢复的数据。
        """
        cp_dir = self.version_dir / '.checkpoints'
        cp_file = cp_dir / f'{label}.json'
        if not cp_file.exists():
            available = [f.stem for f in cp_dir.glob('*.json')] if cp_dir.exists() else []
            raise FileNotFoundError(
                f'检查点「{label}」不存在。'
                + (f'可用检查点：{", ".join(available)}' if available else '当前没有任何检查点。')
            )
        cp_data = json.loads(cp_file.read_text(encoding='utf-8'))
        self.data = cp_data.get('data', cp_data)
        self.save()
        print(f'✅ 已从检查点「{label}」恢复状态')
        return self.data
