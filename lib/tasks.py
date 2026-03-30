import re


def normalize_tasks(tasks: list[dict]):
    normalized = []
    for task in tasks:
        dependencies = task.get('dependencies') or []
        if isinstance(dependencies, str):
            dependencies = [item.strip() for item in dependencies.split(',') if item.strip() and item.strip() != '无']
        output_files = task.get('output_files') or []
        if isinstance(output_files, str):
            output_files = [item.strip() for item in output_files.split(',') if item.strip() and item.strip() != '无']
        normalized.append({
            'id': str(task.get('id', '')).strip(),
            'name': str(task.get('name', '')).strip(),
            'priority': str(task.get('priority', '')).strip(),
            'dependencies': dependencies,
            'estimate': task.get('estimate'),
            'output_files': output_files,
            'status': task.get('status', 'pending'),
        })
    return normalized


def parse_tasks_from_plan(dev_plan: str):
    tasks = []
    table_pattern = r'\|\s*(T\d+)\s*\|\s*([^|]+)\|\s*(P\d+)\s*\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|'
    for match in re.finditer(table_pattern, dev_plan):
        tasks.append({
            'id': match.group(1),
            'name': match.group(2).strip(),
            'priority': match.group(3),
            'dependencies': match.group(4).strip() if match.group(4) else None,
            'estimate': match.group(5).strip() if match.group(5) else None,
            'output_files': match.group(6).strip() if match.group(6) else None,
            'status': 'pending',
        })
    normalized = normalize_tasks(tasks)
    if not normalized:
        print('⚠️ parse_tasks_from_plan: 未解析到任何任务，请检查 plan 格式是否包含标准表格。')
    return normalized
