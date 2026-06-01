'use strict';
/*
 * Conquer Online — Frida agent (READ-ONLY tick proof, task #27).
 *
 * Proves a stable per-frame, game-thread tick by hooking a SYSTEM function the
 * message loop calls every frame (user32!PeekMessageW) — NOT the game's .text —
 * so there is zero game-code modification (the thing that crashed the old app).
 * Also reads the hero via the injected CONFIG offsets to cross-check pymem.
 *
 * NO writes, NO NativeFunction calls, NO game-code hooks. The risky bits
 * (calling JumpFunc etc.) are a later step. `CONFIG` is prepended by the Python
 * side (FridaSession) from core/offsets.py::to_agent_config().
 */

/* global CONFIG */
const S = CONFIG.structs;

let _mod = null;
function modBase() {
  if (_mod === null) {
    try {
      _mod = Process.getModuleByName(CONFIG.module);
    } catch (e) {
      const all = Process.enumerateModules();
      _mod = all.find((m) => m.name.toLowerCase() === CONFIG.module.toLowerCase()) || all[0];
    }
  }
  return _mod;
}
function va(addr) { return modBase().base.add(addr - CONFIG.imageBase); }
function glob(name) { return va(CONFIG.globals[name]); }

function expAddr(mod, fn) {
  try { return Process.getModuleByName(mod).getExportByName(fn); }
  catch (e) {
    try { return Module.findExportByName(mod, fn); } catch (e2) { return null; }
  }
}

function safe(fn) { try { return fn(); } catch (e) { return null; } }
function rdU32(p) { return safe(() => p.readU32()); }
function rdPtr(p) { return safe(() => p.readPointer()); }

function heroPtr() {
  const h = rdPtr(glob('heroSlot'));
  return (h && !h.isNull()) ? h : null;
}
function objCoord(obj) {
  if (!obj || obj.isNull()) return null;
  const sub = rdPtr(obj.add(S.coordSub));
  if (!sub || sub.isNull()) return null;
  const x = rdU32(sub.add(S.coordX)), y = rdU32(sub.add(S.coordY));
  if (x === null || y === null) return null;
  return [x >> S.coordShift, y >> S.coordShift];
}
function objName(obj) {
  if (!obj || obj.isNull()) return '';
  const p = rdPtr(obj.add(S.name));
  if (!p || p.isNull()) return '';
  return safe(() => p.readUtf16String()) || '';
}

// ---- per-frame tick: hook a SYSTEM function (no game-code modification) -----
let frames = 0;
const threads = {};
function hookTick(fn) {
  const a = expAddr('user32.dll', fn);
  if (!a) { send({ type: 'warn', msg: 'tick fn not found: ' + fn }); return false; }
  Interceptor.attach(a, {
    onEnter() {
      frames++;
      const t = Process.getCurrentThreadId();
      threads[t] = (threads[t] || 0) + 1;
    },
  });
  send({ type: 'info', msg: 'tick hooked: user32!' + fn + ' @ ' + a });
  return true;
}

rpc.exports = {
  ping() { return 'ok base=' + modBase().base; },
  frames() { return { count: frames, threads: threads }; },
  hero() {
    const h = heroPtr(); if (!h) return null;
    const c = objCoord(h);
    return {
      uid: rdU32(h.add(S.uid)),
      x: c ? c[0] : null, y: c ? c[1] : null,
      pk: rdU32(h.add(S.pk)),
      speed: rdU32(h.add(S.speed)),
      name: objName(h),
    };
  },
};

// Install the tick on load — PeekMessageW, falling back to PeekMessageA.
const tickOk = hookTick('PeekMessageW') || hookTick('PeekMessageA');
send({ type: 'ready', base: '' + modBase().base, tick: tickOk });
