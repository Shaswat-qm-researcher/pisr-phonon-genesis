#!/usr/bin/env python3
"""
Publication-quality phonon dispersion + atom-projected DOS
from symmetrized force constants.
 
Reads chemical formula from PRIMCELL.vasp (primitive cell) rather than POSCAR.
 
Input:  POSCAR           – unit cell for Phonopy (dynamics)
        PRIMCELL.vasp    – primitive cell  (formula extraction)
        FORCE_CONSTANTS  – interatomic force constants
        projected_dos.dat – atom-projected DOS (optional)
        KPATH.phonopy    – k-path definition
 
Output: phonon_dispersion_<formula>.pdf / .png
 
Usage:
    python plot_phonon_publication.py
    (DIM / NPOINTS / BAND / BAND_LABELS are read from KPATH.phonopy)
"""
 
import os
import re
import sys
from collections import OrderedDict
 
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import matplotlib.ticker as ticker
from matplotlib.gridspec import GridSpec
 
from phonopy import Phonopy
from phonopy.interface.vasp import read_vasp
from phonopy.file_IO import parse_FORCE_CONSTANTS
 
# ── Matplotlib global style for publication ───────────────────────────────────
plt.rcParams.update({
    'font.family'       : 'serif',
    'font.serif'        : ['DejaVu Serif', 'Times New Roman', 'Palatino'],
    'mathtext.fontset'  : 'dejavuserif',
    'axes.linewidth'    : 1.2,
    'xtick.major.width' : 1.2,
    'ytick.major.width' : 1.2,
    'xtick.minor.width' : 0.8,
    'ytick.minor.width' : 0.8,
    'xtick.direction'   : 'in',
    'ytick.direction'   : 'in',
    'pdf.fonttype'      : 42,   # embeds TrueType in PDF (required by most journals)
    'ps.fonttype'       : 42,
})
 
# ── Standard CPK/JMol colours ─────────────────────────────────────────────────
ATOM_FILL = {
    'H' :'#FFFFFF','He':'#D9FFFF',
    'Li':'#CC80FF','Be':'#C2FF00','B' :'#FF6B6B','C' :'#909090',
    'N' :'#3050F8','O' :'#FF0D0D','F' :'#90E050','Ne':'#B3E3F5',
    'Na':'#AB5CF2','Mg':'#8AFF00','Al':'#BFA6A6','Si':'#F0C8A0',
    'P' :'#FF8000','S' :'#FFFF30','Cl':'#1FF01F','Ar':'#80D1E3',
    'K' :'#8F40D4','Ca':'#3DFF00','Sc':'#E6E6E6','Ti':'#BFC2C7',
    'V' :'#A6A6AB','Cr':'#8A99C7','Mn':'#9C7AC7','Fe':'#E06633',
    'Co':'#F090A0','Ni':'#50D050','Cu':'#C88033','Zn':'#7D80B0',
}
ATOM_BORDER = {
    'H' :'#CCCCCC','He':'#A0DDDD',
    'Li':'#9955CC','Be':'#8FBB00','B' :'#CC3333','C' :'#606060',
    'N' :'#1A35CC','O' :'#CC0000','F' :'#60AA20','Ne':'#70BBDD',
    'Na':'#7A3FBF','Mg':'#60CC00','Al':'#8C7070','Si':'#C09060',
    'P' :'#CC5500','S' :'#CCCC00','Cl':'#00BB00','Ar':'#50A0BB',
    'K' :'#6020AA','Ca':'#25CC00','Sc':'#ABABAB','Ti':'#8A9099',
    'V' :'#77777D','Cr':'#5A6699','Mn':'#6A4A99','Fe':'#AA3300',
    'Co':'#C05070','Ni':'#209020','Cu':'#996010','Zn':'#4D5080',
}
 
