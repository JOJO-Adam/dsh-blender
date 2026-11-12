# dsh-blender · JOJO&Adam

A production pack that lets a DeepSeek Harness agent actually drive Blender: headless `bpy` scripts, renders and glTF export, plus modeling technique, 5.x pitfalls and a procedural-asset pipeline.

This is not “how to click around in Blender” — it is how to make the agent build a scene, render it and export a game-ready asset.

## Install

```bash
dsh plugin --profile web add @jojonadam/dsh-blender
dsh plugin --profile desktop add @jojonadam/dsh-blender
```

Requires Blender 5.2 LTS installed locally (`BLENDER_BIN` overrides the macOS default path). Python client has zero third-party dependencies.

## What's inside (8 skills)

| Skill | Purpose |
|---|---|
| `blender-studio` | Entry point: doctor, headless run, render, export (with client + example) |
| `blender-env` | Can't find Blender, version, METAL, black frames, permissions, bpy errors |
| `blender-sop` | 5.2 baseline, Cycles/EEVEE choice, CC0 red line, export discipline, delivery templates |
| `blender-modeling-cookbook` | Parametric bpy construction, BMesh, modifiers, topology, UV, selective Bevel |
| `blender-5x-pitfalls` | API changes and known bugs in 5.x |
| `blender-asset-pipeline` | Procedural assets, batching, LOD, glTF, continuous-mesh anti-pattern |
| `blender-mcp-bridge` | Drive a live Blender via MCP |
| `blender-triage` | Symptom-first troubleshooting, plus an honest “what this can't do” list |

Also ships six delivery/checklist templates and a cross-table consistency checker under `skills/blender-sop/`.

## Boundaries

- Headless suits deterministic work (modeling, materials, render, export, batch). Sculpting, manual rigging and art-direction tweaks need MCP or a human.
- Does not install Blender or download assets (CC0 rules in the SOP).
- Never claims render results it did not produce; no cloud calls.

## Verify

```bash
node test/provider.test.mjs
python3 skills/blender-studio/scripts/blender_client.py doctor
```

## License

MIT · JOJO & Adam · <https://jojo-adam.com>
