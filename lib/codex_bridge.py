def build_codex_request(config: dict, action: str, payload: dict) -> dict:
    codex = config.get('codex', {})
    return {
        'runtime': 'subagent',
        'agent_id': codex.get('agent_id', ''),
        'mode': codex.get('mode', 'run'),
        'model': codex.get('model', ''),
        'timeout_seconds': codex.get('timeout_seconds', 900),
        'action': action,
        'payload': payload,
    }