# ─────────────────────────────────────────────────────────────────────────────
# HELPER: parse VASP POSCAR/PRIMCELL.vasp → ordered species dict
# ─────────────────────────────────────────────────────────────────────────────
def parse_vasp_species(filepath: str) -> OrderedDict:
    """
    Return OrderedDict {element: count} from any VASP5 POSCAR-format file.
    Handles both VASP5 (species on line 6) and VASP4 (counts only on line 6).
    """
    with open(filepath) as fh:
        lines = [l.rstrip('\n') for l in fh]
 
    # line 5 (0-indexed) → species OR counts depending on VASP version
    tok5 = lines[5].split()
    tok6 = lines[6].split() if len(lines) > 6 else []
 
    if tok5 and tok5[0].isalpha():          # VASP5: species names on line 6
        species = tok5
        counts  = [int(x) for x in tok6]
    else:                                   # VASP4: only counts; no species names
        raise ValueError(
            f"'{filepath}' appears to be a VASP4-format file (no species names). "
            "Please use a VASP5-format PRIMCELL.vasp."
        )
 
    if len(species) != len(counts):
        raise ValueError(
            f"Species/count mismatch in '{filepath}': "
            f"{species} vs {counts}"
        )
 
    return OrderedDict(zip(species, counts))
 
 
def formula_from_species(species: OrderedDict) -> str:
    """Compact formula string, e.g. B13CN."""
    return "".join(
        f"{sym}{cnt}" if cnt > 1 else sym
        for sym, cnt in species.items()
    )
 
 
# ─────────────────────────────────────────────────────────────────────────────
# KPATH.phonopy PARSER
# ─────────────────────────────────────────────────────────────────────────────
def _convert_label(tok: str) -> str:
    r"""Convert a phonopy BAND_LABELS token to a matplotlib mathtext string."""
    # Entirely inside $…$  e.g. "$\Gamma$"
    if tok.startswith('$') and tok.endswith('$') and tok.count('$') == 2:
        return tok
    # Mixed token like "H$_2$" or "S$_0$"
    m = re.match(r'^([^$]*)(\$.+\$)$', tok)
    if m:
        prefix = m.group(1)
        inner  = m.group(2).strip('$')
        if prefix:
            return r'$\mathrm{' + prefix + r'}' + inner + r'$'
        return r'$' + inner + r'$'
    return tok
 
 
def parse_kpath_file(filepath: str):
    """
    Parse KPATH.phonopy and return:
        band_path   : list of [q_start, q_end] pairs (fractional coords)
        all_labels  : flat list of all high-symmetry point labels
        npoints     : int, q-points per segment
        dim         : [3 ints], supercell dimensions
        symprec     : float
        panels      : list of panel dicts for plot layout
    """
    with open(filepath) as fh:
        content = re.sub(r'#.*', '', fh.read())
 
    def _get(key, default=''):
        m = re.search(rf'^\s*{key}\s*=\s*(.+)', content,
                      re.MULTILINE | re.IGNORECASE)
        return m.group(1).strip() if m else default
 
    npoints  = int(_get('NPOINTS', '101'))
    dim      = [int(x) for x in _get('DIM', '2 2 2').split()]
    symprec  = float(_get('SYMMETRY_TOLERANCE', _get('SYMPREC', '1e-5')))
    band_str = _get('BAND', '')
    label_str = _get('BAND_LABELS', '')
 
    assert len(dim) == 3, "DIM must contain exactly 3 integers."
 
    # ── Parse band path ──
    band_path, panels = [], []
    for pstr in [s.strip() for s in band_str.split(',')]:
        nums   = [float(x) for x in pstr.split()]
        if len(nums) % 3:
            raise ValueError(f"BAND triplet mismatch: '{pstr}'")
        points = [nums[i:i+3] for i in range(0, len(nums), 3)]
        if len(points) < 2:
            raise ValueError("BAND must have at least 2 points per group.")
        seg_indices = []
        for i in range(len(points) - 1):
            seg_indices.append(len(band_path))
            band_path.append([points[i], points[i+1]])
        panels.append({"segs": seg_indices, "labels": None})
 
    # ── Tokenise BAND_LABELS (respecting $…$ pairs) ──
    raw_toks, buf = [], ''
    for t in label_str.split():
        buf = (buf + ' ' + t).strip() if buf else t
        if buf.count('$') % 2 == 0:
            raw_toks.append(buf); buf = ''
    if buf:
        raw_toks.append(buf)
    labels = [_convert_label(t) for t in raw_toks]
 
    # ── Distribute labels across panels ──
    idx = 0
    for panel in panels:
        n = len(panel["segs"]) + 1
        panel["labels"] = (labels[idx:idx+n] + ['?'] * n)[:n]
        idx += n
 
    return band_path, labels, npoints, dim, symprec, panels
 
 
