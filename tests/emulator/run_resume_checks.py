"""Emulator test (Unicorn) of the resume / cover caves.  Run:  python tests/emulator/run_resume_checks.py

Teste em emulador (Unicorn) das cavernas de retomar jogo / capas.  Needs: pip install unicorn
"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from r36skit.patches import resume_covers as R
from unicorn import *
from unicorn.mips_const import *

out, dbase, blob = R.build(no_cover_stem='_sem_capa')
SLOTS = {0x52ea30: 0x55000010, 0x52ec68: 0x55000020, 0x52ea38: 0x55000030, 0x52ea58: 0x55000040,
         0x52ea28: 0x55000050, 0x52f42c: 0x55000060, 0x52eb0c: 0x55000070}
NAMES = {0x55000010: 'fopen', 0x55000020: 'fread', 0x55000030: 'fclose', 0x55000040: 'strcpy',
         0x55000050: 'sprintf', 0x55000060: 'system', 0x55000070: 'access'}

def mk():
    mu = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 + UC_MODE_LITTLE_ENDIAN)
    mu.mem_map(0x40a000, 0x2000)
    for n, (b0, b) in out.items():
        mu.mem_write(b0, b)
    mu.mem_write(dbase, blob)
    mu.mem_map(0x414000, 0x2000)
    mu.mem_map(0x42e000, 0x2000)
    mu.mem_map(0x52e000, 0x2000)
    mu.mem_map(0x530000, 0x1000)
    mu.mem_map(0x55000000, 0x1000)
    mu.mem_map(0x60000000, 0x100000)
    for s, t in SLOTS.items():
        mu.mem_write(s, struct.pack('<I', t))
        mu.mem_write(t, bytes.fromhex('0800e00300000000'))
    return mu

def rd(mu, a):
    return struct.unpack('<I', bytes(mu.mem_read(a, 4)))[0]

def cstr(mu, a):
    b = b''
    while True:
        c = bytes(mu.mem_read(a, 1))
        if c == b'\0':
            return b.decode()
        b += c
        a += 1

def run(mu, start, regs, stop_addrs, ctx):
    calls = []
    def hook(uc, addr, size, ud):
        if addr in NAMES:
            n = NAMES[addr]
            g = lambda r: uc.reg_read(r)
            if n == 'fopen':
                calls.append(('fopen', cstr(uc, g(UC_MIPS_REG_A0))))
                uc.reg_write(UC_MIPS_REG_V0, 0x1234 if ctx.get('file') is not None else 0)
            elif n == 'fread':
                data = ctx['file'].encode()
                uc.mem_write(g(UC_MIPS_REG_A0), data)
                uc.reg_write(UC_MIPS_REG_V0, len(data))
                calls.append(('fread', len(data)))
            elif n == 'fclose':
                calls.append('fclose')
            elif n == 'strcpy':
                s = cstr(uc, g(UC_MIPS_REG_A1))
                uc.mem_write(g(UC_MIPS_REG_A0), s.encode() + b'\0')
                calls.append(('strcpy', g(UC_MIPS_REG_A0), s))
            elif n == 'sprintf':
                o = cstr(uc, g(UC_MIPS_REG_A1)) % (cstr(uc, g(UC_MIPS_REG_A2)), cstr(uc, g(UC_MIPS_REG_A3)))
                uc.mem_write(g(UC_MIPS_REG_A0), o.encode() + b'\0')
                calls.append(('sprintf', o))
            elif n == 'system':
                calls.append(('system', cstr(uc, g(UC_MIPS_REG_A0))))
            elif n == 'access':
                pass
                path_ = cstr(uc, g(UC_MIPS_REG_A0)); uc.reg_write(UC_MIPS_REG_V0, (ctx['access_map'][path_] if 'access_map' in ctx else ctx.get('access', 0)) & 0xffffffff)
            return
        if addr in stop_addrs:
            ctx['exit'] = addr
            uc.emu_stop()
    mu.hook_add(UC_HOOK_CODE, hook)
    for r, v in regs.items():
        mu.reg_write(r, v)
    ctx.setdefault('exit', None)
    try:
        mu.emu_start(start, 0, count=30000)
    except UcError as e:
        ctx['err'] = str(e)
    return calls

ok = True
def chk(name, cond):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'ERRO '), name)

FLAGA = 0x52e9ec
SP = 0x60080000; GPV = 0x60050000; EB = 0x60010000; DB = 0x60040000
S3 = UC_MIPS_REG_S3; S0 = UC_MIPS_REG_S0; S5 = UC_MIPS_REG_S5; S6 = UC_MIPS_REG_S6
V0 = UC_MIPS_REG_V0; V1 = UC_MIPS_REG_V1

# ---------- cave4 (main_ui) ----------
MARK = '/tmp/rkgame.boot'
LASTP = '/mnt/sdcard/cubegm/lastgame.txt'
def t4(F, s3, marker_exists, last_exists, mask=0x10108):
    mu = mk()
    mu.mem_write(FLAGA, struct.pack('<I', F))
    ctx = {'access_map': {MARK: 0 if marker_exists else -1, LASTP: 0 if last_exists else -1}, 'file': ''}
    mu.mem_write(SP + 0x28, struct.pack('<I', GPV))
    calls = run(mu, out['cave4'][0], {UC_MIPS_REG_SP: SP, UC_MIPS_REG_GP: GPV, S3: s3, V0: 0, S0: mask}, {0x4147b8}, ctx)
    return ctx, mu.reg_read(S3), rd(mu, FLAGA), mu.reg_read(V0), mu.reg_read(UC_MIPS_REG_GP), calls

c, s3, f, v0, gp, calls = t4(0, 0, False, True)
chk('cave4: boot a frio + lastgame -> injeta A, F=1, cria marcador', c['exit'] == 0x4147b8 and s3 == 0x2000 and f == 1 and gp == GPV and ('fopen', MARK) in calls and 'fclose' in calls)
c, s3, f, v0, gp, calls = t4(0, 0, True, True)
chk('cave4: marcador ja existe (reinicio apos video/musica) -> NAO injeta, F=2', s3 == 0 and f == 2 and not any(isinstance(x, tuple) and x[0] == 'fopen' for x in calls))
c, s3, f, v0, gp, calls = t4(0, 0x4000, False, True)
chk('cave4: boot a frio + B pressionado -> nao injeta, F=2, marcador criado', s3 == 0x4000 and f == 2 and ('fopen', MARK) in calls)
c, s3, f, v0, gp, calls = t4(0, 0, False, False)
chk('cave4: boot a frio sem lastgame -> nao injeta, F=2, marcador criado', s3 == 0 and f == 2 and ('fopen', MARK) in calls)
c, s3, f, v0, gp, calls = t4(1, 0x10, False, True)
chk('cave4: F=1 -> nao mexe', s3 == 0x10 and f == 1 and not calls)
c, s3, f, v0, gp, calls = t4(2, 0x2000, False, True)
chk('cave4: F=2 -> nao mexe e v0=s3&s0', s3 == 0x2000 and f == 2 and v0 == (0x2000 & 0x10108) and not calls)

# ---------- cave5 (lista) ----------
def t5(F, filetxt):
    mu = mk()
    mu.mem_write(FLAGA, struct.pack('<I', F))
    ctx = {'file': filetxt}
    mu.mem_write(SP + 0x940, struct.pack('<I', EB)); mu.mem_write(SP + 0x990, struct.pack('<I', DB))
    mu.mem_write(SP + 0x18, struct.pack('<I', GPV)); mu.mem_write(SP + 0x930, struct.pack('<I', 0x77))
    calls = run(mu, out['cave5'][0], {UC_MIPS_REG_SP: SP, UC_MIPS_REG_GP: GPV, S0: 5, S5: 9, S6: 3}, {0x42f80c, 0x42ede4}, ctx)
    return ctx, calls, mu

c, calls, mu = t5(1, '/mnt/sdcard/roms/luta\nTekken 3 (USA).cue\n')
chk('cave5: F=1 e arquivo valido -> salta para o A-handler', c['exit'] == 0x42f80c)
chk('cave5: pasta copiada para o buffer da pasta atual', cstr(mu, DB - 0x40f4) == '/mnt/sdcard/roms/luta')
chk('cave5: entrada 0 = nome do jogo, tipo 8', cstr(mu, EB) == 'Tekken 3 (USA).cue' and rd(mu, EB + 0x100) == 8)
chk('cave5: s0=0 s5=0 s6=1 e sp/gp restaurados', mu.reg_read(S0) == 0 and mu.reg_read(S5) == 0 and mu.reg_read(S6) == 1 and mu.reg_read(UC_MIPS_REG_SP) == SP and mu.reg_read(UC_MIPS_REG_GP) == GPV)
chk('cave5: F=2', rd(mu, FLAGA) == 2)
c, calls, mu = t5(1, '/mnt/sdcard/roms/luta\r\nTekken 3 (USA).cue\r\n')
chk('cave5: aceita CRLF', c['exit'] == 0x42f80c and cstr(mu, EB) == 'Tekken 3 (USA).cue' and cstr(mu, DB - 0x40f4) == '/mnt/sdcard/roms/luta')
c, calls, mu = t5(1, 'so-uma-linha')
chk('cave5: arquivo invalido -> retoma o fluxo normal', c['exit'] == 0x42ede4 and mu.reg_read(V0) == 0x77 and mu.reg_read(V1) == 1 and mu.reg_read(UC_MIPS_REG_SP) == SP and mu.reg_read(S6) == 3 and mu.reg_read(S0) == 5)
c, calls, mu = t5(1, None)
chk('cave5: sem arquivo -> retoma o fluxo normal', c['exit'] == 0x42ede4 and mu.reg_read(UC_MIPS_REG_SP) == SP and mu.reg_read(S0) == 5)
c, calls, mu = t5(0, '/x\ny\n')
chk('cave5: F=0 -> nao age', c['exit'] == 0x42ede4 and not calls)
c, calls, mu = t5(2, '/x\ny\n')
chk('cave5: F=2 -> nao age', c['exit'] == 0x42ede4 and not calls)

# ---------- cave3 (registro do ultimo jogo) ----------
def t3(s6, d_type, name):
    mu = mk()
    ctx = {}
    mu.mem_write(SP + 0x940, struct.pack('<I', EB)); mu.mem_write(SP + 0x990, struct.pack('<I', DB))
    mu.mem_write(SP + 0x18, struct.pack('<I', GPV)); mu.mem_write(SP + 0x930, struct.pack('<I', 0x77))
    mu.mem_write(DB - 0x40f4, b'/mnt/sdcard/roms/luta\0')
    mu.mem_write(EB + 2 * 0x404, name.encode() + b'\0'); mu.mem_write(EB + 2 * 0x404 + 0x100, struct.pack('<I', d_type))
    calls = run(mu, out['cave3'][0], {UC_MIPS_REG_SP: SP, UC_MIPS_REG_GP: GPV, S0: 2, S6: s6}, {0x42f814, 0x42f734}, ctx)
    return ctx, calls, mu

c, calls, mu = t3(3, 8, 'Tekken 3 (USA).cue')
chk('cave3: arquivo -> grava lastgame via setlast.sh e segue o fluxo', ('system', '/bin/sh /mnt/sdcard/cubegm/setlast.sh "/mnt/sdcard/roms/luta" "Tekken 3 (USA).cue"') in calls and c['exit'] == 0x42f814 and mu.reg_read(UC_MIPS_REG_SP) == SP and mu.reg_read(V0) == 0x77)
c, calls, mu = t3(3, 4, 'aventura')
chk('cave3: pasta -> nao grava', not calls and c['exit'] == 0x42f814)
c, calls, mu = t3(0, 8, 'x.cue')
chk('cave3: lista vazia -> desvia para o destino original', c['exit'] == 0x42f734 and not calls)

# ---------- novo: so retoma se desligou jogando ----------
def forgets(calls):
    return any(isinstance(x, tuple) and x[0] == 'system' and 'rm -f /mnt/sdcard/cubegm/lastgame.txt' in x[1] for x in calls)
c, s3, f, v0, gp, calls = t4(0, 0, True, True)
chk('cave4: reinicio (marcador existe) -> esquece o ultimo jogo', forgets(calls) and f == 2 and gp == GPV)
c, s3, f, v0, gp, calls = t4(0, 0x4000, False, True)
chk('cave4: B pressionado ao ligar -> esquece o ultimo jogo', forgets(calls) and f == 2)
c, s3, f, v0, gp, calls = t4(0, 0, False, True)
chk('cave4: boot a frio com lastgame -> retoma e NAO apaga', not forgets(calls) and f == 1 and s3 == 0x2000)
c, s3, f, v0, gp, calls = t4(2, 0x2000, True, True)
chk('cave4: F=2 -> nunca apaga de novo', not forgets(calls))

def t8():
    mu = mk()
    ctx = {}
    mu.mem_write(SP + 0x18, struct.pack('<I', GPV))
    calls = run(mu, out['cave8'][0], {UC_MIPS_REG_SP: SP, UC_MIPS_REG_GP: 0x1234, UC_MIPS_REG_FP: 0x5050, S3: 0x5000}, {0x42fe78}, ctx)
    return ctx, calls, mu
c, calls, mu = t8()
chk('cave8: jogo terminou -> apaga lastgame.txt (e registra gameexit)', forgets(calls) and any('gameexit' in x[1] for x in calls if isinstance(x, tuple)) and c['exit'] == 0x42fe78)
chk('cave8: executa a instrucao original (a2 = fp - s3), restaura gp e sp', mu.reg_read(UC_MIPS_REG_A2) == 0x50 and mu.reg_read(UC_MIPS_REG_GP) == GPV and mu.reg_read(UC_MIPS_REG_SP) == SP)
chk('cave8: hook original confere com o rkgame de fabrica', R.HOOKS['cave8'] == (0x42FE70, '2330d3031800bc8f'))
print('TODOS OK' if ok else 'FALHOU')
sys.exit(0 if ok else 1)
