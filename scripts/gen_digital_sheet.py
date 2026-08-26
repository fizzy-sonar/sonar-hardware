#!/usr/bin/env python3
"""T-011 digital sheet generator (Sonar v1, D012). Stdlib only.

Single source of truth for the Cmod A7-35T pin assignment. Regenerates:
  - sonar-v1-pcb/digital.kicad_sch            (digital sheet, per D012)
  - sonar-v1-pcb/sonar.kicad_sch              (removes DF40/adc_bus, adds sheet block)
  - gateware/constraints/sonar_cmod_a7.xdc    (T-020 starting constraints)
  - orchestration/pinmap.md                   (authoritative audited pin table)

PROVENANCE: the pio->package-pin mapping below is transcribed OFFLINE from the
Digilent Cmod-A7-Master.xdc / Cmod A7 reference manual (no network on either the
authoring or the 2026-08-26 audit machine - both sandboxes block DNS/TCP and the
approval policy forbids escalation). Second-agent audit (codex/sol-t011-audit,
2026-08-26) found the table internally self-consistent (every MRCC/SRCC IO-name
string matches its clock-capable flag) and matching the auditor's independent
recall of the master XDC 48/48; the T-008 clock-capable list in
docs/pdm-capture-contract.md was found corrupt (it claims pio46/47/48 as
clock-capable, but those DIP positions are the power pins - the master XDC GPIO
section stops at pio44 - so its contested pio18/19/37/38/40 entries lose
authority) and has been corrected there. Clock-critical nets use only pins where
BOTH sources agree (pio3/5/8/36/43), so no net assignment changed.
STILL OUTSTANDING before T-020 synthesis: one live fetch of
https://github.com/Digilent/digilent-xdc/blob/master/Cmod-A7-Master.xdc and the
Cmod A7 reference manual pinout table (60-second human paste-check is enough) to
confirm the table byte-for-byte, the DIP position<->pio identity mapping, and the
power-pin positions 45=GND/46=3V3/47=VU/48=GND.

Run from repo root:  python3 scripts/gen_digital_sheet.py
"""
import os, re, sys, uuid, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYMLIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
ROOT_SHEET_UUID = "f72ceae0-eee4-4385-b0e8-639846bcb5f2"   # sonar.kicad_sch
DIGITAL_SHEET_UUID = "d19a7a11-b1c2-4d3e-8f40-a11d1a11ce11"  # stable across runs
DIGITAL_SHEET_INST_UUID = "d19a7a11-b1c2-4d3e-8f40-a11d1a11ce22"
DIGITAL_PAGE = "40"

def U(): return str(uuid.uuid4())
def fmt(v): return f"{v:.2f}".rstrip('0').rstrip('.')

