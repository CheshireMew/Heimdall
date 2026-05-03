import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const script = process.argv[2]
const args = process.argv.slice(3)

if (!script) {
  console.error('Usage: node scripts/run_backend_python.mjs <script.py> [...args]')
  process.exit(2)
}

const candidates = [
  process.env.HEIMDALL_PYTHON,
  path.join(repoRoot, 'venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python'),
  path.join(repoRoot, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python'),
].filter(Boolean)

const python = candidates.find((candidate) => existsSync(candidate))

if (!python) {
  console.error(
    'Backend Python runtime not found. Set HEIMDALL_PYTHON or create venv/.venv in the repository root.',
  )
  process.exit(1)
}

const resolvedScript = path.isAbsolute(script) ? script : path.join(repoRoot, script)
const result = spawnSync(python, [resolvedScript, ...args], {
  cwd: repoRoot,
  stdio: 'inherit',
  shell: false,
})

if (result.error) {
  console.error(result.error.message)
  process.exit(1)
}

process.exit(result.status ?? 1)
