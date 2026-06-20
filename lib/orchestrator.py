class OrchestratorError(Exception):
    pass


def get_orchestrator(config: dict):
    adapters = config.get('adapters', {})
    mode = adapters.get('orchestration', 'codex_managed')

    if mode in {'codex_managed', 'codex', 'codex_skill', 'none', '', None}:
        raise OrchestratorError(
            'Codex-managed mode does not call an external model. '
            'Use the current Codex session to analyze, implement, review, and update DevTaskFlow state.'
        )

    raise OrchestratorError(
        f'不支持的 orchestration 模式: {mode}。Codex版只支持 codex_managed。'
    )
