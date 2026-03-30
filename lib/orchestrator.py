class OrchestratorError(Exception):
    pass


def get_orchestrator(config: dict):
    adapters = config.get('adapters', {})
    mode = adapters.get('orchestration', 'local_llm')

    if mode in {'none', '', None}:
        mode = 'local_llm'

    if mode == 'local_llm':
        try:
            from orchestrators.local_llm import LocalLLMOrchestrator
        except ImportError as e:
            raise OrchestratorError(f'无法导入 LocalLLMOrchestrator: {e}。请检查 orchestrators/local_llm.py 是否存在。')
        return LocalLLMOrchestrator(config)
    if mode == 'openclaw_subagent':
        try:
            from orchestrators.openclaw_subagent import OpenClawSubagentOrchestrator
        except ImportError as e:
            raise OrchestratorError(f'无法导入 OpenClawSubagentOrchestrator: {e}。请检查 orchestrators/openclaw_subagent.py 是否存在。')
        return OpenClawSubagentOrchestrator(config)

    raise OrchestratorError(f'不支持的 orchestration 模式: {mode}')
