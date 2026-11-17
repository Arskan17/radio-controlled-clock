#!/usr/bin/env python3
"""Generate the KUPONG documentation SVGs in this folder.

    python3 docs/img/generate.py

Plain SVG + inline CSS only (no scripts, no web fonts) so GitHub renders
them, including the CSS animation and light/dark mode.
"""
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent

STYLE = """
svg{--bg:#f6f8fa;--surface:#ffffff;--ink:#1f2328;--muted:#59636e;--line:#57606a;
--board:#dcebd6;--boardline:#6d9a62;--copper:#b8732e;--blue:#1f6f9f;--yellow:#9a7300;
--glow:#DFB548;--lcd:#c9d1c1;--lcdink:#1c2418;--cob:#111;--metal:#b9c0c8;--brass:#c9a227}
@media (prefers-color-scheme: dark){svg{--bg:#0d1117;--surface:#161b22;--ink:#e6edf3;
--muted:#9198a1;--line:#8b949e;--board:#173022;--boardline:#3f7a4f;--copper:#d39a52;
--blue:#7FC4E7;--yellow:#DFB548;--lcd:#2b3328;--lcdink:#dce8d2;--cob:#050505;--metal:#8d959e;--brass:#a8862a}}
.bg{fill:var(--bg)}
.surface{fill:var(--surface);stroke:var(--line);stroke-width:1.5}
text{font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;fill:var(--ink);font-size:14px}
.title{font-size:20px;font-weight:700}
.muted{fill:var(--muted)}
.small{font-size:12px}
.bold{font-weight:700}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.blue{fill:var(--blue)}
.wire{stroke:var(--line);stroke-width:2;fill:none}
.trace{stroke:var(--copper);stroke-width:2.5;fill:none;stroke-linecap:round;stroke-linejoin:round}
.copper{fill:var(--copper)}
.board{fill:var(--board);stroke:var(--boardline);stroke-width:2}
.tp circle{fill:var(--glow);stroke:var(--bg);stroke-width:2}
.tp text{font-weight:700;font-size:14px;fill:#1f2328;text-anchor:middle}
.opt{stroke:var(--yellow);stroke-width:2;stroke-dasharray:6 5;fill:none}
.dot{fill:var(--line)}
"""


