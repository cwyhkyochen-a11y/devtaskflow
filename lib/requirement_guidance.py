from __future__ import annotations

import sys
from typing import List


def suggest_requirement_improvements(requirements: str) -> List[str]:
    text = (requirements or '').strip()
    suggestions: List[str] = []

    if len(text) < 40:
        suggestions.append('需求描述偏短，建议补充"要做什么、给谁用、最重要的功能"这三点。')

    if not any(keyword in text for keyword in ['用户', '客户', '员工', '团队', '谁用', '给谁用']):
        suggestions.append('可以补一句"这个东西主要给谁用"，这样后续方案会更贴近实际。')

    if not any(keyword in text for keyword in ['功能', '需要', '支持', '可以', '希望']):
        suggestions.append('可以补充 3~5 个最重要的功能点，避免后续方案过于空泛。')

    if not any(keyword in text for keyword in ['页面', '风格', '界面', '简洁', '美观', '移动端', 'PC']):
        suggestions.append('如果你对界面有偏好，可以补一句，比如"简洁、偏后台风格、适合手机使用"等。')

    if not any(keyword in text for keyword in ['第一版', 'MVP', '优先', '先做', '暂时不做']):
        suggestions.append('建议补充"这次第一版先做什么，不做什么"，这样更利于控制范围。')

    if not suggestions:
        suggestions.append('当前需求描述已经可以进入分析阶段；如果还有边界条件或禁区，也可以再补一两句。')

    return suggestions


def render_requirement_guidance(requirements: str) -> str:
    suggestions = suggest_requirement_improvements(requirements)
    lines = ['# 需求建议', '', '基于你刚刚提供的需求，建议补充或确认以下几点：', '']
    for item in suggestions:
        lines.append(f'- {item}')
    lines.extend(['', '你不需要按问卷逐项回答；如果有想补充的，直接自然语言追加即可。'])
    return '\n'.join(lines)


# ============================================================
# 引导式需求收集（agent 对话中使用）
# ============================================================

COLLECT_QUESTIONS = [
    {
        'id': 'type',
        'question': '你想做什么类型的工具？',
        'options': ['管理类（比如客户管理、订单管理）', '展示类（比如官网、作品集）', '工具类（比如计算器、转换器）', '其他'],
        'multi': False,
    },
    {
        'id': 'users',
        'question': '主要给谁用？',
        'options': ['团队内部', '客户', '个人', '公众'],
        'multi': False,
    },
    {
        'id': 'core_features',
        'question': '最核心的功能是什么？（自由描述，说 3-5 个关键功能就行）',
        'options': None,
        'multi': False,
    },
    {
        'id': 'auth',
        'question': '需要用户登录吗？',
        'options': ['需要', '不需要', '不确定'],
        'multi': False,
    },
    {
        'id': 'tech',
        'question': '技术方面有偏好吗？',
        'options': ['没有，你帮我选', 'Web 网页', '手机端', '桌面应用', '不限'],
        'multi': False,
    },
    {
        'id': 'extras',
        'question': '还有什么想补充的吗？（选填）',
        'options': None,
        'multi': False,
    },
]


def get_collect_questions() -> list[dict]:
    """返回引导式问题列表，供 agent 在对话中逐个问用户。"""
    return COLLECT_QUESTIONS


def answers_to_requirement(answers: dict) -> str:
    """把用户回答转成一段自然语言需求文本。"""
    type_map = {
        '管理类（比如客户管理、订单管理）': '管理类系统',
        '展示类（比如官网、作品集）': '展示类网站',
        '工具类（比如计算器、转换器）': '实用工具',
    }
    users_map = {
        '团队内部': '给团队内部使用',
        '客户': '给客户使用',
        '个人': '个人使用',
        '公众': '面向公众开放',
    }
    tech_map = {
        '没有，你帮我选': '',
        'Web 网页': '做成网页应用',
        '手机端': '需要适配手机端',
        '桌面应用': '桌面应用',
        '不限': '',
    }

    parts = []
    user_type = (answers.get('type', '') or '').strip()
    if user_type in type_map:
        parts.append(f'我要做一个{type_map[user_type]}')
    elif user_type:
        parts.append(f'我要做一个{user_type}')
    else:
        parts.append('我要做一个工具')

    users = (answers.get('users', '') or '').strip()
    if users in users_map:
        parts.append(users_map[users])

    features = (answers.get('core_features', '') or '').strip()
    if features:
        parts.append(f'核心功能是：{features}')

    auth = (answers.get('auth', '') or '').strip()
    if auth == '需要':
        parts.append('需要用户登录注册')
    elif auth == '不需要':
        parts.append('不需要登录')

    tech = (answers.get('tech', '') or '').strip()
    if tech in tech_map and tech_map[tech]:
        parts.append(tech_map[tech])

    extras = (answers.get('extras', '') or '').strip()
    if extras:
        parts.append(f'补充：{extras}')

    return '，'.join(parts) + '。'
