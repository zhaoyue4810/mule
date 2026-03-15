#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_DIR="${ROOT_DIR}/server"
APP_DIR="${ROOT_DIR}/apps/xince-app"
ADMIN_DIR="${ROOT_DIR}/apps/xince-admin"
RUNTIME_DIR="${ROOT_DIR}/.runtime/dev-stack"

SERVER_PID_FILE="${RUNTIME_DIR}/server.pid"
APP_PID_FILE="${RUNTIME_DIR}/app-h5.pid"
ADMIN_PID_FILE="${RUNTIME_DIR}/admin.pid"

SERVER_LOG="${RUNTIME_DIR}/server.log"
APP_LOG="${RUNTIME_DIR}/app-h5.log"
ADMIN_LOG="${RUNTIME_DIR}/admin.log"

SERVER_PORT="8080"
APP_PORT="5173"
ADMIN_PORT="5174"

mkdir -p "${RUNTIME_DIR}"

log() {
  printf '[dev-stack] %s\n' "$*"
}

die() {
  printf '[dev-stack] ERROR: %s\n' "$*" >&2
  exit 1
}

ensure_command() {
  command -v "$1" >/dev/null 2>&1 || die "缺少命令: $1"
}

ensure_file_from_example() {
  local target="$1"
  local example="$2"
  if [[ ! -f "${target}" && -f "${example}" ]]; then
    cp "${example}" "${target}"
    log "已自动创建 $(basename "${target}")"
  fi
}

pid_is_running() {
  local pid="$1"
  kill -0 "${pid}" >/dev/null 2>&1
}

stop_process() {
  local name="$1"
  local pid_file="$2"
  if [[ ! -f "${pid_file}" ]]; then
    return
  fi

  local pid
  pid="$(cat "${pid_file}")"
  if [[ -n "${pid}" ]] && pid_is_running "${pid}"; then
    log "停止 ${name} (PID ${pid})"
    kill "${pid}" >/dev/null 2>&1 || true
    sleep 1
    if pid_is_running "${pid}"; then
      kill -9 "${pid}" >/dev/null 2>&1 || true
    fi
  fi
  rm -f "${pid_file}"
}

print_status_line() {
  local label="$1"
  local pid_file="$2"
  local url="${3:-}"

  if [[ -f "${pid_file}" ]]; then
    local pid
    pid="$(cat "${pid_file}")"
    if [[ -n "${pid}" ]] && pid_is_running "${pid}"; then
      if [[ -n "${url}" ]]; then
        printf '%-12s running  pid=%s  %s\n' "${label}" "${pid}" "${url}"
      else
        printf '%-12s running  pid=%s\n' "${label}" "${pid}"
      fi
      return
    fi
  fi
  printf '%-12s stopped\n' "${label}"
}

ensure_python_env() {
  ensure_command python3
  if [[ ! -x "${SERVER_DIR}/.venv/bin/python" ]]; then
    log "创建后端虚拟环境"
    (
      cd "${SERVER_DIR}"
      python3 -m venv .venv
      ./.venv/bin/python -m pip install -e ".[dev]"
    )
  fi
}

ensure_node_deps() {
  ensure_command npm

  if [[ ! -d "${APP_DIR}/node_modules" ]]; then
    log "安装 xince-app 依赖"
    (cd "${APP_DIR}" && npm install)
  fi

  if [[ ! -d "${ADMIN_DIR}/node_modules" ]]; then
    log "安装 xince-admin 依赖"
    (cd "${ADMIN_DIR}" && npm install)
  fi
}

prepare_envs() {
  ensure_file_from_example "${SERVER_DIR}/.env" "${SERVER_DIR}/.env.example"
  ensure_file_from_example "${APP_DIR}/.env" "${APP_DIR}/.env.example"
}

run_migrations() {
  log "执行数据库迁移"
  (
    cd "${SERVER_DIR}"
    ./.venv/bin/alembic upgrade head
  )
}

start_server() {
  if [[ -f "${SERVER_PID_FILE}" ]] && pid_is_running "$(cat "${SERVER_PID_FILE}")"; then
    log "后端已在运行"
    return
  fi

  log "启动后端 http://127.0.0.1:${SERVER_PORT}"
  (
    cd "${SERVER_DIR}"
    nohup bash -lc "source .venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port ${SERVER_PORT}" \
      >"${SERVER_LOG}" 2>&1 &
    echo $! > "${SERVER_PID_FILE}"
  )
}