# ---------------------------------------------------------------------------
# PIN TABLE -- single source of truth.
# (pio, dip_pin, pkg, io_name, bank, cc, net, fpga_dir, group, note)
#   cc: "yes"=clock-capable (MRCC/SRCC in IO name; T-008 list resolved as corrupt in
#       the 2026-08-26 audit, see pinmap.md), ""=not CC.
# ---------------------------------------------------------------------------
PINS = [
 ("pio1",  1,"M3","IO_L8N_T1_AD14N_35",      35,"",        "TX_EN",       "out",  "tx",  "DRV8876 EN/IN1 (T-013)"),
 ("pio2",  2,"L3","IO_L8P_T1_AD14P_35",      35,"",        "TX_PH",       "out",  "tx",  "DRV8876 PH/IN2 (T-013)"),
 ("pio3",  3,"A16","IO_L12P_T1_MRCC_16",     16,"yes",     "ETH_REF_CLK", "in",   "eth", "50 MHz osc input (DNP block); MRCC_16"),
 ("pio4",  4,"K3","IO_L7N_T1_AD6N_35",       35,"",        "ETH_MDC",     "out",  "eth", ""),
 ("pio5",  5,"C15","IO_L11P_T1_SRCC_16",     16,"yes",     "TX_NFAULT",   "in",   "tx",  "open-drain; pull-up on TX sheet"),
 ("pio6",  6,"H1","IO_L3P_T0_DQS_AD5P_35",   35,"",        "ETH_MDIO",    "inout","eth", ""),
 ("pio7",  7,"A15","IO_L6N_T0_VREF_16",      16,"",        "PDM_CLK_EN",  "out",  "pdm", "CDCLVC1112 1G; 100k pulldown on array sheet"),
 ("pio8",  8,"B15","IO_L11N_T1_SRCC_16",     16,"yes",     "TX_PMODE",    "out",  "tx",  ""),
 ("pio9",  9,"A14","IO_L6P_T0_16",           16,"",        "PDM_CLK_SRC", "out",  "pdm", "3.072 MHz v1 / 4.8 MHz ICS alt, from MMCM"),
 ("pio10",10,"J3","IO_L7P_T1_AD6P_35",       35,"",        "PDM_D0",      "in",   "pdm", "CH00/CH01 = M00/M10"),
 ("pio11",11,"J1","IO_L3N_T0_DQS_AD5N_35",   35,"",        "PDM_D1",      "in",   "pdm", "CH02/CH03 = M20/M30"),
 ("pio12",12,"K2","IO_L5P_T0_AD13P_35",      35,"",        "PDM_D2",      "in",   "pdm", "CH04/CH05 = M01/M11"),
 ("pio13",13,"L1","IO_L6N_T0_VREF_35",       35,"",        "PDM_D3",      "in",   "pdm", "CH06/CH07 = M21/M31"),
 ("pio14",14,"L2","IO_L5N_T0_AD13N_35",      35,"",        "PDM_D4",      "in",   "pdm", "CH08/CH09 = M02/M12"),
 ("pio15",15,"M1","IO_L9N_T1_DQS_AD7N_35",   35,"",        "PDM_D5",      "in",   "pdm", "CH10/CH11 = M32/M42"),
 ("pio16",16,"N3","IO_L12P_T1_MRCC_35",      35,"yes", "PDM_D6",      "in",   "pdm", "CH12/CH13 = M03/M13"),
 ("pio17",17,"P3","IO_L12N_T1_MRCC_35",      35,"yes", "PDM_D7",      "in",   "pdm", "CH14/CH15 = M23/M33"),
 ("pio18",18,"M2","IO_L9P_T1_DQS_AD7P_35",   35,"", "PDM_D8",      "in",   "pdm", "CH16/CH17 = M04/M14"),
 ("pio19",19,"N1","IO_L10N_T1_AD15N_35",     35,"", "PDM_D9",      "in",   "pdm", "CH18/CH19 = M24/M34"),
 ("pio20",20,"N2","IO_L10P_T1_AD15P_35",     35,"",        "PDM_D10",     "in",   "pdm", "CH20/CH21 = M40/M41"),
 ("pio21",21,"P1","IO_L19N_T3_VREF_35",      35,"",        "PDM_D11",     "in",   "pdm", "CH22/CH23 = M43/M44"),
 ("pio22",22,"R3","IO_L2P_T0_34",            34,"",        "FT_D0",       "inout","ft",  ""),
 ("pio23",23,"T3","IO_L2N_T0_34",            34,"",        "FT_D1",       "inout","ft",  ""),
 ("pio24",24,"R2","IO_L1P_T0_34",            34,"",        "FT_D2",       "inout","ft",  ""),
 ("pio25",25,"T1","IO_L3P_T0_DQS_34",        34,"",        "FT_D3",       "inout","ft",  ""),
 ("pio26",26,"T2","IO_L1N_T0_34",            34,"",        "FT_D4",       "inout","ft",  ""),
 ("pio27",27,"U1","IO_L3N_T0_DQS_34",        34,"",        "FT_D5",       "inout","ft",  ""),
 ("pio28",28,"W2","IO_L5N_T0_34",            34,"",        "FT_D6",       "inout","ft",  ""),
 ("pio29",29,"V2","IO_L5P_T0_34",            34,"",        "FT_D7",       "inout","ft",  ""),
 ("pio30",30,"W3","IO_L6N_T0_VREF_34",       34,"",        "FT_RXF_N",    "in",   "ft",  "ACBUS0"),
 ("pio31",31,"V3","IO_L6P_T0_34",            34,"",        "FT_TXE_N",    "in",   "ft",  "ACBUS1"),
 ("pio32",32,"W5","IO_L12P_T1_MRCC_34",      34,"yes", "FT_RD_N",     "out",  "ft",  "ACBUS2"),
 ("pio33",33,"V4","IO_L11N_T1_SRCC_34",      34,"yes", "FT_WR_N",     "out",  "ft",  "ACBUS3"),
 ("pio34",34,"U4","IO_L11P_T1_SRCC_34",      34,"yes", "FT_OE_N",     "out",  "ft",  "ACBUS6"),
 ("pio35",35,"V5","IO_L16N_T2_34",           34,"",        "ETH_TXD0",    "out",  "eth", ""),
 ("pio36",36,"W4","IO_L12N_T1_MRCC_34",      34,"yes",     "PDM_CLK_FB",  "in",   "pdm", "RETURNED CLOCK - clock-capable pin mandatory (T-008)"),
 ("pio37",37,"U5","IO_L16P_T2_34",           34,"", "ETH_TXD1",    "out",  "eth", ""),
 ("pio38",38,"U2","IO_L9N_T1_DQS_34",        34,"", "ETH_TX_EN",   "out",  "eth", ""),
 ("pio39",39,"W6","IO_L13N_T2_MRCC_34",      34,"yes", "ETH_RXD0",    "in",   "eth", ""),
 ("pio40",40,"U3","IO_L9P_T1_DQS_34",        34,"", "ETH_RXD1",    "in",   "eth", ""),
 ("pio41",41,"U7","IO_L19P_T3_34",           34,"",        "ETH_CRS_DV",  "in",   "eth", ""),
 ("pio42",42,"W7","IO_L13P_T2_MRCC_34",      34,"yes", "ETH_RX_ER",   "in",   "eth", ""),
 ("pio43",43,"U8","IO_L14P_T2_SRCC_34",      34,"yes",     "FT_CLKOUT",   "in",   "ft",  "60 MHz sync-FIFO clock; SRCC_34"),
 ("pio44",44,"V8","IO_L14N_T2_SRCC_34",      34,"yes", "TX_NSLEEP",   "out",  "tx",  "DRV8876 nSLEEP (T-013)"),
 ("pio45",45,"--","(power)",                   0,"",        "GND",         "pwr",  "pwr", "socket power pin (recalled position - VERIFY)"),
 ("pio46",46,"--","(power)",                   0,"",        "CMOD_3V3",    "pwr",  "pwr", "module 3V3 rail pin (recalled - VERIFY); NC default, SJ1 DNP"),
 ("pio47",47,"--","(power)",                   0,"",        "CMOD_VU",     "pwr",  "pwr", "module VU/USB-5V pin (recalled - VERIFY); NC default, SJ2 DNP"),
 ("pio48",48,"--","(power)",                   0,"",        "GND",         "pwr",  "pwr", "socket power pin (recalled position - VERIFY)"),
]
ONMODULE = [  # on-module Cmod A7 resources (not on DIP socket), recalled from master XDC
 ("sysclk","L17","IO_L12P_T1_MRCC_14",14,"12 MHz oscillator (on module)"),
 ("led[0]","A17","IO_L12N_T1_MRCC_16",16,"on-module LED1"),
 ("led[1]","C16","IO_L13P_T2_MRCC_16",16,"on-module LED2"),
 ("led0_b","B17","IO_L14N_T2_SRCC_16",16,"on-module RGB LED blue"),
 ("led0_g","B16","IO_L13N_T2_MRCC_16",16,"on-module RGB LED green"),
 ("led0_r","C17","IO_L14P_T2_SRCC_16",16,"on-module RGB LED red"),
 ("btn[0]","A18","IO_L19N_T3_VREF_16",16,"on-module BTN0"),
 ("btn[1]","B18","IO_L19P_T3_16",16,"on-module BTN1"),
]
PMOD_JA = [  # on-module Pmod JA (bank 14), spare, not wired on this board
 ("ja[0]","G17","IO_L5N_T0_D07_14"),("ja[1]","G19","IO_L4N_T0_D05_14"),
 ("ja[2]","N18","IO_L9P_T1_DQS_14"),("ja[3]","L18","IO_L8P_T1_D11_14"),
 ("ja[4]","H17","IO_L5P_T0_D06_14"),("ja[5]","H19","IO_L4P_T0_D04_14"),
 ("ja[6]","J19","IO_L6N_T0_D08_VREF_14"),("ja[7]","K18","IO_L8N_T1_D12_14"),
]

# ---------------------------------------------------------------------------
# s-expression / symbol helpers
# ---------------------------------------------------------------------------
def lib_symbol_block(libfile, name):
    src = open(os.path.join(SYMLIB, libfile)).read()
    m = re.search(r'\(symbol "' + re.escape(name) + r'"[\s\n]', src)
    if not m: raise KeyError(f"{libfile}:{name} not found")
    i = m.start(); d = 0; j = i
    while True:
        c = src[j]
        if c == '(': d += 1
        elif c == ')':
            d -= 1
            if d == 0: return src[i:j+1]
        j += 1

def embed_symbol(libname, libfile, symname):
    return lib_symbol_block(libfile, symname).replace(
        f'(symbol "{symname}"', f'(symbol "{libname}:{symname}"', 1)

def pins_of(block):
    out = []
    for m in re.finditer(r'\(pin \S+ \S+\s+\(at ([\d.-]+) ([\d.-]+) (\d+)\)', block):
        i = m.start(); d = 0; j = i
        while True:
            c = block[j]
            if c == '(': d += 1
            elif c == ')':
                d -= 1
                if d == 0: break
            j += 1
        p = block[i:j+1]
        ty = re.match(r'\(pin (\S+) (\S+)', p)
        nm = re.search(r'\(name "((?:[^"\\]|\\.)*)"', p)
        no = re.search(r'\(number "([^"]*)"', p)
        out.append(dict(num=no.group(1), name=nm.group(1), type=ty.group(1),
                        x=float(m.group(1)), y=float(m.group(2)), ang=int(m.group(3))))
    return out

def dir_vec(angle):
    a = math.radians(angle + 180)   # away from symbol body, +y down
    return (math.cos(a), math.sin(a))