# ─────────────────────────────────────────────────────────────────────────────
# INTERACTIVE PROMPTS
# ─────────────────────────────────────────────────────────────────────────────
def prompt_dir(label: str, default: str = None) -> str:
    prompt = f"{label} [{default}]: " if default else f"{label}: "
    while True:
        val = input(prompt).strip() or default or ''
        val = os.path.expanduser(val)
        if os.path.isdir(val):
            return val
        print(f"  ✗ Not found: '{val}'. Try again.")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 62)
    print("   Phonon Dispersion Plotter  ·  Publication Quality")
    print("=" * 62)
 
    cwd = os.getcwd()
    input_dir  = prompt_dir("Input directory", default=cwd)
    output_dir = prompt_dir("Output directory", default=input_dir)
    os.makedirs(output_dir, exist_ok=True)
 
    # ── Required / optional file paths ──────────────────────────────────────
    paths = {
        'POSCAR'         : os.path.join(input_dir, 'POSCAR'),
        'PRIMCELL'       : os.path.join(input_dir, 'PRIMCELL.vasp'),
        'FORCE_CONSTANTS': os.path.join(input_dir, 'FORCE_CONSTANTS'),
        'KPATH'          : os.path.join(input_dir, 'KPATH.phonopy'),
        'PDOS'           : os.path.join(input_dir, 'projected_dos.dat'),
    }
 
    missing = [k for k in ('POSCAR','PRIMCELL','FORCE_CONSTANTS','KPATH')
               if not os.path.isfile(paths[k])]
    if missing:
        print("\n  ✗ Missing required file(s):")
        for k in missing:
            print(f"      – {paths[k]}")
        sys.exit(1)
 
    has_pdos = os.path.isfile(paths['PDOS'])
    for k, p in paths.items():
        if k == 'PDOS':
            status = ('✓' if has_pdos else
                      '✗  (PDOS panel will be skipped)')
        else:
            status = '✓'
        print(f"  {status}  {p}")
 
    # ── Read chemical formula from PRIMCELL.vasp ─────────────────────────────
    print(f"\nReading formula from PRIMCELL.vasp …")
    prim_species = parse_vasp_species(paths['PRIMCELL'])
    formula      = formula_from_species(prim_species)
    print(f"  ✓ Formula (from primitive cell): {formula}")
    print(f"  ✓ Species: { dict(prim_species) }")
 
    # ── Read k-path ──────────────────────────────────────────────────────────
    print(f"\nReading k-path from KPATH.phonopy …")
    BAND_PATH, all_labels, NPOINTS, DIM, SYMPREC, PANELS = \
        parse_kpath_file(paths['KPATH'])
    print(f"  ✓ DIM          : {DIM}")
    print(f"  ✓ NPOINTS/seg  : {NPOINTS}")
    print(f"  ✓ Segments     : {len(BAND_PATH)}")
    print(f"  ✓ Labels       : {all_labels}")
    print(f"  ✓ Plot panels  : {len(PANELS)}")
    for i, p in enumerate(PANELS):
        print(f"      Panel {i}: segs={p['segs']}  labels={p['labels']}")
 
    # ── Load structure & force constants ─────────────────────────────────────
    print("\nLoading structure and force constants …")
    unitcell = read_vasp(paths['POSCAR'])
    phonon   = Phonopy(unitcell, np.diag(DIM), symprec=SYMPREC)
    phonon.force_constants = parse_FORCE_CONSTANTS(paths['FORCE_CONSTANTS'])
 
    # Atom species from POSCAR (for PDOS column mapping)
    poscar_species = OrderedDict()
    for sym in unitcell.symbols:
        poscar_species[sym] = poscar_species.get(sym, 0) + 1
    print(f"  ✓ POSCAR atoms : { dict(poscar_species) }")
 
    # PDOS column mapping (col 0 = frequency; one column per atom)
    atom_col_ranges: dict = {}
    col = 1
    for sym, cnt in poscar_species.items():
        atom_col_ranges[sym] = (col, col + cnt)
        col += cnt
 
    n_ops = len(phonon.primitive_symmetry.symmetry_operations['rotations'])
    print(f"  ✓ FC shape     : {phonon.force_constants.shape}")
    print(f"  ✓ Symmetry ops : {n_ops}")
 
    print("\nSymmetrizing force constants …")
    phonon.symmetrize_force_constants()
    print("  Done.")
 
    # ── Compute band structure ────────────────────────────────────────────────
    print(f"\nComputing band structure ({NPOINTS} pts/segment) …")
    rec_lat  = np.linalg.inv(unitcell.cell).T
    seg_data = []
 
    for si, (q1, q2) in enumerate(BAND_PATH):
        q1, q2 = np.array(q1), np.array(q2)
        seg_len = np.linalg.norm((q2 - q1) @ rec_lat)
        qpoints = [(q1 + t/(NPOINTS-1) * (q2-q1)).tolist()
                   for t in range(NPOINTS)]
        phonon.run_qpoints(qpoints)
        freqs = phonon.get_qpoints_dict()['frequencies']
        x     = np.linspace(0, seg_len, NPOINTS)
        n_neg = int(np.sum(freqs < -0.5))
        if n_neg:
            print(f"  ⚠  Seg {si}: {n_neg} imaginary modes below −0.5 THz")
        seg_data.append({"x": x, "freqs": freqs, "width": seg_len})
 
    n_bands = seg_data[0]["freqs"].shape[1]
    all_f   = np.concatenate([s["freqs"].flatten() for s in seg_data])
    f_min, f_max = all_f.min(), all_f.max()
    print(f"\n  Frequency range : {f_min:.3f} → {f_max:.3f} THz")
 
    # y-axis limits: slight pad below zero (for imaginary modes), 8 % above max
    ylim = (min(-1.5, f_min * 1.05), round(f_max * 1.08, 1))
 
    # ── Load PDOS ────────────────────────────────────────────────────────────
    dos_species: OrderedDict = OrderedDict()
    freq_dos = dos_total = None
 
    if has_pdos:
        print(f"\nLoading projected_dos.dat …")
        try:
            raw      = np.loadtxt(paths['PDOS'], comments='#')
            freq_dos = raw[:, 0]
            for sym, (c0, c1) in atom_col_ranges.items():
                dos_species[sym] = raw[:, c0:c1].sum(axis=1)
            dos_total = sum(dos_species.values())
            print(f"  ✓ {len(freq_dos)} frequency points, "
                  f"{len(dos_species)} species")
        except Exception as exc:
            print(f"  ✗ Could not load PDOS ({exc}). Skipping.")
            has_pdos = False
 
    # ── Output file names ────────────────────────────────────────────────────
    out_pdf = os.path.join(output_dir, f"phonon_dispersion_{formula}.pdf")
    out_png = os.path.join(output_dir, f"phonon_dispersion_{formula}.png")
 
    # ─────────────────────────────────────────────────────────────────────────
    # FIGURE LAYOUT
    # ─────────────────────────────────────────────────────────────────────────
    panel_widths = [
        sum(seg_data[si]["width"] for si in p["segs"]) for p in PANELS
    ]
    min_w = 0.15 * max(panel_widths)
    panel_widths = [max(w, min_w) for w in panel_widths]
    dos_w  = 0.55 * max(panel_widths)
    ratios = panel_widths + ([dos_w] if has_pdos else [])
    n_cols = len(PANELS) + (1 if has_pdos else 0)
 
    BAND_COLOR = '#5A87E8'    # blue
    BOX_LW     = 1.2
    ZERO_COLOR = '#777777'
 
    fig = plt.figure(figsize=(9.4, 5.0))
    gs  = GridSpec(
        1, n_cols,
        width_ratios=ratios,
        wspace=0.18,
        left=0.09, right=0.97, top=0.87, bottom=0.09,
    )
 
    # ── Band panels ──────────────────────────────────────────────────────────
    band_axes = []
    for pi, panel in enumerate(PANELS):
        ax     = fig.add_subplot(gs[pi])
        offset = 0.0
        ticks  = []
 
        for i, si in enumerate(panel["segs"]):
            seg = seg_data[si]
            x   = seg["x"] + offset
            for b in range(n_bands):
                ax.plot(x, seg["freqs"][:, b],
                        color=BAND_COLOR, linewidth=1.6,
                        solid_capstyle='round',
                        zorder=2, rasterized=True)
            if i == 0:
                ticks.append(offset)
            end = offset + seg["width"]
 
            # vertical dashed dividers at interior high-sym points
            if i < len(panel["segs"]) - 1:
                ax.axvline(x=end, color='#999999',
                           linewidth=0.8, linestyle='--', zorder=1)
            ticks.append(end)
            offset = end
 
        ax.axhline(y=0, color=ZERO_COLOR, linewidth=1.0,
                   linestyle='--', alpha=0.85, zorder=3)
 
        ax.set_xlim(ticks[0], ticks[-1])
        ax.set_ylim(*ylim)
        ax.set_xticks(ticks)
 
        # High-symmetry label formatting
        labels_panel = panel["labels"]
        # Merge coincident endpoints between adjacent segments: done via ticks
        ax.set_xticklabels(labels_panel, fontsize=14, fontweight='bold')
        for lbl in ax.get_xticklabels():
            lbl.set_ha('center')
 
        # y-axis: left panel only
        if pi == 0:
            ax.set_ylabel("Frequency (THz)", fontsize=14, labelpad=6)
            ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=False, nbins=6))
        else:
            ax.tick_params(axis='y', labelleft=False)
 
        ax.tick_params(axis='both', direction='in', which='both',
                   labelsize=15, width=1.5, size=4, top=True, right=True)
 
        for sp in ax.spines.values():
            sp.set_linewidth(BOX_LW)
 
        band_axes.append(ax)
 
    # ── PDOS panel ───────────────────────────────────────────────────────────
    if has_pdos:
        ax_dos = fig.add_subplot(gs[len(PANELS)])
        mx = dos_total.max()
 
        # Total DOS (shaded background)
        dT = dos_total / mx
        ax_dos.fill_betweenx(freq_dos, 0, dT,
                             color='#CCCCCC', alpha=0.30, zorder=1)
        ax_dos.plot(dT, freq_dos,
                    color='#888888', linewidth=0.7, zorder=5)
 
        # Per-species projected DOS
        for sym, dos in dos_species.items():
            d        = dos / mx
            fill_c   = ATOM_FILL.get(sym,   '#AAAAAA')
            border_c = ATOM_BORDER.get(sym, '#555555')
            ax_dos.fill_betweenx(freq_dos, 0, d,
                                 color=fill_c, alpha=0.45, zorder=2)
            ax_dos.plot(d, freq_dos,
                        color=border_c, linewidth=1.0, zorder=6)
 
        ax_dos.axhline(y=0, color=ZERO_COLOR, linewidth=1.0,
                       linestyle='--', alpha=0.85, zorder=3)
        ax_dos.set_ylim(*ylim)
        ax_dos.set_xlim(0, 1.08)
        ax_dos.set_xlabel("Phonon PDOS", fontsize=14, labelpad=6)
        ax_dos.tick_params(axis='y', labelleft=False)
        ax_dos.tick_params(axis='x', which='major',
                           direction='in', width=1.2, length=6,
                           labelsize=14, top=True)
        ax_dos.set_xticks([0, 0.5, 1.0])
        ax_dos.set_xticklabels(['0', '0.5', '1'], fontsize=14)
        for sp in ax_dos.spines.values():
            sp.set_linewidth(BOX_LW)
 
    # ── Shared legend ────────────────────────────────────────────────────────
    legend_handles = [
        mlines.Line2D([], [], color=BAND_COLOR, linewidth=1.5,
                      label='Phonon bands'),
    ]
    if has_pdos:
        for sym in dos_species:
            legend_handles.append(
                mpatches.Patch(
                    facecolor=ATOM_FILL.get(sym, '#AAAAAA'),
                    edgecolor=ATOM_BORDER.get(sym, '#555555'),
                    linewidth=0.9, label=sym,
                )
            )
        legend_handles.append(
            mpatches.Patch(facecolor='#CCCCCC', edgecolor='#888888',
                           linewidth=0.9, label='Total')
        )
 
    fig.legend(
        handles=legend_handles,
        loc='upper center',
        bbox_to_anchor=(0.51, 1.00),
        ncol=len(legend_handles),
        fontsize=16,
        frameon=True,
        framealpha=0.92,
        edgecolor='black',
        fancybox=True,
        handlelength=1.4,
        handleheight=0.9,
        handletextpad=0.5,
        columnspacing=1.0,
    )
 
    # ── Save ─────────────────────────────────────────────────────────────────
    print(f"\nSaving …")
    for path in (out_pdf, out_png):
        dpi = 600 if path.endswith('.png') else 300
        fig.savefig(path, dpi=dpi, bbox_inches='tight')
        print(f"  ✓ {path}")
 
    plt.close(fig)
    print("\nDone. ✓")
    print("=" * 62)
 
 
if __name__ == "__main__":
    main()