start_app_h5() {
  if [[ -f "${APP_PID_FILE}" ]] && pid_is_running "$(cat "${APP_PID_FILE}")"; then
    log "用户端 H5 已在运行"
    return
  fi

  log "启动用户端 H5 http://127.0.0.1:${APP_PORT}"
  (
    cd "${APP_DIR}"
    nohup npm run dev:h5 -- --host 127.0.0.1 --port "${APP_PORT}" \
      >"${APP_LOG}" 2>&1 &
    echo $! > "${APP_PID_FILE}"
  )
}

start_admin() {
  if [[ -f "${ADMIN_PID_FILE}" ]] && pid_is_running "$(cat "${ADMIN_PID_FILE}")"; then
    log "管理后台已在运行"
    return
  fi

  log "启动管理后台 http://127.0.0.1:${ADMIN_PORT}"
  (
    cd "${ADMIN_DIR}"
    nohup npm run dev -- --host 127.0.0.1 --port "${ADMIN_PORT}" \
      >"${ADMIN_LOG}" 2>&1 &
    echo $! > "${ADMIN_PID_FILE}"
  )
}

show_status() {
  print_status_line "backend" "${SERVER_PID_FILE}" "http://127.0.0.1:${SERVER_PORT}"
  print_status_line "app-h5" "${APP_PID_FILE}" "http://127.0.0.1:${APP_PORT}"
  print_status_line "admin" "${ADMIN_PID_FILE}" "http://127.0.0.1:${ADMIN_PORT}"
  printf '\n'
  printf 'logs:\n'
  printf '  server: %s\n' "${SERVER_LOG}"
  printf '  app:    %s\n' "${APP_LOG}"
  printf '  admin:  %s\n' "${ADMIN_LOG}"
}

show_logs() {
  local target="${1:-all}"
  case "${target}" in
    server)
      tail -n 80 -f "${SERVER_LOG}"
      ;;
    app|app-h5)
      tail -n 80 -f "${APP_LOG}"
      ;;
    admin)
      tail -n 80 -f "${ADMIN_LOG}"
      ;;
    all)
      log "请分别查看单独日志:"
      printf '  %s logs server\n' "$0"
      printf '  %s logs app\n' "$0"
      printf '  %s logs admin\n' "$0"
      ;;
    *)
      die "未知日志目标: ${target}"
      ;;
  esac
}

build_mp() {
  ensure_command npm
  if [[ ! -d "${APP_DIR}/node_modules" ]]; then
    log "安装 xince-app 依赖"
    (cd "${APP_DIR}" && npm install)
  fi
  log "构建微信小程序"
  (cd "${APP_DIR}" && npm run build:mp-weixin)
  log "构建完成，请导入 ${APP_DIR}/dist/build/mp-weixin"
}

up() {
  ensure_command bash
  ensure_python_env
  ensure_node_deps
  prepare_envs
  run_migrations
  start_server
  start_app_h5
  start_admin
  sleep 2
  show_status
  printf '\n'
  printf '打开地址:\n'
  printf '  用户端 H5: http://127.0.0.1:%s\n' "${APP_PORT}"
  printf '  管理后台:  http://127.0.0.1:%s\n' "${ADMIN_PORT}"
  printf '  后端文档:  http://127.0.0.1:%s/docs\n' "${SERVER_PORT}"
  printf '\n'
  printf '管理后台默认登录:\n'
  printf '  username: admin\n'
  printf '  password: xince-admin-2026\n'
}

down() {
  stop_process "用户端 H5" "${APP_PID_FILE}"
  stop_process "管理后台" "${ADMIN_PID_FILE}"
  stop_process "后端" "${SERVER_PID_FILE}"
  log "开发栈已停止"
}

restart() {
  down
  up
}

usage() {
  cat <<EOF
用法:
  $(basename "$0") up
  $(basename "$0") down
  $(basename "$0") restart
  $(basename "$0") status
  $(basename "$0") logs [server|app|admin]
  $(basename "$0") build-mp

说明:
  up        一键准备并启动后端、用户端 H5、管理后台
  down      停止全部本地开发进程
  restart   重启全部本地开发进程
  status    查看当前运行状态
  logs      查看指定服务日志
  build-mp  构建微信小程序产物
EOF
}

main() {
  local command="${1:-up}"
  case "${command}" in
    up)
      up
      ;;
    down)
      down
      ;;
    restart)
      restart
      ;;
    status)
      show_status
      ;;
    logs)
      show_logs "${2:-all}"
      ;;
    build-mp)
      build_mp
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