# ---------------------------------------------------------------------------
class Sheet:
    def __init__(self):
        self.items, self.symbols, self.libs = [], [], {}

    def symbol(self, libname, libfile, symname, ref, value, x, y, rot=0, fp="",
               dnp=False, value_hide=False):
        x = round(x/1.27)*1.27   # keep pins on the 1.27 mm connection grid (ERC)
        y = round(y/1.27)*1.27
        key = f"{libname}:{symname}"
        self.libs[key] = (libfile, symname)
        pins = pins_of(lib_symbol_block(libfile, symname))
        b = ['\t(symbol', f'\t\t(lib_id "{key}")', f'\t\t(at {fmt(x)} {fmt(y)} {rot})',
             '\t\t(unit 1)', '\t\t(body_style 1)', '\t\t(exclude_from_sim yes)',
             '\t\t(in_bom yes)', '\t\t(on_board yes)', '\t\t(in_pos_files yes)',
             f'\t\t(dnp {"yes" if dnp else "no"})', '\t\t(fields_autoplaced yes)',
             f'\t\t(uuid "{U()}")']
        def prop(name, val, dy, hide=False):
            b.append(f'\t\t(property "{name}" "{val}"')
            b.append(f'\t\t\t(at {fmt(x)} {fmt(y+dy)} 0)')
            if hide: b.append('\t\t\t(hide yes)')
            b.append('\t\t\t(show_name no)')
            b.append('\t\t\t(do_not_autoplace no)')
            b.append('\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)')
        prop("Reference", ref, -3.81, hide=ref.startswith('#'))
        prop("Value", value, 3.81, hide=value_hide)
        prop("Footprint", fp, 0, hide=True)
        prop("Datasheet", "", 0, hide=True)
        prop("Description", "", 0, hide=True)
        for p in pins:
            b.append(f'\t\t(pin "{p["num"]}"\n\t\t\t(uuid "{U()}")\n\t\t)')
        b.append('\t\t(instances\n\t\t\t(project "sonar"')
        b.append(f'\t\t\t\t(path "/{ROOT_SHEET_UUID}/{DIGITAL_SHEET_UUID}"')
        b.append(f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
        self.symbols.append('\n'.join(b))
        # KiCad negates lib-symbol Y on placement (verified against kicad-cli ERC
        # coordinates, 2026-08-26): sheet_pos = (X+px, Y-py), angle -> 360-angle.
        anchors = {}
        for p in pins:
            if rot == 0: rx, ry, ra = p['x'], -p['y'], (360 - p['ang']) % 360
            elif rot == 180: rx, ry, ra = -p['x'], p['y'], (180 - p['ang']) % 360
            else: raise ValueError("only rot 0/180 supported")
            anchors[p['num']] = dict(x=x+rx, y=y+ry, ang=ra, name=p['name'], type=p['type'])
        return anchors

    def wire(self, x1, y1, x2, y2):
        self.items.append(
            f'\t(wire\n\t\t(pts\n\t\t\t(xy {fmt(x1)} {fmt(y1)}) (xy {fmt(x2)} {fmt(y2)})\n\t\t)\n'
            f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')

    def global_label(self, name, x, y, angle=0, shape="passive"):
        just = "right" if angle == 180 else "left"
        self.items.append(
            f'\t(global_label "{name}"\n\t\t(shape {shape})\n\t\t(at {fmt(x)} {fmt(y)} {angle})\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n'
            f'\t\t(uuid "{U()}")\n'
            f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n\t\t\t(at {fmt(x)} {fmt(y)} 0)\n'
            f'\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)\n\t)')

    def no_connect(self, x, y):
        self.items.append(f'\t(no_connect\n\t\t(at {fmt(x)} {fmt(y)})\n\t\t(uuid "{U()}")\n\t)')

    def text(self, s, x, y, size=1.27, bold=False):
        esc = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        bf = '\n\t\t\t\t(bold yes)' if bold else ''
        self.items.append(
            f'\t(text "{esc}"\n\t\t(exclude_from_sim no)\n\t\t(at {fmt(x)} {fmt(y)} 0)\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size}){bf}\n\t\t\t)\n\t\t\t(justify left top)\n\t\t)\n'
            f'\t\t(uuid "{U()}")\n\t)')

    # -- composite wiring ----------------------------------------------------
    def stub_label(self, anchor, net, shape="passive", length=7.62):
        vx, vy = dir_vec(anchor['ang'])
        ex, ey = anchor['x']+vx*length, anchor['y']+vy*length
        self.wire(anchor['x'], anchor['y'], ex, ey)
        ang = 0 if vx >= 0 else 180
        self.global_label(net, ex, ey, ang, shape)

    def stub_power(self, anchor, psym, ref, rot=None, length=2.54):
        vx, vy = dir_vec(anchor['ang'])
        ex, ey = anchor['x']+vx*length, anchor['y']+vy*length
        self.wire(anchor['x'], anchor['y'], ex, ey)
        if rot is None:
            # body extends along the wire direction, away from the device pin:
            # GND body is below its pin at rot 0; +3.3V body is above at rot 0.
            if round(vy) != 0:
                rot = (0 if vy > 0 else 180) if psym == "GND" else (180 if vy > 0 else 0)
            else:
                rot = 0
        pp = pins_of(lib_symbol_block("power.kicad_sym", psym))[0]
        # pin is at (0,0) in power symbols; place origin at wire end
        self.symbol("power", "power.kicad_sym", psym, ref, psym, ex, ey, rot=rot,
                    value_hide=True)

    def stub_nc(self, anchor):
        self.no_connect(anchor['x'], anchor['y'])

    def write(self, path):
        out = ['(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")',
               f'\t(uuid "{DIGITAL_SHEET_UUID}")', '\t(paper "A3")',
               '\t(title_block\n\t\t(title "Sonar v1 - Digital: Cmod A7-35T + FT232H + PDM header + DNP RMII")\n\t\t(rev "1")\n\t)',
               '\t(lib_symbols']
        for key,(libfile, symname) in sorted(self.libs.items()):
            block = embed_symbol(key.split(':')[0], libfile, symname)
            for line in block.split('\n'):
                out.append('\t\t' + line)
        out.append('\t)')
        out.extend(self.items)
        out.extend(self.symbols)
        out.append(f'\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "{DIGITAL_PAGE}")\n\t\t)\n\t)')
        out.append('\t(embedded_fonts no)')
        out.append(')')
        open(path, 'w').write('\n'.join(out) + '\n')

# ---------------------------------------------------------------------------
# Digital sheet construction
# ---------------------------------------------------------------------------
SHAPE = {"in": "input", "out": "output", "inout": "bidirectional", "pwr": "passive"}

def build():
    sh = Sheet()
    # ---- notes -------------------------------------------------------------
    sh.text("Sonar v1 - Digital sheet (T-011, D012): Cmod A7-35T DIP-48 socket, FT232H sync-FIFO header, generic PDM header, DNP RMII provision, TX control, test points.", 25.4, 12.7, 1.524, bold=True)
    sh.text("AUTHORITATIVE PIN TABLE: orchestration/pinmap.md (generated by scripts/gen_digital_sheet.py).\n"
            "Clock-capable pins: PDM_CLK_FB=pio36 (MRCC), FT_CLKOUT=pio43 (SRCC), ETH_REF_CLK=pio3 (MRCC) - all double-sourced.\n"
            "Package pins: offline transcription of the Digilent Cmod-A7-Master.xdc, audited offline by a second agent 2026-08-26;\n"
            "live master-XDC diff still required before T-020 synthesis (see orchestration/pinmap.md).", 25.4, 18.5)
    sh.text("POWER STRATEGY (decided, T-011): the Cmod A7 powers itself from its own micro-USB. The board does not power the module and the\n"
            "module does not power the board: CMOD_3V3 / CMOD_VU default to no-connect. SJ1/SJ2 are DNP solder-jumper rework options\n"
            "(SJ1: module 3V3 <-> board +3.3V; SJ2: module VU <-> board 5V - fit only with T-012 review, never as a paralleled-regulator hack).\n"
            "Grounds are common through the socket GND pins. The FT232H breakout is self-powered from its own USB (its 5V pin is NC).\n"
            "Board +3.3V rail source: T-012 power tree (do not confuse with the legacy \"3.3V\" net of the old analog tree).", 25.4, 29)
    sh.text("PDM HEADER CONTENTION RULE (D012): exactly ONE capture platform attached at a time - either the Cmod A7 in socket J40,\n"
            "or the Pico 2 (T-009) via ribbon on J42. NEVER both: both would drive PDM_CLK_SRC/PDM_CLK_EN into each other.\n"
            "Microphones and the CDCLVC1112 clock buffer live on the array sheet (T-010/T-016); PDM_* nets cross sheets by global label.", 25.4, 42.5)
    sh.text("TX control nets (TX_EN/TX_PH/TX_NSLEEP/TX_NFAULT/TX_PMODE) leave this sheet by global label to the TX h-bridge sheet (T-013).\n"
            "TX_NFAULT is open-drain: pull-up belongs on the TX sheet. Debug LEDs: use on-module Cmod LEDs (led0/led1/RGB) - see pinmap.md.", 25.4, 52)

    # ---- J40: Cmod DIP-48 socket -------------------------------------------
    pm = sh.symbol("Connector_Generic", "Connector_Generic.kicad_sym",
                   "Conn_02x24_Counter_Clockwise", "J40", "DIP-48 socket - Cmod A7-35T",
                   185, 95, value_hide=True, fp="Package_DIP:DIP-48_W15.24mm_Socket")
    n_pwr = 0
    for p in PINS:
        dip, net, d = str(p[1]), p[6], p[7]
        a = pm[dip]
        if net == "GND":
            n_pwr += 1
            sh.stub_power(a, "GND", f"#PWR4{n_pwr:02d}")
        else:
            sh.stub_label(a, net, SHAPE[d])

    # ---- J41: FT232H header (Adafruit 2264-style 1x20) ----------------------
    ft = sh.symbol("Connector_Generic", "Connector_Generic.kicad_sym",
                   "Conn_01x20", "J41", "FT232H breakout header (Adafruit-style)",
                   265, 105, value_hide=True, fp="Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical")
    FT_MAP = {"1": None, "2": "GND",
              "3": "FT_D0", "4": "FT_D1", "5": "FT_D2", "6": "FT_D3", "7": "FT_D4",
              "8": "FT_D5", "9": "FT_D6", "10": "FT_D7",
              "11": "FT_RXF_N", "12": "FT_TXE_N", "13": "FT_RD_N", "14": "FT_WR_N",
              "15": "FT_SIWU", "16": "FT_CLKOUT", "17": "FT_OE_N",
              "18": None, "19": None, "20": None}
    for num, net in FT_MAP.items():
        a = ft[num]
        if net is None: sh.stub_nc(a)
        elif net == "GND": sh.stub_power(a, "GND", "#PWR450")
        else: sh.stub_label(a, net, SHAPE[{"FT_SIWU": "out"}.get(net, "") or next((q[7] for q in PINS if q[6] == net), "inout")])
    sh.text("J41: 1x20 0.1in header matching the Adafruit FT232H breakout (#2264): pin1=5V (NC), pin2=GND, pins3-10=D0-D7,\n"
            "pins11-20=C0-C9. Sync-FIFO (FT245) mapping: C0=RXF#, C1=TXE#, C2=RD#, C3=WR#, C4=SIWU (FPGA tie option),\n"
            "C5=CLKOUT (60 MHz, to clock-capable pio43), C6=OE#, C7-C9 unused (NC). Breakout VCCIO is 3.3 V.\n"
            "VERIFY the physical breakout pin order against the Adafruit board at layout (net identities are what matter).", 262, 135)

    # ---- J42: generic PDM header (2x13, GND interleave) ---------------------
    pd = sh.symbol("Connector_Generic", "Connector_Generic.kicad_sym",
                   "Conn_02x13_Odd_Even", "J42", "PDM array header / Pico 2 ribbon",
                   265, 195, value_hide=True, fp="Connector_IDC:IDC-Header_2x13_P2.54mm_Vertical")
    PDM_MAP = {}
    for i in range(12): PDM_MAP[str(1 + 2*i)] = f"PDM_D{i}"
    PDM_MAP["25"] = "PDM_CLK_SRC"
    for n in (2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24): PDM_MAP[str(n)] = "GND"
    PDM_MAP["22"] = "PDM_CLK_EN"
    PDM_MAP["26"] = "PDM_CLK_FB"
    gnd_n = 0
    for num in sorted(PDM_MAP, key=int):
        net = PDM_MAP[num]; a = pd[num]
        if net == "GND":
            gnd_n += 1
            sh.stub_power(a, "GND", f"#PWR46{gnd_n}")
        else:
            sh.stub_label(a, net, SHAPE[next(q[7] for q in PINS if q[6] == net)])
    sh.text("J42: 2x13 IDC, every data line has an adjacent GND (odd pins = signals, even pins = GND except pin22=CLK_EN, pin26=CLK_FB).\n"
            "Doubles as the Pico 2 v0 ribbon attachment. CONTENTION RULE: Cmod in J40 OR ribbon on J42, never both.\n"
            "Signals + GND only: both platforms are self-powered; the mic rail 3V3_MIC stays on the array sheet (T-010/T-012).", 262, 218)

    # ---- DNP Ethernet provision ---------------------------------------------
    sh.text("DNP ETHERNET PROVISION (D012 amendment b): U60 LAN8720A + J43 HR911105A MagJack + X1 50 MHz osc + R400-R403/C400-C406 are ALL DNP on v1.\n"
            "100M RMII carries only the decimated stream (raw PDM needs the FT232H). Populate-and-learn milestone, never a respin.\n"
            "MODE[2:0]/PHYAD0 strap levels (RXD0/RXD1/CRS_DV/RXER pins) are sampled at nRST release - Artix-7 config-time weak pull-ups can\n"
            "override the PHY's internal strap pulls; determine strap resistors from the LAN8720A datasheet at populate time.\n"
            "TCT to +3.3V / RCT decoupled per LAN8720A voltage-mode reference - verify against the chosen PHY+jack datasheets at populate.", 285, 25)
    u = sh.symbol("Interface_Ethernet", "Interface_Ethernet.kicad_sym",
                  "LAN8720A", "U60", "LAN8720A", 340, 115, dnp=True,
                  fp="Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.5x2.5mm")
    U60 = {  # pin -> (action, net)  # ref U60: U50 collides with legacy array-sheet U50
        "1": ("pwr", "+3.3V"), "6": ("label", "ETH_VDDCR"), "9": ("pwr", "+3.3V"),
        "19": ("pwr", "+3.3V"), "25": ("pwr", "GND"),
        "4": ("nc", None), "14": ("nc", None),
        "5": ("label", "ETH_REF_CLK"), "15": ("label", "ETH_RST_N"),
        "7": ("label", "ETH_RXD1"), "8": ("label", "ETH_RXD0"),
        "10": ("label", "ETH_RX_ER"), "11": ("label", "ETH_CRS_DV"),
        "12": ("label", "ETH_MDIO"), "13": ("label", "ETH_MDC"),
        "16": ("label", "ETH_TX_EN"), "17": ("label", "ETH_TXD0"), "18": ("label", "ETH_TXD1"),
        "20": ("label", "ETH_TXN"), "21": ("label", "ETH_TXP"),
        "22": ("label", "ETH_RXN"), "23": ("label", "ETH_RXP"),
        "24": ("label", "ETH_RBIAS"), "2": ("label", "ETH_INTSEL"), "3": ("label", "ETH_REGOFF"),
    }
    for num, (act, net) in U60.items():
        a = u[num]
        if act == "nc": sh.stub_nc(a)
        elif act == "pwr": sh.stub_power(a, net, f"#PWR47{num}")
        else: sh.stub_label(a, net)

    mj = sh.symbol("Connector", "Connector.kicad_sym",
                   "RJ45_Hanrun_HR911105A_Horizontal", "J43", "HR911105A MagJack", 400, 70, value_hide=True,
                   dnp=True, fp="Connector_RJ:RJ45_Hanrun_HR911105A_Horizontal")
    MJ = {"1": ("label", "ETH_TXP"), "2": ("label", "ETH_TXN"),
          "3": ("label", "ETH_RXP"), "6": ("label", "ETH_RXN"),
          "4": ("pwr", "+3.3V"), "5": ("label", "ETH_RCT"),
          "8": ("pwr", "+3.3V"), "SH": ("pwr", "GND"),
          "9": ("nc", None), "10": ("nc", None), "11": ("nc", None), "12": ("nc", None)}
    for num, (act, net) in MJ.items():
        a = mj[num]
        if a['type'] == 'no_connect': continue
        if act == "nc": sh.stub_nc(a)
        elif act == "pwr": sh.stub_power(a, net, f"#PWR48{num if num.isdigit() else '9'}")
        else: sh.stub_label(a, net)
    sh.text("J43 pins 9-12 = jack LED cathodes (NC for v1; pin 8 = LED common, to +3.3V).\n"
            "Bob-Smith termination of unused pairs: evaluate at layout if populated.", 375, 85)

    xo = sh.symbol("Oscillator", "Oscillator.kicad_sym", "SG-8002CA", "X1", "50 MHz (DNP)",
                   310, 60, dnp=True, value_hide=True, fp="Oscillator:Oscillator_SMD_Abracon_ASV-4Pin_7.0x5.1mm")
    for p in xo.values():
        if p['name'] == 'OUT': sh.stub_label(p, "ETH_REF_CLK")
        elif p['name'] == 'GND': sh.stub_power(p, "GND", "#PWR491")
        elif p['name'] in ('Vcc', 'VDD', 'OE'): sh.stub_power(p, "+3.3V", f"#PWR49{p['name'][-1]}")

    # ETH passives (all DNP): value, top-net, bottom-net
    PASSIVES = [
        ("R400", "12.1k 1%", "R", "ETH_RBIAS", "GND"),      # RBIAS
        ("R401", "10k", "R", "ETH_RST_N", "+3.3V"),         # nRST pull-up
        ("R402", "10k", "R", "ETH_INTSEL", "GND"),          # INTSEL strap down
        ("R403", "10k", "R", "ETH_REGOFF", "GND"),          # REGOFF=0: internal 1V2 reg
        ("C400", "100nF", "C", "+3.3V", "GND"),             # VDD2A
        ("C401", "100nF", "C", "+3.3V", "GND"),             # VDDIO
        ("C402", "100nF", "C", "+3.3V", "GND"),             # VDD1A
        ("C403", "100nF", "C", "ETH_VDDCR", "GND"),         # VDDCR HF
        ("C404", "10uF", "C", "ETH_VDDCR", "GND"),          # VDDCR bulk
        ("C405", "100nF", "C", "ETH_RCT", "GND"),           # RX centre tap
        ("C406", "100nF", "C", "+3.3V", "GND"),             # X1 decoupling
    ]
    for i, (ref, val, kind, top, bot) in enumerate(PASSIVES):
        cx, cy = 300 + (i % 6) * 12.7, 160.02 + (i // 6) * 25.4
        fp = ("Resistor_SMD:R_0603_1608Metric" if kind == "R" else "Capacitor_SMD:C_0603_1608Metric")
        a = sh.symbol("Device", "Device.kicad_sym", kind, ref, val, cx, cy, dnp=True, fp=fp)
        top_pin = min(a.values(), key=lambda p: p['y'])
        bot_pin = max(a.values(), key=lambda p: p['y'])
        if top == "+3.3V": sh.stub_power(top_pin, "+3.3V", f"#PWR5{i:02d}")
        else: sh.stub_label(top_pin, top)
        if bot == "GND": sh.stub_power(bot_pin, "GND", f"#PWR6{i:02d}")
        elif bot == "+3.3V": sh.stub_power(bot_pin, "+3.3V", f"#PWR6{i:02d}")
        else: sh.stub_label(bot_pin, bot)

    # ---- power strategy solder jumpers + LED --------------------------------
    sj1 = sh.symbol("Jumper", "Jumper.kicad_sym", "SolderJumper_2_Open", "J44",
                    "SJ1 DNP: Cmod 3V3 <> board +3.3V", 120, 75,
                    dnp=True, fp="Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm")
    sj2 = sh.symbol("Jumper", "Jumper.kicad_sym", "SolderJumper_2_Open", "J45",
                    "SJ2 DNP: Cmod VU <> board 5V", 120, 85,
                    dnp=True, fp="Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm")
    for anchors, nets in ((sj1, ("CMOD_3V3", "+3.3V")), (sj2, ("CMOD_VU", "5V"))):
        for num, net in zip(("1", "2"), nets):
            a = anchors[num]
            if net == "+3.3V": sh.stub_power(a, "+3.3V", f"#PWR7{num}{num}")
            else: sh.stub_label(a, net)

    # power LED on +3.3V
    r = sh.symbol("Device", "Device.kicad_sym", "R", "R410", "1k", 60, 70,
                  fp="Resistor_SMD:R_0603_1608Metric")
    led = sh.symbol("Device", "Device.kicad_sym", "LED", "D400", "LED_PWR", 64, 80,
                    fp="LED_SMD:LED_0603_1608Metric")
    r_top = min(r.values(), key=lambda a: a['y'])
    r_bot = max(r.values(), key=lambda a: a['y'])
    led_a = next(a for a in led.values() if a['name'] == 'A')
    led_k = next(a for a in led.values() if a['name'] == 'K')
    sh.stub_power(r_top, "+3.3V", "#PWR701", rot=0)
    sh.wire(r_bot['x'], r_bot['y'], r_bot['x'], led_a['y'])
    sh.wire(r_bot['x'], led_a['y'], led_a['x'], led_a['y'])
    sh.stub_power(led_k, "GND", "#PWR702")
    sh.text("D400: +3.3V power-good indicator (1k -> ~2 mA).", 46, 90)

    # ---- PWR_FLAGs: +3.3V source is the T-012 power tree (not yet built);
    # ETH_VDDCR is driven by the LAN8720A internal 1.2 V regulator (block DNP).
    pf1 = sh.symbol("power", "power.kicad_sym", "PWR_FLAG", "#FLG401", "PWR_FLAG", 90, 130)
    sh.stub_power(pf1['1'], "+3.3V", "#PWR790")
    pf2 = sh.symbol("power", "power.kicad_sym", "PWR_FLAG", "#FLG402", "PWR_FLAG", 100, 130)
    sh.stub_label(pf2['1'], "ETH_VDDCR")
    sh.text("PWR_FLAGs: +3.3V is sourced by the T-012 power tree (not yet in the schematic);\n"
            "ETH_VDDCR is driven by the LAN8720A internal 1.2V regulator (whole block DNP).", 76, 140)

    # ---- test points ---------------------------------------------------------
    TPS = ["PDM_CLK_SRC", "PDM_CLK_FB", "FT_CLKOUT", "ETH_REF_CLK", "TX_EN", "PDM_CLK_EN", "ETH_RST_N"]
    for i, net in enumerate(TPS):
        tx, ty = 45 + i * 22, 250
        a = sh.symbol("Connector", "Connector.kicad_sym", "TestPoint", f"TP40{i}",
                      net, tx, ty, value_hide=True, fp="TestPoint:TestPoint_Pad_1.5x1.5mm")
        p = a['1']
        vx, vy = dir_vec(p['ang'])
        ex, ey = p['x'] + vx*3.81, p['y'] + vy*3.81
        sh.wire(p['x'], p['y'], ex, ey)
        sh.global_label(net, ex, ey, 0 if vx >= 0 else 180, "passive")

    return sh

# ---------------------------------------------------------------------------
# Top-sheet patch: remove DF40 + adc_bus, insert digital sheet block
# ---------------------------------------------------------------------------
BOX = (285.5, 368.0, 10.0, 205.0)  # xmin, xmax, ymin, ymax of the DF40/adc_bus region

def top_level_blocks(src):
    """Yield (start_line, end_line, first_token) for each depth-1 form."""
    lines = src.split('\n')
    i = 0
    while i < len(lines):
        l = lines[i]
        if re.match(r'^\t\(\S', l):
            depth = l.count('(') - l.count(')')
            j = i
            while depth > 0:
                j += 1
                depth += lines[j].count('(') - lines[j].count(')')
            yield i, j, re.match(r'^\t\((\S+)', l).group(1), lines[i:j+1]
            i = j + 1
        else:
            yield i, i, None, [lines[i]]
            i += 1

def block_at(block_lines):
    for l in block_lines[:8]:
        m = re.search(r'\(at ([\d.-]+) ([\d.-]+)', l)
        if m: return (float(m.group(1)), float(m.group(2)))
    return None

def block_pts(block_lines):
    pts = []
    for l in block_lines:
        for m in re.finditer(r'\(xy ([\d.-]+) ([\d.-]+)\)', l):
            pts.append((float(m.group(1)), float(m.group(2))))
    return pts

def in_box(x, y):
    return BOX[0] <= x <= BOX[1] and BOX[2] <= y <= BOX[3]

def patch_top_sheet(verbose=True):
    path = os.path.join(ROOT, "sonar-v1-pcb", "sonar.kicad_sch")
    src = open(path).read()
    stats = dict(df40=0, adc_labels=0, bus_entry=0, in_box=0, partial=[], kept_labels=[])
    out_chunks = []
    for i, j, tok, lines in top_level_blocks(src):
        text = '\n'.join(lines)
        if tok == 'symbol' and 'DF40C-80DS' in text:
            stats['df40'] += 1; continue
        if tok == 'label':
            m = re.match(r'^\t\(label "((?:[^"\\]|\\.)*)"', lines[0])
            name = m.group(1) if m else ""
            at = block_at(lines)
            if name.startswith('adc_bus'):
                stats['adc_labels'] += 1; continue
            if at and in_box(*at):
                stats['in_box'] += 1; continue
        if tok == 'bus_entry':
            at = block_at(lines)
            assert at and 305 <= at[0] <= 316, f"bus_entry outside expected x: {at}"
            stats['bus_entry'] += 1; continue
        if tok in ('wire', 'bus'):
            pts = block_pts(lines)
            if pts and all(in_box(*p) for p in pts):
                stats['in_box'] += 1; continue
            if pts and any(in_box(*p) for p in pts):
                stats['partial'].append(pts)
        out_chunks.append(text)
    src2 = '\n'.join(out_chunks)

    if 'digital.kicad_sch' not in src2:
        sheet_block = f'''	(sheet
		(at 295 25)
		(size 110 150)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(fields_autoplaced no)
		(stroke
			(width 0.1524)
			(type solid)
		)
		(fill
			(color 157 255 224 1)
		)
		(uuid "{DIGITAL_SHEET_INST_UUID}")
		(property "Sheetname" "digital"
			(at 295 24.2884 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left bottom)
			)
		)
		(property "Sheetfile" "digital.kicad_sch"
			(at 295 175.5846 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left top)
			)
		)
		(instances
			(project "sonar"
				(path "/{ROOT_SHEET_UUID}"
					(page "{DIGITAL_PAGE}")
				)
			)
		)
	)'''
        idx = src2.find('\t(sheet_instances')
        assert idx > 0
        src2 = src2[:idx] + sheet_block + '\n' + src2[idx:]
    open(path, 'w').write(src2)
    if verbose:
        print("top-sheet patch:", stats)
    return stats

# ---------------------------------------------------------------------------
# XDC writer (T-020 starting constraints)
# ---------------------------------------------------------------------------
def pio_num(p): return int(p[0][3:])
def by_net():
    d = {}
    for p in PINS: d[p[6]] = p
    return d

def xdc_line(pkg, port):
    return f"set_property -dict {{ PACKAGE_PIN {pkg:<4} IOSTANDARD LVCMOS33 }} [get_ports {{ {port} }}]"

def write_xdc(path):
    n = by_net()
    L = []
    L.append("## Sonar v1 - Cmod A7-35T constraints (T-011 baseline for T-020)")
    L.append("## GENERATED by scripts/gen_digital_sheet.py - edit the generator or pinmap, not this file.")
    L.append("##")
    L.append("## PROVENANCE: PACKAGE_PIN values transcribed offline from the Digilent")
    L.append("## Cmod-A7-Master.xdc (no network on the authoring OR the audit machine).")
    L.append("## Second-agent audit 2026-08-26: table is self-consistent, matches the auditor's")
    L.append("## independent recall 48/48, and the corrupt T-008 clock-capable list was resolved")
    L.append("## against this table (see orchestration/pinmap.md). One live fetch of the master XDC")
    L.append("## + Cmod A7 reference manual pinout is STILL REQUIRED before first bitstream.")
    L.append("## URL: https://github.com/Digilent/digilent-xdc/blob/master/Cmod-A7-Master.xdc")
    L.append("##")
    L.append("## VCCO: all user banks (14/15/16/34/35) are fixed at 3.3V on the Cmod A7 -> LVCMOS33.")
    L.append("")
    L.append("## 12 MHz on-module oscillator")
    L.append(xdc_line("L17", "sysclk"))
    L.append("create_clock -add -name sys_clk_pin -period 83.333 -waveform {0 41.667} [get_ports { sysclk }]")
    L.append("")
    L.append("## On-module LEDs / buttons (debug)")
    for port, pkg in (("led[0]","A17"),("led[1]","C16"),("led0_b","B17"),("led0_g","B16"),
                      ("led0_r","C17"),("btn[0]","A18"),("btn[1]","B18")):
        L.append(xdc_line(pkg, port))
    L.append("")
    L.append("## PDM microphone interface (T-008 baseline: 12 data lines, paired mics, returned clock)")
    for i in range(12):
        L.append(xdc_line(n[f"PDM_D{i}"][2], f"pdm_d[{i}]"))
    L.append(xdc_line(n["PDM_CLK_SRC"][2], "pdm_clk_src"))
    L.append(xdc_line(n["PDM_CLK_EN"][2], "pdm_clk_en"))
    L.append("## Returned clock from CDCLVC1112 Y11 - MUST land on a clock-capable pin (pio36, MRCC_34).")
    L.append("## IDDR sampling must use this returned clock, not a copy of the source net (capture contract).")
    L.append(xdc_line(n["PDM_CLK_FB"][2], "pdm_clk_fb"))
    L.append("create_clock -add -name pdm_clk_fb_pin -period 325.521 -waveform {0 162.760} [get_ports { pdm_clk_fb }]  # 3.072 MHz v1 (parameterize; 208.333 ns for the 4.8 MHz ICS alternate)")
    L.append("")
    L.append("## FT232H synchronous FIFO (FT245 sync mode, 60 MHz CLKOUT)")
    for i in range(8):
        L.append(xdc_line(n[f"FT_D{i}"][2], f"ft_d[{i}]"))
    for net, port in (("FT_RXF_N","ft_rxf_n"),("FT_TXE_N","ft_txe_n"),("FT_RD_N","ft_rd_n"),
                      ("FT_WR_N","ft_wr_n"),("FT_OE_N","ft_oe_n"),("FT_CLKOUT","ft_clkout")):
        L.append(xdc_line(n[net][2], port))
    L.append("create_clock -add -name ft_clkout_pin -period 16.667 -waveform {0 8.333} [get_ports { ft_clkout }]  # 60 MHz")
    L.append("")
    L.append("## DNP RMII Ethernet provision (LAN8720A + 50 MHz osc; not populated on v1)")
    L.append("## Uncomment when the DNP block is populated.")
    for net, port in (("ETH_TXD0","eth_txd[0]"),("ETH_TXD1","eth_txd[1]"),("ETH_TX_EN","eth_tx_en"),
                      ("ETH_RXD0","eth_rxd[0]"),("ETH_RXD1","eth_rxd[1]"),("ETH_CRS_DV","eth_crs_dv"),
                      ("ETH_RX_ER","eth_rx_er"),("ETH_REF_CLK","eth_ref_clk"),
                      ("ETH_MDC","eth_mdc"),("ETH_MDIO","eth_mdio")):
        L.append("#" + xdc_line(n[net][2], port))
    L.append("#create_clock -add -name eth_ref_clk_pin -period 20.000 -waveform {0 10} [get_ports { eth_ref_clk }]  # 50 MHz")
    L.append("")
    L.append("## TX control to h-bridge sheet (T-013)")
    for net, port in (("TX_EN","tx_en"),("TX_PH","tx_ph"),("TX_NSLEEP","tx_nsleep"),
                      ("TX_NFAULT","tx_nfault"),("TX_PMODE","tx_pmode")):
        L.append(xdc_line(n[net][2], port))
    L.append("")
    L.append("## NOTE for T-020: PDM input timing (tDD 18-40 ns / tDZ 3-16 ns vs pdm_clk_fb both edges)")
    L.append("## belongs in a timing XDC with set_input_delay on both edges; see docs/pdm-capture-contract.md")
    L.append("## and docs/pdm-rx-design.md timing budget (setup 122.2 ns / hold 2.12 ns at 3.072 MHz).")
    open(path, 'w').write('\n'.join(L) + '\n')

# ---------------------------------------------------------------------------
# pinmap.md writer
# ---------------------------------------------------------------------------
def write_pinmap(path):
    n_cc = sum(1 for p in PINS if p[5] == "yes")
    L = []
    L.append("# Sonar v1 authoritative pin map - Cmod A7-35T (T-011)")
    L.append("")
    L.append("_GENERATED by `scripts/gen_digital_sheet.py` from its PIN TABLE - edit the generator, not this file._")
    L.append("")
    L.append("Status: **v1 baseline; second-agent audit done 2026-08-26 (offline, discrepancies**")
    L.append("**resolved); one live primary-source fetch still outstanding** (see below). Every FPGA")
    L.append("signal lands here; T-020's XDC (`gateware/constraints/sonar_cmod_a7.xdc`) is generated")
    L.append("from the same table. Architecture per D011/D012 (ratified); electrical baseline per")
    L.append("`docs/pdm-rx-design.md` + `docs/pdm-capture-contract.md`.")
    L.append("")
    L.append("## Provenance and audit status")
    L.append("")
    L.append("**No network on either machine**: the authoring session and the second-agent audit")
    L.append("session (codex/sol-t011-audit, 2026-08-26) both ran in sandboxes with DNS/TCP blocked")
    L.append("and approval policy `Never`, so the pio->package-pin mapping below is an offline")
    L.append("transcription of the Digilent `Cmod-A7-Master.xdc` / Cmod A7 reference manual that has")
    L.append("NOT yet been diffed byte-for-byte against the live sources.")
    L.append("")
    L.append("Audit evidence gathered 2026-08-26 (see ticket T-011 Log for the full report):")
    L.append("")
    L.append("- The table is internally self-consistent: every IO-name string containing MRCC/SRCC is")
    L.append("  flagged clock-capable and vice versa; bank suffixes match the bank column 48/48.")
    L.append("- The auditor's independent recall of the master XDC agrees 48/48 on pio->pkg-pin and")
    L.append("  IO-name. (Caveat: correlated recall from shared training data is weak corroboration -")
    L.append("  this is why the live fetch remains required.)")
    L.append("- **Discrepancy RESOLVED**: the T-008 clock-capable list in `docs/pdm-capture-contract.md`")
    L.append("  (pio3,5,8,18,19,36,37,38,40,43,46,47,48) is corrupt: pio46/47/48 are the DIP power")
    L.append("  positions (the master XDC GPIO section stops at pio44; the Cmod A7 has exactly 44 user")
    L.append("  I/O on the DIP), so that list's contested entries (pio18/19/37/38/40) lose authority.")
    L.append("  The clock-capable set is the IO-name-derived one: pio3,5,8,16,17 (banks 16/35) and")
    L.append("  pio32,33,34,36,39,42,43,44 (bank 34). `docs/pdm-capture-contract.md` has been corrected.")
    L.append("- **No net assignment changed**: all three clock-critical nets sit on pins both sources")
    L.append("  agreed on (`PDM_CLK_FB`=pio36 MRCC_34, `FT_CLKOUT`=pio43 SRCC_34, `ETH_REF_CLK`=pio3")
    L.append("  MRCC_16), so the resolution cannot perturb the design.")
    L.append("")
    L.append("**Still outstanding (blocks T-020 synthesis, ~60 s for a human with a browser)**: fetch")
    L.append("https://github.com/Digilent/digilent-xdc/blob/master/Cmod-A7-Master.xdc and the Cmod A7")
    L.append("reference manual pinout table; confirm the 48-row table, the DIP-position<->pio identity")
    L.append("mapping, and the power-pin positions (45=GND, 46=3V3, 47=VU, 48=GND).")
    L.append("")
    L.append("## Budget summary")
    L.append("")
    L.append("| Group | Nets | Pins |")
    L.append("|---|---|---|")
    L.append("| PDM array | PDM_D0..11, PDM_CLK_SRC, PDM_CLK_EN, PDM_CLK_FB | 15 |")
    L.append("| FT232H sync FIFO | FT_D0..7, FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N, FT_OE_N, FT_CLKOUT | 14 |")
    L.append("| RMII DNP provision | ETH_TXD0/1, ETH_TX_EN, ETH_RXD0/1, ETH_CRS_DV, ETH_RX_ER, ETH_REF_CLK, ETH_MDC, ETH_MDIO | 10 |")
    L.append("| TX control | TX_EN, TX_PH, TX_NSLEEP, TX_NFAULT, TX_PMODE | 5 |")
    L.append("| **Total DIP I/O** | | **44 / 44** |")
    L.append("| Spare | none on DIP; on-module Pmod JA (8 I/O, bank 14) + on-module LEDs/BTN remain free | |")
    L.append("")
    L.append("Bank usage (all banks fixed at VCCO = 3.3 V on the Cmod A7; LVCMOS33 everywhere):")
    L.append("bank 35 = pio1,2,4,6,10-21 (16 pins: PDM data + TX_EN/TX_PH + ETH_MDC/MDIO);")
    L.append("bank 16 = pio3,5,7,8,9 (5 pins: ETH_REF_CLK, PDM_CLK_SRC/EN, TX_NFAULT/PMODE);")
    L.append("bank 34 = pio22-44 (23 pins: FT232H + RMII + PDM_CLK_FB + TX_NSLEEP).")
    L.append("")
    L.append("## The pin table")
    L.append("")
    L.append("| pio | DIP pin | pkg pin* | IO name* | Bank | Clock-capable | Net | FPGA dir | Notes |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for p in PINS:
        cc = {"yes": "YES", "": ""}[p[5]]
        L.append(f"| {p[0]} | {p[1]} | {p[2]} | {p[3]} | {p[4] if p[4] else '-'} | {cc} | `{p[6]}` | {p[7]} | {p[9]} |")
    L.append("")
    L.append("\\* pkg pin / IO name: offline transcription, second-agent-audited offline 2026-08-26;")
    L.append("  **live master-XDC diff still required before T-020 synthesis.**")
    L.append("")
    L.append("## On-module resources (not on the DIP socket)")
    L.append("")
    L.append("| Signal | pkg pin* | IO name* | Note |")
    L.append("|---|---|---|---|")
    for s in ONMODULE:
        L.append(f"| {s[0]} | {s[1]} | {s[2]} | {s[4]} |")
    L.append("")
    L.append("Pmod JA (bank 14, on module, free for debug/expansion): " +
             ", ".join(f"{a}={b}" for a, b, _ in PMOD_JA) + ".")
    L.append("")
    L.append("## Board-level decisions (ratified within T-011 scope)")
    L.append("")
    L.append("1. **Power strategy**: Cmod A7 self-powered from its own micro-USB; board and module")
    L.append("   share GND only. `CMOD_3V3`/`CMOD_VU` socket pins are no-connect by default;")
    L.append("   SJ1/SJ2 (DNP solder jumpers) are rework options to tie module 3V3<->board +3.3V or")
    L.append("   VU<->board 5V, to be fitted only with T-012 review. FT232H breakout self-powered")
    L.append("   from its own USB (its 5V pin is NC). Pico 2 self-powered.")
    L.append("2. **Contention rule**: exactly one capture platform at a time - Cmod in J40 *or*")
    L.append("   Pico 2 ribbon on J42, never both (both drive PDM_CLK_SRC/PDM_CLK_EN).")
    L.append("3. **Clock architecture**: FPGA generates PDM_CLK_SRC (MMCM from on-module 12 MHz;")
    L.append("   3.072 MHz v1, parameterized for the 4.8 MHz ICS alternate); CDCLVC1112 on the array")
    L.append("   sheet returns PDM_CLK_FB on clock-capable pio36; the IDDR samples from the returned")
    L.append("   clock per the capture contract. PDM data lines pio10-21 sit together on bank 35.")
    L.append("4. **DNP Ethernet**: LAN8720A + HR911105A MagJack + 50 MHz osc on 10 spare pins;")
    L.append("   strap-resistor values deferred to populate time (Artix-7 config-time pull-ups can")
    L.append("   override PHY internal strap pulls).")
    L.append("5. **PDM data line mapping follows the capture contract exactly** (D0=CH00/CH01=M00/M10")
    L.append("   ... D11=CH22/CH23=M43/M44); T-020 may not renumber channels.")
    L.append("")
    L.append("## Cross-sheet net inventory (global labels on `digital.kicad_sch`)")
    L.append("")
    L.append("- To array sheet (T-010): `PDM_D0..11`, `PDM_CLK_SRC`, `PDM_CLK_EN`, `PDM_CLK_FB`.")
    L.append("- To TX sheet (T-013): `TX_EN`, `TX_PH`, `TX_NSLEEP`, `TX_NFAULT`, `TX_PMODE`.")
    L.append("- To power tree (T-012): `+3.3V` (power symbol), `GND`, `5V` (SJ2 option),")
    L.append("  `CMOD_3V3`, `CMOD_VU` (SJ options).")
    L.append("- DNP-internal: `ETH_VDDCR`, `ETH_RBIAS`, `ETH_RST_N`, `ETH_INTSEL`, `ETH_REGOFF`,")
    L.append("  `ETH_RCT`, `ETH_TXP/N`, `ETH_RXP/N`.")
    open(path, 'w').write('\n'.join(L) + '\n')

# ---------------------------------------------------------------------------
def main():
    os.makedirs(os.path.join(ROOT, "gateware", "constraints"), exist_ok=True)
    sh = build()
    sch = os.path.join(ROOT, "sonar-v1-pcb", "digital.kicad_sch")
    sh.write(sch)
    print(f"wrote {sch}: {len(sh.symbols)} symbols, {len(sh.items)} items, {len(sh.libs)} lib symbols")
    write_xdc(os.path.join(ROOT, "gateware", "constraints", "sonar_cmod_a7.xdc"))
    print("wrote gateware/constraints/sonar_cmod_a7.xdc")
    write_pinmap(os.path.join(ROOT, "orchestration", "pinmap.md"))
    print("wrote orchestration/pinmap.md")
    stats = patch_top_sheet()
    print("patched sonar-v1-pcb/sonar.kicad_sch")

if __name__ == "__main__":
    main()
