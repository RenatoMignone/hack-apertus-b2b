# Local developer services. PostgreSQL/MinIO remain on Eric's host via your tunnel.
.DEFAULT_GOAL := help
ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PYTHON ?= $(ROOT)/.venv/bin/python
RUNTIME ?= $(ROOT)/.venv/bin/navigator-runtime
NPM ?= npm
ENV_FILE ?= $(ROOT)/src/backend/deploy/.env
STATE_DIR ?= $(ROOT)/.local/dev-services

.PHONY: help docker server frontend worker all destroy
help:
	@printf '%s\n' \
	  'make docker    Start local SearXNG Docker service and follow its logs.' \
	  'make server    Start API on http://127.0.0.1:8000 and follow logs.' \
	  'make frontend  Start HTTP frontend on http://127.0.0.1:5173 and follow logs.' \
	  'make worker    Start the LangGraph worker and follow logs.' \
	  'make all       Start all four in background; write logs under .local/dev-services/.' \
	  'make destroy   Stop Make-managed processes and local search containers; keep data.' \
	  'make help      Show this help.' \
	  '' \
	  'Prerequisites: backend .venv, frontend npm ci, private deploy/.env, Docker,' \
	  'and the existing SSH tunnel to Eric. No migrations or dependency installs run.' \
	  'Ctrl+C stops an individually followed API/frontend/worker; Docker keeps running.' \
	  'To view background logs, use make server / frontend / worker / docker.' \
	  'ENV_FILE=/path/to/private.env overrides the backend/search configuration.' \
	  'destroy leaves SSH, shared infrastructure and manually started processes alone.'

docker server frontend worker all destroy:
	@DEV_ROOT="$(ROOT)" DEV_RUNTIME="$(RUNTIME)" DEV_NPM="$(NPM)" \
	  DEV_ENV_FILE="$(ENV_FILE)" DEV_STATE_DIR="$(STATE_DIR)" \
	  "$(PYTHON)" -u -c "$$NAVIGATOR_DEV_MANAGER" "$@"

# Embedded here so the project has one Makefile and no extra launcher scripts.
# Process groups + creation stamps prevent stopping a reused or unrelated PID.
define NAVIGATOR_DEV_MANAGER
import fcntl, json, os, signal, socket, subprocess, sys, time
from pathlib import Path

root = Path(os.environ['DEV_ROOT'])
state = Path(os.environ['DEV_STATE_DIR']).resolve()
env_file = Path(os.environ['DEV_ENV_FILE']).resolve()
state.mkdir(parents=True, exist_ok=True, mode=0o700)
os.chmod(state, 0o700)
action = sys.argv[1]
runtime = os.environ['DEV_RUNTIME']
commands = {
    'server': [runtime, '--env-file', str(env_file), 'serve', '--host', '127.0.0.1', '--port', '8000'],
    'worker': [runtime, '--env-file', str(env_file), 'worker'],
    'frontend': [os.environ['DEV_NPM'], 'run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173', '--strictPort'],
}
compose = ['docker', 'compose', '--project-name', 'navigator-search', '--env-file', str(env_file),
           '-f', str(root / 'src/backend/deploy/search.compose.yaml')]
children = {}

def stamp(pid):
    try:
        if os.getpgid(pid) != pid:
            return None
        proc = Path('/proc') / str(pid) / 'stat'
        if proc.exists():
            fields = proc.read_text().rsplit(')', 1)[1].split()
            return None if fields[0] == 'Z' else fields[19]
        return subprocess.check_output(['ps', '-p', str(pid), '-o', 'lstart='], text=True).strip() or None
    except (OSError, subprocess.SubprocessError):
        return None

def tracked(name):
    try:
        row = json.loads((state / (name + '.pid')).read_text())
        child = children.get(name)
        if child and child.poll() is not None:
            return None
        return row if stamp(row['pid']) == row['stamp'] else None
    except (OSError, ValueError, KeyError):
        return None

def stop(name):
    row = tracked(name)
    if row:
        pid = row['pid']
        for sig in (signal.SIGTERM, signal.SIGCONT):
            try:
                os.killpg(pid, sig)
            except ProcessLookupError:
                pass
        until = time.monotonic() + 8
        while tracked(name) and time.monotonic() < until:
            time.sleep(.1)
        if tracked(name):
            os.killpg(pid, signal.SIGKILL)
        child = children.pop(name, None)
        if child:
            child.wait(timeout=5)
        print(name + ': stopped')
    (state / (name + '.pid')).unlink(missing_ok=True)

