// server.js - DevTaskFlow 看板后端
const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();

const WORKSPACE = process.env.DTFLOW_WORKSPACE || process.cwd();
const PORT = process.env.DTFLOW_BOARD_PORT || 8765;

function loadProjects() {
  // 优先从 PROJECTS.md 注释中的 JSON 加载（与 Python 端一致）
  const mdFile = path.join(WORKSPACE, 'PROJECTS.md');
  if (fs.existsSync(mdFile)) {
    try {
      const md = fs.readFileSync(mdFile, 'utf8');
      const marker = '<!-- DTFLOW_PROJECTS_JSON\n';
      const endMarker = '\nDTFLOW_PROJECTS_JSON_END -->';
      const start = md.indexOf(marker);
      if (start !== -1) {
        const end = md.indexOf(endMarker, start);
        if (end !== -1) {
          const jsonStr = md.slice(start + marker.length, end);
          return JSON.parse(jsonStr);
        }
      }
    } catch (e) {
      console.warn('⚠️ 解析 PROJECTS.md 失败，尝试 fallback 到 PROJECTS.json:', e.message);
    }
  }
  // fallback: 读取 PROJECTS.json
  const projFile = path.join(WORKSPACE, 'PROJECTS.json');
  if (!fs.existsSync(projFile)) return [];
  return JSON.parse(fs.readFileSync(projFile, 'utf8'));
}

function readJSON(filePath) {
  if (!fs.existsSync(filePath)) return null;
  try { return JSON.parse(fs.readFileSync(filePath, 'utf8')); } catch { return null; }
}

function readFirstN(filePath, n) {
  if (!fs.existsSync(filePath)) return '';
  const data = fs.readFileSync(filePath, 'utf8');
  return data.slice(0, n);
}

// 脱敏：过滤 state 和 config 中的敏感字段
function sanitizeState(state) {
  if (!state || typeof state !== 'object') return state;
  const { publish, ...rest } = state;
  // 移除可能包含 token/路径信息的字段
  delete rest.last_error_detail;
  return rest;
}

function sanitizeDeploy(deploy) {
  if (!deploy || typeof deploy !== 'object') return {};
  // 只返回非敏感的部署状态信息，不暴露 host/user/path/credentials
  return {
    adapter: deploy.adapter || '',
    has_build_command: !!deploy.build_command,
    has_deploy_command: !!deploy.deploy_command,
    has_restart_command: !!deploy.restart_command,
  };
}

app.get('/api/projects', (req, res) => {
  const projects = loadProjects();
  const result = projects.map(p => {
    const projPath = p.path;
    const configPath = path.join(projPath, '.dtflow', 'config.json');
    const config = readJSON(configPath) || {};
    const versionDir = path.join(projPath, 'versions', p.current_version || '');
    const state = readJSON(path.join(versionDir, '.state.json')) || {};
    const reqPath = path.join(versionDir, 'docs', 'REQUIREMENTS.md');
    const reqSummary = readFirstN(reqPath, 200);
    return {
      name: p.name,
      status: p.status,
      current_version: p.current_version,
      updated_at: p.updated_at,
      note: p.note,
      version_state: sanitizeState(state),
      deploy: sanitizeDeploy(config.deploy),
      requirements_summary: reqSummary,
    };
  });
  res.json(result);
});

app.get('/api/projects/:name', (req, res) => {
  const name = req.params.name;
  const projects = loadProjects();
  const p = projects.find(pr => pr.name === name);
  if (!p) return res.status(404).json({error: '项目未找到'});
  const projPath = p.path;
  const configPath = path.join(projPath, '.dtflow', 'config.json');
  const config = readJSON(configPath) || {};
  const versionDir = path.join(projPath, 'versions', p.current_version || '');
  const state = readJSON(path.join(versionDir, '.state.json')) || {};
  const tasks = state.tasks || [];
  const lastError = state.last_error || null;
  const reqPath = path.join(versionDir, 'docs', 'REQUIREMENTS.md');
  const reqFull = fs.existsSync(reqPath) ? fs.readFileSync(reqPath, 'utf8') : '';
  res.json({
    name: p.name,
    status: p.status,
    current_version: p.current_version,
    updated_at: p.updated_at,
    note: p.note,
    deploy: sanitizeDeploy(config.deploy),
    version_state: sanitizeState(state),
    tasks,
    last_error: lastError,
    requirements: reqFull,
  });
});

app.get('/api/health', (req, res) => {
  res.json({status: 'ok', time: new Date().toISOString()});
});

app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, HOST, () => {
  console.log(`DevTaskFlow board listening on ${HOST}:${PORT}`);
});
