import json
from typing import Any


class ResultValidationError(Exception):
    pass


ANALYZE_REQUIRED_KEYS = {
    'status', 'action', 'result_format', 'summary', 'tasks'
}

WRITE_REQUIRED_KEYS = {
    'status', 'action', 'result_format', 'summary', 'file_operations'
}

REVIEW_REQUIRED_KEYS = {
    'status', 'action', 'result_format', 'summary', 'passed', 'score', 'issues'
}

FIX_REQUIRED_KEYS = {
    'status', 'action', 'result_format', 'summary', 'file_operations'
}


ALLOWED_ACTIONS = {'analyze', 'write', 'review', 'fix'}
ALLOWED_STATUS = {'success', 'error', 'not_implemented'}
ALLOWED_FILE_OPERATIONS = {'create', 'overwrite', 'append'}


def load_json_text(raw_text: str) -> dict[str, Any]:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ResultValidationError(f'结构化结果不是合法 JSON: {e}')



def _require_keys(data: dict[str, Any], keys: set[str]):
    missing = [key for key in keys if key not in data]
    if missing:
        raise ResultValidationError(f'结构化结果缺少必填字段: {", ".join(missing)}')



def _validate_common(data: dict[str, Any], expected_action: str):
    action = data.get('action')
    status = data.get('status')
    if action not in ALLOWED_ACTIONS:
        raise ResultValidationError(f'action 非法: {action}')
    if action != expected_action:
        raise ResultValidationError(f'action 不匹配，期望 {expected_action}，实际 {action}')
    if status not in ALLOWED_STATUS:
        raise ResultValidationError(f'status 非法: {status}')
    if not isinstance(data.get('summary', ''), str):
        raise ResultValidationError('summary 必须是字符串')



def validate_analyze_result(data: dict[str, Any]) -> dict[str, Any]:
    data = copy.deepcopy(data)
    _require_keys(data, ANALYZE_REQUIRED_KEYS)
    _validate_common(data, 'analyze')
    tasks = data.get('tasks')
    if not isinstance(tasks, list) or not tasks:
        raise ResultValidationError('tasks 必须是非空数组')
    for idx, task in enumerate(tasks, start=1):
        if not isinstance(task, dict):
            raise ResultValidationError(f'tasks[{idx}] 必须是对象')
        for key in ['id', 'name', 'priority']:
            if not task.get(key):
                raise ResultValidationError(f'tasks[{idx}] 缺少字段: {key}')
        task.setdefault('dependencies', [])
        task.setdefault('output_files', [])
        task.setdefault('status', 'pending')
    data.setdefault('warnings', [])
    data.setdefault('errors', [])
    return data



def _validate_file_operations(data: dict[str, Any]):
    ops = data.get('file_operations')
    if not isinstance(ops, list) or not ops:
        raise ResultValidationError('file_operations 必须是非空数组')
    for idx, op in enumerate(ops, start=1):
        if not isinstance(op, dict):
            raise ResultValidationError(f'file_operations[{idx}] 必须是对象')
        path = op.get('path', '')
        operation = op.get('operation', '')
        content = op.get('content', '')
        if not path or not isinstance(path, str):
            raise ResultValidationError(f'file_operations[{idx}] path 非法')
        if operation not in ALLOWED_FILE_OPERATIONS:
            raise ResultValidationError(f'file_operations[{idx}] operation 非法: {operation}')
        if not isinstance(content, str) or not content.strip():
            raise ResultValidationError(f'file_operations[{idx}] content 不能为空')
        op.setdefault('description', '')



def validate_write_result(data: dict[str, Any]) -> dict[str, Any]:
    _require_keys(data, WRITE_REQUIRED_KEYS)
    _validate_common(data, 'write')
    _validate_file_operations(data)
    data.setdefault('warnings', [])
    data.setdefault('errors', [])
    return data



def validate_fix_result(data: dict[str, Any]) -> dict[str, Any]:
    _require_keys(data, FIX_REQUIRED_KEYS)
    _validate_common(data, 'fix')
    _validate_file_operations(data)
    data.setdefault('warnings', [])
    data.setdefault('errors', [])
    return data



def validate_review_result(data: dict[str, Any]) -> dict[str, Any]:
    _require_keys(data, REVIEW_REQUIRED_KEYS)
    _validate_common(data, 'review')
    if not isinstance(data.get('passed'), bool):
        raise ResultValidationError('passed 必须是布尔值')
    score = data.get('score')
    if not isinstance(score, (int, float)):
        raise ResultValidationError('score 必须是数字')
    issues = data.get('issues')
    if not isinstance(issues, list):
        raise ResultValidationError('issues 必须是数组')
    data.setdefault('warnings', [])
    data.setdefault('errors', [])
    return data
