/**
 * Provider smoke test: run without DSH by faking `ctx.skills`.
 *   node test/provider.test.mjs
 */
import assert from 'node:assert/strict'
import { existsSync } from 'node:fs'
import { join } from 'node:path'
import { apply } from '../lib/index.js'

let registered
apply({
  skills: {
    registerProvider(factory) {
      registered = factory({})
    },
  },
})

const list = await registered.list()
assert.equal(list.length, 7, `expected 7 skills, got ${list.length}`)

const studio = list.find((item) => item.name === 'blender-studio')
assert.ok(studio, 'blender-studio not discovered')
assert.equal(studio.provider, 'jojo-adam-blender')
assert.ok(studio.description.length > 20)

const loaded = await registered.get(studio)
assert.ok(loaded.content.includes('Blender × DSH'))
assert.ok(existsSync(join(studio.resourceBase.path, 'scripts/blender_client.py')))
assert.ok(existsSync(join(studio.resourceBase.path, 'examples/make_tiles.py')))

const names = list.map((item) => item.name).sort()
console.log(`ok — ${list.length} skills: ${names.join(', ')}`)