def svg(w, h, body, title, desc, extra_style=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-labelledby="t d">
<title id="t">{title}</title>
<desc id="d">{desc}</desc>
<style>{STYLE}{extra_style}</style>
<rect class="bg" width="{w}" height="{h}" rx="12"/>
{body}
</svg>
"""


def tp(x, y, n):
    return f'<g class="tp"><circle cx="{x}" cy="{y}" r="13"/><text x="{x}" y="{y + 5}">{n}</text></g>'


def comb_pad(cx, cy, r=26):
    """Interdigitated (carbon/gold) button contact, as on cheap rubber-dome buttons."""
    s = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="var(--copper)" stroke-width="2.5"/>']
    xl, xr = cx - r * 0.72, cx + r * 0.72
    top, step = cy - r * 0.6, r * 0.3
    s.append(f'<line class="trace" x1="{xl:.1f}" y1="{top:.1f}" x2="{xl:.1f}" y2="{top + 4 * step:.1f}"/>')
    s.append(f'<line class="trace" x1="{xr:.1f}" y1="{top:.1f}" x2="{xr:.1f}" y2="{top + 4 * step:.1f}"/>')
    for i in range(5):
        y = top + i * step
        if i % 2 == 0:
            s.append(f'<line class="trace" x1="{xl:.1f}" y1="{y:.1f}" x2="{cx + r * 0.42:.1f}" y2="{y:.1f}"/>')
        else:
            s.append(f'<line class="trace" x1="{cx - r * 0.42:.1f}" y1="{y:.1f}" x2="{xr:.1f}" y2="{y:.1f}"/>')
    return "\n".join(s)


# ---------------------------------------------------------------- 1. board
def board():
    b = []
    b.append('<text class="title" x="24" y="38">KUPONG: inside the €1 alarm clock</text>')
    b.append('<text class="muted" x="24" y="60">Representative layout of a typical €1 LCD clock. '
             'Check it against your own board before cutting or soldering.</text>')
    # PCB
    b.append('<rect class="board" x="40" y="80" width="560" height="460" rx="18"/>')
    # LCD glass (sits in front of the board)
    b.append('<rect x="80" y="100" width="480" height="150" rx="8" fill="var(--lcd)" stroke="var(--line)" stroke-dasharray="6 4"/>')
    b.append('<text class="mono" x="320" y="208" text-anchor="middle" style="font-size:96px;font-weight:700;fill:var(--lcdink)">12:00</text>')
    b.append('<text class="mono" x="128" y="232" style="font-size:16px;font-weight:700;fill:var(--lcdink)">AL</text>')
    b.append('<path d="M505 220 q0 -16 10 -16 q10 0 10 16 l4 5 h-28 z M512 228 a3 3 0 0 0 6 0" fill="var(--lcdink)"/>')
    b.append('<text class="small muted" x="92" y="120">LCD glass (front): 4 digits, colon, AL, bell</text>')
    # zebra strip
    b.append('<defs><pattern id="zebra" width="6" height="14" patternUnits="userSpaceOnUse">'
             '<rect width="3" height="14" fill="var(--line)"/><rect x="3" width="3" height="14" fill="var(--surface)"/></pattern></defs>')
    b.append('<rect x="110" y="256" width="420" height="14" fill="url(#zebra)" stroke="var(--line)"/>')
    # LCD pads + fan-out traces to the COB
    cob_x, cob_y, cob_r = 320, 380, 42
    for i in range(24):
        px = 116 + i * 17.5
        b.append(f'<rect class="copper" x="{px - 4:.1f}" y="274" width="8" height="10"/>')
        # aim at a point on the COB rim
        ang = math.pi + (i / 23) * math.pi  # left .. right along the top half
        ex, ey = cob_x + cob_r * math.cos(ang), cob_y + cob_r * math.sin(ang)
        b.append(f'<polyline class="trace" style="stroke-width:1.4" points="{px:.1f},284 {px:.1f},300 {ex:.1f},{ey:.1f}"/>')
    b.append('<text class="small muted" x="536" y="268">zebra strip</text>')
    # COB
    b.append(f'<circle cx="{cob_x}" cy="{cob_y}" r="{cob_r}" fill="var(--cob)" stroke="var(--line)"/>')
    b.append(f'<text x="{cob_x}" y="{cob_y + 5}" text-anchor="middle" class="small bold" style="fill:#e6edf3">clock IC</text>')
    b.append(f'<text x="{cob_x}" y="{cob_y + 62}" text-anchor="middle" class="small muted">COB (chip under epoxy blob)</text>')
    # crystal
    b.append('<rect x="408" y="352" width="16" height="50" rx="8" fill="var(--metal)" stroke="var(--line)"/>')
    b.append('<line class="trace" x1="416" y1="402" x2="416" y2="412"/><line class="trace" x1="416" y1="412" x2="362" y2="392"/>')
    b.append('<line class="trace" x1="410" y1="352" x2="360" y2="366"/>')
    b.append('<text class="small muted" x="432" y="372">32.768 kHz</text><text class="small muted" x="432" y="388">crystal</text>')
    # SMD caps
    b.append('<rect x="236" y="342" width="14" height="8" fill="#8a6a4a"/><rect x="196" y="398" width="14" height="8" fill="#8a6a4a"/>')
    # buzzer
    b.append('<circle cx="545" cy="440" r="36" fill="var(--brass)" stroke="var(--line)"/><circle cx="545" cy="440" r="22" fill="var(--surface)" stroke="var(--line)"/>')
    b.append('<text class="small" x="545" y="444" text-anchor="middle">piezo</text>')
    b.append('<polyline class="trace" points="515,420 470,410 362,384"/>')
    b.append('<polyline class="trace" points="520,466 480,500"/>')
    # buttons (contacts on the back side, pressed through the case)
    set_x, plus_x, by = 140, 230, 470
    b.append(comb_pad(set_x, by))
    b.append(comb_pad(plus_x, by))
    b.append(f'<text class="bold" x="{set_x}" y="{by + 48}" text-anchor="middle">SET</text>')
    b.append(f'<text class="bold" x="{plus_x}" y="{by + 48}" text-anchor="middle">+</text>')
    # signal traces: right comb -> COB
    b.append(f'<polyline class="trace" points="{set_x + 19},{by - 15} {set_x + 40},{by - 50} 286,402"/>')
    b.append(f'<polyline class="trace" points="{plus_x + 19},{by - 15} {plus_x + 30},{by - 40} 295,412"/>')
    # common (GND) traces: left comb -> GND rail -> BAT-
    b.append(f'<polyline class="trace" points="{set_x - 19},{by + 10} {set_x - 19},526 400,526 400,512"/>')
    b.append(f'<polyline class="trace" points="{plus_x - 19},{by + 10} {plus_x - 19},526"/>')
    # battery pads
    b.append('<rect class="copper" x="380" y="490" width="40" height="22" rx="3"/>')
    b.append('<rect class="copper" x="440" y="490" width="40" height="22" rx="3"/>')
    b.append('<text class="small bold" x="400" y="505" text-anchor="middle" style="fill:#1f2328">BAT−</text>')
    b.append('<text class="small bold" x="460" y="505" text-anchor="middle" style="fill:#1f2328">BAT+</text>')
    b.append('<polyline class="trace" points="460,490 460,470 352,400"/>')
    b.append('<line x1="400" y1="512" x2="400" y2="560" stroke="#555" stroke-width="4"/>')
    b.append('<line x1="460" y1="512" x2="460" y2="560" stroke="#c0392b" stroke-width="4"/>')
    b.append('<text class="small muted" x="476" y="556">to AAA holder (1.5 V)</text>')
    # tap points
    b.append(tp(set_x - 34, by - 34, 1))
    b.append(tp(plus_x + 44, by + 4, 2))
    b.append(tp(472, 482, 3))
    b.append(tp(368, 482, 4))
    b.append(tp(590, 398, 5))
    # legend
    lx = 630
    b.append(f'<rect class="surface" x="{lx}" y="80" width="306" height="460" rx="12"/>')
    b.append(f'<text class="bold" x="{lx + 20}" y="110">Tap points</text>')
    rows = [
        (1, "SET contacts", "→ optocoupler #1"),
        (2, "+ contacts", "→ optocoupler #2"),
        (3, "BAT+ (1.5 V)", "optional: ESP-switched 1.5 V"),
        (4, "BAT− (GND)", "optional: common ground"),
        (5, "Buzzer", "optional: detect alarm ringing"),
    ]
    y = 142
    for n, a, c in rows:
        b.append(tp(lx + 32, y - 5, n))
        b.append(f'<text x="{lx + 56}" y="{y - 6}" class="bold">{a}</text>')
        b.append(f'<text x="{lx + 56}" y="{y + 12}" class="small muted">{c}</text>')
        y += 50
    b.append(f'<text class="bold" x="{lx + 20}" y="{y + 12}">Original circuit</text>')
    notes = [
        "Clock IC under the epoxy blob counts",
        "the 32.768 kHz crystal (2¹⁵ Hz → 1 s)",
        "and drives the LCD segments through",
        "the zebra strip. Buttons pull an IC",
        "input to the common pad. All at 1.5 V.",
    ]
    for i, t in enumerate(notes):
        b.append(f'<text class="small muted" x="{lx + 20}" y="{y + 36 + i * 18}">{t}</text>')
    return svg(960, 580, "\n".join(b), "KUPONG board anatomy",
               "Representative top view of the KUPONG clock board: LCD with zebra strip, "
               "chip-on-board clock IC, 32.768 kHz crystal, SET and + button contacts, "
               "battery pads and piezo buzzer, with five numbered tap points.")


# ---------------------------------------------------------------- 2. wiring
def resistor(x, y, label):
    pts = [(x, y)]
    for i in range(6):
        pts.append((x + 8 + i * 8, y + (-7 if i % 2 == 0 else 7)))
    pts.append((x + 56, y))
    p = " ".join(f"{a},{b}" for a, b in pts)
    return (f'<polyline class="wire" points="{p}"/>'
            f'<text class="small muted" x="{x + 28}" y="{y - 12}" text-anchor="middle">{label}</text>')


def opto(x, y, label):
    """PC817: pin1 anode (x, y+20), pin2 cathode (x, y+60), pin4 collector (x+150, y+20), pin3 emitter (x+150, y+60)."""
    s = [f'<rect class="surface" x="{x}" y="{y}" width="150" height="80" rx="6"/>',
         f'<text class="small bold" x="{x + 75}" y="{y - 8}" text-anchor="middle">{label}</text>']
    # LED
    s.append(f'<polyline class="wire" points="{x},{y + 20} {x + 40},{y + 20} {x + 40},{y + 30}"/>')
    s.append(f'<polygon points="{x + 30},{y + 30} {x + 50},{y + 30} {x + 40},{y + 48}" fill="var(--glow)" stroke="var(--line)"/>')
    s.append(f'<line class="wire" x1="{x + 30}" y1="{y + 48}" x2="{x + 50}" y2="{y + 48}"/>')
    s.append(f'<polyline class="wire" points="{x + 40},{y + 48} {x + 40},{y + 60} {x},{y + 60}"/>')
    # light arrows
    for dy in (34, 44):
        s.append(f'<line x1="{x + 58}" y1="{y + dy}" x2="{x + 82}" y2="{y + dy}" stroke="var(--glow)" stroke-width="2"/>'
                 f'<polygon points="{x + 82},{y + dy - 4} {x + 90},{y + dy} {x + 82},{y + dy + 4}" fill="var(--glow)"/>')
    # phototransistor
    s.append(f'<line class="wire" x1="{x + 100}" y1="{y + 28}" x2="{x + 100}" y2="{y + 52}" style="stroke-width:3"/>')
    s.append(f'<polyline class="wire" points="{x + 100},{y + 34} {x + 120},{y + 20} {x + 150},{y + 20}"/>')
    s.append(f'<polyline class="wire" points="{x + 100},{y + 46} {x + 120},{y + 60} {x + 150},{y + 60}"/>')
    s.append(f'<polygon points="{x + 113},{y + 51} {x + 120},{y + 60} {x + 109},{y + 58}" fill="var(--line)"/>')
    for px, py, n in ((x - 12, y + 16, 1), (x - 12, y + 72, 2), (x + 156, y + 16, 4), (x + 156, y + 72, 3)):
        s.append(f'<text class="small muted" x="{px}" y="{py}">{n}</text>')
    return "\n".join(s)


def wiring():
    b = []
    b.append('<text class="title" x="24" y="38">Modification: the ESP32-C3 presses the buttons through optocouplers</text>')
    b.append('<text class="muted" x="24" y="60">Each PC817 shorts one button contact pair like a finger would. '
             'The 3.3 V ESP never touches the 1.5 V clock chip.</text>')
    # ESP
    b.append('<rect class="surface" x="40" y="90" width="200" height="370" rx="10"/>')
    b.append('<text class="bold" x="60" y="118">ESP32-C3</text><text class="small muted" x="60" y="136">SuperMini, USB-C 5 V</text>')
    pins = [("GPIO3  SET", 210), ("GPIO4  +", 330), ("GPIO5  PWR", 400), ("GND", 440)]
    for name, y in pins:
        b.append(f'<text class="small mono" x="228" y="{y + 4}" text-anchor="end">{name}</text>')
        b.append(f'<circle class="dot" cx="240" cy="{y}" r="4"/>')
    # SET channel
    b.append('<line class="wire" x1="240" y1="210" x2="290" y2="210"/>' + resistor(290, 210, "R1 1 kΩ") +
             '<line class="wire" x1="346" y1="210" x2="420" y2="210"/>')
    b.append(opto(420, 190, "PC817 #1 (SET)"))
    # + channel
    b.append('<line class="wire" x1="240" y1="330" x2="290" y2="330"/>' + resistor(290, 330, "R2 1 kΩ") +
             '<line class="wire" x1="346" y1="330" x2="420" y2="330"/>')
    b.append(opto(420, 310, "PC817 #2 (+)"))
    # cathodes -> GND rail
    b.append('<polyline class="wire" points="420,250 390,250 390,440"/><polyline class="wire" points="420,370 390,370"/>')
    b.append('<circle class="dot" cx="390" cy="370" r="4"/><circle class="dot" cx="390" cy="440" r="4"/>')
    b.append('<line class="wire" x1="240" y1="440" x2="390" y2="440"/>')
    # KUPONG side
    b.append('<rect class="board" x="690" y="90" width="246" height="370" rx="14"/>')
    b.append('<text class="bold" x="710" y="118">KUPONG board</text>')
    b.append('<text class="small muted" x="710" y="136">original electronics stay in place</text>')
    for cy, name, n in ((230, "SET", 1), (350, "+", 2)):
        b.append(comb_pad(820, cy))
        b.append(f'<text class="bold" x="864" y="{cy + 5}">{name}</text>')
        b.append(tp(886, cy - 26, n))
    # collector -> signal pad, emitter -> common pad
    for base in (190, 310):
        b.append(f'<polyline class="wire" points="570,{base + 20} 760,{base + 20} 760,{base + 30} 801,{base + 30}"/>')
        b.append(f'<polyline class="wire" points="570,{base + 60} 850,{base + 60} 850,{base + 40} 839,{base + 40}"/>')
        b.append(f'<text class="small muted" x="590" y="{base + 14}">C → signal pad</text>')
        b.append(f'<text class="small muted" x="590" y="{base + 78}">E → common pad</text>')
    # battery pads + optional power path
    b.append('<rect class="copper" x="740" y="410" width="44" height="24" rx="3"/><rect class="copper" x="852" y="410" width="44" height="24" rx="3"/>')
    b.append('<text class="small bold" x="762" y="426" text-anchor="middle" style="fill:#1f2328">BAT−</text>')
    b.append('<text class="small bold" x="874" y="426" text-anchor="middle" style="fill:#1f2328">BAT+</text>')
    b.append(tp(722, 422, 4))
    b.append(tp(914, 400, 3))
    b.append('<polyline class="opt" points="390,440 390,470 762,470 762,434"/>')
    b.append('<polyline class="opt" points="240,400 268,400 268,500 470,500"/>')
    b.append('<rect class="surface" x="470" y="484" width="120" height="34" rx="6" style="stroke:var(--yellow)"/>')
    b.append('<text class="small bold" x="530" y="506" text-anchor="middle">1.5 V LDO</text>')
    b.append('<polyline class="opt" points="590,500 874,500 874,434"/>')
    b.append('<text class="small" x="40" y="548"><tspan class="bold" style="fill:var(--yellow)">- - - Option B</tspan>'
             '<tspan class="muted"> (no AAA): the ESP powers the clock (e.g. XC6206P152) and can power-cycle it to a known 0:00 state.</tspan></text>')
    b.append('<text class="small muted" x="40" y="568">Option A: keep the AAA; only the two optocouplers are wired, no common ground needed.</text>')
    return svg(960, 590, "\n".join(b), "KUPONG modification wiring",
               "Schematic: ESP32-C3 GPIO3 and GPIO4 each drive a PC817 optocoupler LED through 1 kilo-ohm; "
               "the optocoupler transistors are wired across the KUPONG SET and + button contacts. "
               "Optional: GPIO5 feeds a 1.5 V regulator to the battery pads.")


# ---------------------------------------------------------------- 3. animation
ANIM = """
.led{animation:led 8s infinite}
.ray{animation:led 8s infinite}
.hot{animation:hot 8s infinite}
.arm{transform-box:view-box;transform-origin:520px 128px;animation:arm 8s infinite}
.closed-label{animation:led 8s infinite}
.blink{animation:blink 1s steps(1) infinite}
.d06{animation:d06 8s infinite}.d07{animation:d07 8s infinite}.d08{animation:d08 8s infinite}.d09{animation:d09 8s infinite}
.playhead{animation:play 8s linear infinite}
@keyframes led{0%,12.4%{opacity:.12}12.5%,16.2%{opacity:1}16.3%,31.2%{opacity:.12}31.25%,34.9%{opacity:1}35%,49.9%{opacity:.12}50%,53.7%{opacity:1}53.8%,100%{opacity:.12}}
@keyframes hot{0%,12.4%{stroke:var(--line)}12.5%,16.2%{stroke:var(--glow)}16.3%,31.2%{stroke:var(--line)}31.25%,34.9%{stroke:var(--glow)}35%,49.9%{stroke:var(--line)}50%,53.7%{stroke:var(--glow)}53.8%,100%{stroke:var(--line)}}
@keyframes arm{0%,12.4%{transform:rotate(-32deg)}12.5%,16.2%{transform:rotate(0)}16.3%,31.2%{transform:rotate(-32deg)}31.25%,34.9%{transform:rotate(0)}35%,49.9%{transform:rotate(-32deg)}50%,53.7%{transform:rotate(0)}53.8%,100%{transform:rotate(-32deg)}}
@keyframes blink{0%{opacity:1}50%{opacity:.2}}
@keyframes d06{0%,12.4%{opacity:1}12.5%,100%{opacity:0}}
@keyframes d07{0%,12.4%{opacity:0}12.5%,31.2%{opacity:1}31.25%,100%{opacity:0}}
@keyframes d08{0%,31.2%{opacity:0}31.25%,49.9%{opacity:1}50%,100%{opacity:0}}
@keyframes d09{0%,49.9%{opacity:0}50%,100%{opacity:1}}
@keyframes play{from{transform:translateX(0)}to{transform:translateX(840px)}}
/* static frame (reduced motion): a press in progress, hours showing 07 */
.d06,.d08,.d09{opacity:0}
@media (prefers-reduced-motion: reduce){*{animation:none!important}.playhead{display:none}}
"""


def animation():
    b = []
    b.append('<text class="title" x="24" y="38">How one button press is injected</text>')
    b.append('<text class="muted" x="24" y="60">Clock in set mode, hours flashing. Each GPIO4 pulse = one press of “+”.</text>')
    # ESP
    b.append('<rect class="surface" x="40" y="88" width="170" height="110" rx="10"/>')
    b.append('<text class="bold" x="58" y="116">ESP32-C3</text><text class="small mono muted" x="58" y="140">GPIO4 → +</text>')
    b.append('<circle class="led" cx="190" cy="150" r="7" fill="var(--glow)"/>')
    b.append('<polyline class="wire hot" points="210,150 250,150"/>' + resistor(250, 150, "1 kΩ").replace('class="wire"', 'class="wire hot"') +
             '<polyline class="wire hot" points="306,150 340,150"/>')
    # opto
    b.append('<rect class="surface" x="340" y="88" width="230" height="110" rx="10"/>')
    b.append('<text class="small bold" x="455" y="80" text-anchor="middle">PC817 optocoupler</text>')
    b.append('<polygon class="led" points="372,128 404,128 388,156" fill="var(--glow)" stroke="var(--line)"/>')
    b.append('<line class="wire" x1="372" y1="156" x2="404" y2="156"/>')
    b.append('<polyline class="wire hot" points="340,150 356,150 356,120 388,120 388,128"/><polyline class="wire" points="388,156 388,180 356,180"/><text class="small muted" x="350" y="184" text-anchor="end">GND</text>')
    for dy in (134, 148):
        b.append(f'<g class="ray"><line x1="414" y1="{dy}" x2="452" y2="{dy}" stroke="var(--glow)" stroke-width="3"/>'
                 f'<polygon points="452,{dy - 5} 462,{dy} 452,{dy + 5}" fill="var(--glow)"/></g>')
    # switch: fixed contacts + rotating arm
    b.append('<circle class="dot" cx="520" cy="128" r="5"/><circle class="dot" cx="520" cy="172" r="5"/>')
    b.append('<line class="arm" x1="520" y1="128" x2="520" y2="172" stroke="var(--ink)" stroke-width="4" stroke-linecap="round"/>')
    b.append('<text class="small closed-label" x="535" y="154" style="fill:var(--yellow);font-weight:700">ON</text>')
    b.append('<polyline class="wire hot" points="520,128 520,110 600,110 600,128 620,128"/>')
    b.append('<polyline class="wire hot" points="520,172 520,186 600,186 600,172 620,172"/>')
    b.append('<text class="small muted" x="560" y="210" text-anchor="middle">across the + contacts</text>')
    # LCD
    b.append('<rect class="board" x="620" y="80" width="300" height="130" rx="12"/>')
    b.append('<rect x="640" y="98" width="260" height="94" rx="6" fill="var(--lcd)" stroke="var(--line)"/>')
    lcd = 'class="mono" style="font-size:64px;font-weight:700;fill:var(--lcdink)"'
    b.append('<g class="blink">' + "".join(
        f'<text class="mono d{v}" x="720" y="168" text-anchor="middle" style="font-size:64px;font-weight:700;fill:var(--lcdink)">{v}</text>'
        for v in ("06", "07", "08", "09")) + '</g>')
    b.append(f'<text {lcd} x="770" y="166" text-anchor="middle">:</text><text {lcd} x="830" y="168" text-anchor="middle">30</text>')
    b.append('<text class="small muted" x="770" y="230" text-anchor="middle">KUPONG LCD</text>')
    # timeline
    b.append('<rect class="surface" x="40" y="262" width="880" height="120" rx="10"/>')
    b.append('<text class="small mono muted" x="52" y="290">GPIO4</text>')
    x0, s = 80, 105  # px per second
    pts = [(x0, 350)]
    for t in (1.0, 2.5, 4.0):
        a, c = x0 + t * s, x0 + (t + 0.3) * s
        pts += [(a, 350), (a, 304), (c, 304), (c, 350)]
        b.append(f'<text class="small bold" x="{(a + c) / 2:.0f}" y="296" text-anchor="middle" style="fill:var(--yellow)">+</text>')
    pts.append((x0 + 8 * s, 350))
    b.append('<polyline points="' + " ".join(f"{a:.0f},{c}" for a, c in pts) + '" fill="none" stroke="var(--blue)" stroke-width="3"/>')
    for t in range(9):
        b.append(f'<text class="small muted" x="{x0 + t * s}" y="372" text-anchor="middle">{t}s</text>')
    b.append(f'<text class="small muted" x="{x0 + 5.0 * s}" y="330">… then SET → minutes, same way</text>')
    b.append(f'<line class="playhead" x1="{x0}" y1="276" x2="{x0}" y2="356" stroke="var(--ink)" stroke-width="2" stroke-dasharray="4 3"/>')
    b.append('<text class="small muted" x="40" y="408">Pulse ≈ 300 ms (tune to what the clock registers). The opto’s LED lights, its transistor conducts, and the clock sees a pressed button.</text>')
    return svg(960, 424, "\n".join(b), "Button press injection animation",
               "Animated: the ESP32 pulses GPIO4 three times; each pulse lights the optocoupler LED, "
               "closes its transistor across the + contacts, and the KUPONG hour digits step 06, 07, 08, 09.",
               ANIM)


if __name__ == "__main__":
    for name, fn in (("kupong-board.svg", board), ("kupong-wiring.svg", wiring),
                     ("kupong-press-animation.svg", animation)):
        (OUT / name).write_text(fn(), encoding="utf-8")
        print("wrote", OUT / name)