def start(name):
    existing = tracked(name)
    if existing:
        status = subprocess.check_output(['ps', '-p', str(existing['pid']), '-o', 'stat='], text=True).strip()
        if status.startswith('T'):
            raise RuntimeError(name + ' is suspended; run make destroy before restarting (use Ctrl+C, not Ctrl+Z)')
        print(name + ': already running')
        return False
    if not env_file.is_file() and name != 'frontend':
        raise RuntimeError('Missing private ENV_FILE: ' + str(env_file))
    if name == 'frontend' and not (root / 'src/frontend/node_modules/.bin/vite').exists():
        raise RuntimeError('Run npm ci in src/frontend first')
    port = {'server': 8000, 'frontend': 5173}.get(name)
    if port:
        with socket.socket() as sock:
            if sock.connect_ex(('127.0.0.1', port)) == 0:
                raise RuntimeError(str(port) + ' is already in use; stop the manually started service with Ctrl+C')
    log = state / (name + '.log')
    with log.open('ab') as output:
        os.chmod(log, 0o600)
        output.write( ('\n--- starting ' + name + ' ---\n').encode()); output.flush()
        environment = dict(os.environ)
        environment['PYTHONUNBUFFERED'] = '1'
        if name == 'frontend':
            environment['VITE_API_MODE'] = 'http'
            environment['VITE_API_BASE_URL'] = ''
        child = subprocess.Popen(commands[name], cwd=root / 'src/frontend' if name == 'frontend' else root,
            env=environment, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    children[name] = child
    row = {'pid': child.pid, 'stamp': stamp(child.pid)}
    pidfile = state / (name + '.pid')
    pidfile.write_text(json.dumps(row)); os.chmod(pidfile, 0o600)
    if not row['stamp']:
        raise RuntimeError(name + ' exited immediately; see ' + str(log))
    until = time.monotonic() + (20 if port else 1)
    while time.monotonic() < until:
        if child.poll() is not None:
            raise RuntimeError(name + ' exited; see ' + str(log))
        if port:
            with socket.socket() as sock:
                if sock.connect_ex(('127.0.0.1', port)) == 0:
                    break
        time.sleep(.1)
    else:
        if port:
            raise RuntimeError(name + ' did not open its port; see ' + str(log))
    print(name + ': started; log ' + str(log))
    return True

def docker_up():
    if not env_file.is_file():
        raise RuntimeError('Missing private ENV_FILE: ' + str(env_file))
    log = state / 'docker.log'
    with log.open('ab') as output:
        os.chmod(log, 0o600)
        subprocess.run(compose + ['up', '-d'], cwd=root, stdout=output, stderr=subprocess.STDOUT, check=True)
    print('docker: SearXNG started (shared database/storage and SSH are unchanged)')

def follow(name):
    try:
        with (state / (name + '.log')).open() as log:
            # Show this session's output without replaying an entire old log.
            for line in log.read().splitlines()[-80:]:
                print(line)
            while tracked(name):
                line = log.readline()
                if line:
                    print(line, end='')
                else:
                    time.sleep(.15)
        child = children.get(name)
        if child and child.poll():
            raise RuntimeError(name + ' exited; inspect its log')
    except KeyboardInterrupt:
        pass
    finally:
        with (state / '.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            stop(name)

try:
    with (state / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if action == 'destroy':
            for name in ('frontend', 'worker', 'server'):
                stop(name)
            subprocess.run(compose + ['down'], cwd=root, check=True)
            print('Project services stopped. Logs/data and SSH tunnel retained.')
        elif action == 'all':
            if not Path(runtime).is_file() or not env_file.is_file():
                raise RuntimeError('Prepare the backend .venv and private ENV_FILE first')
            if not (root / 'src/frontend/node_modules/.bin/vite').exists():
                raise RuntimeError('Run npm ci in src/frontend first')
            docker_up()
            started = []
            try:
                for name in ('server', 'worker', 'frontend'):
                    if start(name):
                        started.append(name)
            except BaseException:
                failed_name = name
                for name in reversed(started):
                    stop(name)
                # Also reap a child that failed its startup/port check.
                if failed_name not in started and failed_name in children:
                    stop(failed_name)
                raise
            print('Frontend: http://127.0.0.1:5173 | API: http://127.0.0.1:8000')
            print('Background processes started; this does not certify DB/provider readiness.')
        elif action == 'docker':
            docker_up()
        else:
            try:
                start(action)
            except BaseException:
                if action in children:
                    stop(action)
                raise
    if action in commands:
        follow(action)
    elif action == 'docker':
        child = subprocess.Popen(compose + ['logs', '-f', '--tail=80'], cwd=root)
        try:
            child.wait()
        except KeyboardInterrupt:
            child.terminate(); child.wait()
except (OSError, RuntimeError, subprocess.SubprocessError) as error:
    print('Error: ' + str(error), file=sys.stderr)
    sys.exit(1)
except KeyboardInterrupt:
    sys.exit(130)
endef
export NAVIGATOR_DEV_MANAGER
