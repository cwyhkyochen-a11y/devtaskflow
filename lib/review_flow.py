from pathlib import Path

from orchestrator import get_orchestrator
from project import scan_project_files, get_current_version_dir
from state import StateManager
from contracts_review import build_review_payload
from prompt_loader import load_prompt


def parse_review_passed(review_result: str):
    return '❌ 不通过' not in review_result


def run_review(project_root: Path, config: dict):
    version_dir = get_current_version_dir(project_root, config)
    if not version_dir:
        raise RuntimeError('没有找到当前版本目录')

    state = StateManager(version_dir)
    if state.data.get('status') != 'written':
        raise RuntimeError(f"当前状态不允许 review: {state.data.get('status')}")

    task_id = state.data.get('current_task')
    tasks = state.data.get('tasks', [])
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        raise RuntimeError('找不到当前任务')

    dev_plan_file = version_dir / 'docs' / 'DEV_PLAN.md'
    if not dev_plan_file.exists():
        raise RuntimeError('找不到 DEV_PLAN.md')
    dev_plan = dev_plan_file.read_text(encoding='utf-8')

    code_files = scan_project_files(project_root, limit=20)
    code = '\n\n'.join([
        f"=== 文件: {f['path']} ===\n```\n{f['content'][:4000]}\n```" for f in code_files[:10]
    ])

    state.data['status'] = 'reviewing'
    state.data['last_action'] = 'review'
    state.data['last_error'] = None
    state.save()

    orchestrator = get_orchestrator(config)
    result = orchestrator.run('review', build_review_payload(project_root, version_dir, task, dev_plan, code))

    if result.get('status') == 'not_implemented':
        raise RuntimeError(result.get('message', 'review 编排器未实现'))

    review_text = result.get('raw_text', '') or result.get('summary', '')
    if not review_text:
        raise RuntimeError('review 未返回 raw_text')

    review_file = version_dir / 'docs' / f'REVIEW_TASK_{task_id}.md'
    review_file.write_text(review_text, encoding='utf-8')

    passed = result.get('passed') if isinstance(result.get('passed'), bool) else parse_review_passed(review_text)
    state.data['status'] = 'review_passed' if passed else 'needs_fix'
    state.data['last_orchestration'] = config.get('adapters', {}).get('orchestration', 'local_llm') or 'local_llm'
    state.data['last_result_format'] = result.get('result_format', 'unknown')
    state.data['last_summary'] = result.get('summary', '')
    state.save()

    return {
        'task_id': task['id'],
        'task_name': task['name'],
        'review_file': str(review_file),
        'passed': passed,
        'orchestration': state.data['last_orchestration'],
        'result_format': state.data['last_result_format'],
        'summary': state.data['last_summary'],
    }


def run_comprehensive_review(project_root: Path, config: dict):
    """上线前综合审查：9 维度全面检查。"""
    version_dir = get_current_version_dir(project_root, config)
    if not version_dir:
        raise RuntimeError('没有找到当前版本目录')

    state = StateManager(version_dir)

    # 加载综合审查 prompt
    prompt_text = load_prompt('comprehensive_review_system.md')

    # 收集所有源代码
    code_files = scan_project_files(project_root, limit=30)
    code_context = '\n\n'.join([
        f"=== 文件: {f['path']} ===\n```\n{f['content'][:5000]}\n```" for f in code_files[:20]
    ])

    # 加载 DEV_PLAN.md
    dev_plan_file = version_dir / 'docs' / 'DEV_PLAN.md'
    dev_plan = dev_plan_file.read_text(encoding='utf-8') if dev_plan_file.exists() else '（无开发计划）'

    # 加载 DESIGN_SYSTEM.md
    ds_file = version_dir / 'docs' / 'DESIGN_SYSTEM.md'
    ds_root = version_dir / 'DESIGN_SYSTEM.md'
    if ds_file.exists():
        design_system = ds_file.read_text(encoding='utf-8')
    elif ds_root.exists():
        design_system = ds_root.read_text(encoding='utf-8')
    else:
        design_system = '（无设计系统规范）'

    # 加载 USER_GUIDE.md
    ug_file = project_root / 'docs' / 'USER_GUIDE.md'
    user_guide = ug_file.read_text(encoding='utf-8') if ug_file.exists() else '（无使用说明书）'

    state.data['status'] = 'comprehensive_reviewing'
    state.data['last_action'] = 'comprehensive_review'
    state.data['last_error'] = None
    state.save()

    orchestrator = get_orchestrator(config)

    # 构造审查 payload
    user_content = f"""## 开发计划
{dev_plan}

## 设计系统规范
{design_system}

## 使用说明书
{user_guide}

## 项目源代码
{code_context}
"""

    result = orchestrator.run('comprehensive_review', {
        'system_prompt': prompt_text,
        'user_content': user_content,
        'project_root': str(project_root),
        'version_dir': str(version_dir),
    })

    # 如果编排器不支持 comprehensive_review，回退到通用方式
    if result.get('status') == 'not_implemented':
        # 使用 review 编排器，替换 system prompt
        result = orchestrator.run('review', {
            'system_prompt': prompt_text,
            'dev_plan': dev_plan,
            'code': code_context,
            'task_name': '上线前综合审查',
            'task_description': '从代码质量、安全性、交互友好度、需求符合度、设计一致性、字段依赖、命名规范、React 性能、Web UI 质量 9 个维度全面审查',
            'project_root': str(project_root),
            'version_dir': str(version_dir),
        })

    summary_text = result.get('raw_text', '') or result.get('summary', '')
    if not summary_text:
        raise RuntimeError('综合审查未返回结果')

    # 写入审查报告
    review_file = version_dir / 'docs' / 'COMPREHENSIVE_REVIEW.md'
    review_file.write_text(summary_text, encoding='utf-8')

    # 解析评分
    passed = result.get('passed')
    score = result.get('score')
    issues = result.get('issues', [])

    # 如果没有结构化结果，尝试从文本中提取分数
    if passed is None or score is None:
        import re
        score_match = re.search(r'(?:总分|score|评分)[：:]\s*(\d+(?:\.\d+)?)', summary_text, re.IGNORECASE)
        if score_match:
            score = float(score_match.group(1))
            passed = score >= 7
        else:
            passed = '不通过' not in summary_text and '❌' not in summary_text
            score = None  # 无法解析评分时返回 None，而非伪造默认值

    state.data['status'] = 'comprehensive_review_passed' if passed else 'comprehensive_review_failed'
    state.data['last_orchestration'] = config.get('adapters', {}).get('orchestration', 'local_llm') or 'local_llm'
    state.data['last_result_format'] = result.get('result_format', 'unknown')
    state.data['last_summary'] = summary_text[:500]
    state.save()

    return {
        'review_file': str(review_file),
        'passed': passed,
        'score': score,
        'issues': issues,
        'summary': summary_text,
        'orchestration': state.data['last_orchestration'],
        'result_format': state.data['last_result_format'],
    }
