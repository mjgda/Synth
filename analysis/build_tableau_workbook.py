"""Generate a Tableau packaged workbook (.twbx) for the market-share data.

Usage:  python analysis/build_tableau_workbook.py

Reads   tableau/market_share_tableau.csv   (run analysis/build_dashboard.py first)
Writes  tableau/Four-Brand Share Monitor.twbx

The workbook XML follows the structure of workbooks saved by Tableau 2019-2026. It was written
without access to Tableau, so it has only been checked for structure here.
Share calculations use FIXED level-of-detail expressions, so they need no table-calculation settings.
"""
from __future__ import annotations

import uuid
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "tableau" / "market_share_tableau.csv"
OUT = ROOT / "tableau" / "Four-Brand Share Monitor.twbx"
TWB_NAME = "Four-Brand Share Monitor.twb"
DATA_DIR = "Data/market_share"
DS = "federated.0mk7shr4m0n1t0r5yn7h3t1c00"
DS_CAPTION = "market_share_tableau"
TEXT_CONN = "textscan.1mk7shr4c5v0000000000000000"

BRAND_COLORS = {"Valley Central": "#2a78d6", "Neptune": "#eb6834", "Cornfield": "#1baf7a", "Barefoot": "#eda100"}
TIER_COLORS = {"Rail": "#e87ba4", "Call": "#008300", "Premium": "#6250d6", "Top Shelf": "#e34948"}


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace("'", "&apos;").replace('"', "&quot;").replace("\n", "&#10;"))


def uid() -> str:
    return "{" + str(uuid.uuid4()).upper() + "}"


# ---- source columns: (name, datatype, role, type, remote-type, aggregation, extra attrs) ----------
BASE = [
    ("Month Date", "date", "dimension", "ordinal", 133, "Year", ""),
    ("Interval", "string", "dimension", "nominal", 129, "Count", ""),
    ("Year", "integer", "dimension", "ordinal", 20, "Sum", ""),
    ("Month Num", "integer", "dimension", "ordinal", 20, "Sum", ""),
    ("Half", "string", "dimension", "nominal", 129, "Count", ""),
    ("Partial Year", "string", "dimension", "nominal", 129, "Count", ""),
    ("Manufacturer", "string", "dimension", "nominal", 129, "Count", ""),
    ("Brand Order", "integer", "dimension", "ordinal", 20, "Sum", ""),
    ("Product", "string", "dimension", "nominal", 129, "Count", ""),
    ("Tier Order", "integer", "dimension", "ordinal", 20, "Sum", ""),
    ("State", "string", "dimension", "nominal", 129, "Count", " semantic-role='[State].[Name]'"),
    ("Region", "string", "dimension", "nominal", 129, "Count", ""),
    ("Units", "integer", "measure", "quantitative", 20, "Sum", ""),
    ("Units Year Earlier", "integer", "measure", "quantitative", 20, "Sum", ""),
]
BASE_BY_NAME = {b[0]: b for b in BASE}

# ---- calculated fields: key -> (caption, datatype, role, type, formula, default-format) -------------
C = {k: f"Calculation_{n}" for k, n in [
    ("mkt", 7310000000000000001), ("mkt_py", 7310000000000000002), ("tier_tot", 7310000000000000003),
    ("share", 7310000000000000004), ("tier_share", 7310000000000000005), ("chg", 7310000000000000006),
    ("low", 7310000000000000007), ("chg_safe", 7310000000000000008), ("mkt_fx", 7310000000000000009),
    ("sh_fx", 7310000000000000010), ("share_chg", 7310000000000000011), ("units_cmp", 7310000000000000012),
    ("mkt_cmp", 7310000000000000013), ("low_label", 7310000000000000014)]}
CALCS = {
    "units_cmp": ("Units (comparable)", "integer", "measure", "quantitative",
                  "IF NOT ISNULL([Units Year Earlier]) THEN [Units] END", None),
    "mkt": ("Market Units (all brands)", "integer", "measure", "quantitative",
            "{FIXED [Month Date], [Product], [State] : SUM([Units])}", None),
    "mkt_py": ("Market Units Year Earlier", "integer", "measure", "quantitative",
               "{FIXED [Month Date], [Product], [State] : SUM([Units Year Earlier])}", None),
    "mkt_cmp": ("Market Units (comparable)", "integer", "measure", "quantitative",
                f"IF NOT ISNULL([Units Year Earlier]) THEN [{C['mkt']}] END", None),
    "tier_tot": ("Units All Tiers", "integer", "measure", "quantitative",
                 "{FIXED [Month Date], [Manufacturer], [State] : SUM([Units])}", None),
    "share": ("Brand Share", "real", "measure", "quantitative",
              f"SUM([Units]) / SUM([{C['mkt']}])", "p0.0%"),
    "tier_share": ("Tier Share", "real", "measure", "quantitative",
                   f"SUM([Units]) / SUM([{C['tier_tot']}])", "p0.0%"),
    "chg": ("Units Change %", "real", "measure", "quantitative",
            f"IF SUM([Units Year Earlier]) > 0 THEN SUM([{C['units_cmp']}]) / SUM([Units Year Earlier]) - 1 END", "p0.0%"),
    "low": ("Low Volume", "boolean", "measure", "nominal",
            f"SUM([{C['units_cmp']}]) < [Parameters].[Parameter 1] OR SUM([Units Year Earlier]) < [Parameters].[Parameter 1]", None),
    "low_label": ("Below Min Label", "string", "measure", "nominal",
                  f'IF [{C["low"]}] THEN "below min" END', None),
    "chg_safe": ("Units Change % (safe)", "real", "measure", "quantitative",
                 f"IF NOT [{C['low']}] THEN [{C['chg']}] END", "p0.0%"),
    "mkt_fx": ("Market Effect", "real", "measure", "quantitative",
               f"(SUM([{C['mkt_cmp']}]) - SUM([{C['mkt_py']}])) * SUM([Units Year Earlier]) / SUM([{C['mkt_py']}])", "n#,##0"),
    "sh_fx": ("Share Effect", "real", "measure", "quantitative",
              f"SUM([{C['mkt_cmp']}]) * (SUM([{C['units_cmp']}]) / SUM([{C['mkt_cmp']}]) - SUM([Units Year Earlier]) / SUM([{C['mkt_py']}]))", "n#,##0"),
    "share_chg": ("Share Change (pts)", "real", "measure", "quantitative",
                  f"SUM([{C['units_cmp']}]) / SUM([{C['mkt_cmp']}]) - SUM([Units Year Earlier]) / SUM([{C['mkt_py']}])", "p0.0%"),
}
CALC_DEPS = {
    "mkt": ["Month Date", "Product", "State", "Units"],
    "mkt_py": ["Month Date", "Product", "State", "Units Year Earlier"],
    "tier_tot": ["Month Date", "Manufacturer", "State", "Units"],
    "share": ["Units", "@mkt"], "tier_share": ["Units", "@tier_tot"],
    "units_cmp": ["Units", "Units Year Earlier"], "mkt_cmp": ["Units Year Earlier", "@mkt"],
    "chg": ["Units Year Earlier", "@units_cmp"], "low": ["Units Year Earlier", "@units_cmp", "#param"],
    "chg_safe": ["@low", "@chg"], "low_label": ["@low"], "mkt_fx": ["Units Year Earlier", "@mkt_cmp", "@mkt_py"],
    "sh_fx": ["Units Year Earlier", "@units_cmp", "@mkt_cmp", "@mkt_py"],
    "share_chg": ["Units Year Earlier", "@units_cmp", "@mkt_cmp", "@mkt_py"],
}
PARAM = ("<column caption='Min units for % change' datatype='integer' name='[Parameter 1]' param-domain-type='range' "
         "role='measure' type='quantitative' value='50'>\n"
         "        <calculation class='tableau' formula='50' />\n"
         "        <range granularity='50' max='10000' min='0' />\n"
         "      </column>")


def base_col_xml(name: str) -> str:
    n, dt, role, typ, _, _, extra = BASE_BY_NAME[name]
    return f"<column datatype='{dt}' name='[{esc(n)}]' role='{role}'{extra} type='{typ}' />"


def calc_col_xml(key: str) -> str:
    cap, dt, role, typ, formula, fmt = CALCS[key]
    f = f" default-format='{esc(fmt)}'" if fmt else ""
    return (f"<column caption='{esc(cap)}' datatype='{dt}'{f} name='[{C[key]}]' role='{role}' type='{typ}'>\n"
            f"              <calculation class='tableau' formula='{esc(formula)}' />\n"
            f"            </column>")


def closure(fields: list[str]) -> tuple[list[str], list[str], bool]:
    """Expand calc keys (prefixed @) to all base columns and calcs they depend on."""
    base, calcs, param = set(), set(), False
    stack = list(fields)
    while stack:
        f = stack.pop()
        if f == "#param":
            param = True
        elif f.startswith("@"):
            k = f[1:]
            if k not in calcs:
                calcs.add(k)
                stack.extend(CALC_DEPS[k])
        else:
            base.add(f)
    return sorted(base), [k for k in CALCS if k in calcs], param


# ---- column instances -------------------------------------------------------------------------
def inst(kind: str, field: str) -> tuple[str, str, str]:
    """Return (instance name, xml, base field or @calc)."""
    if field.startswith("@"):
        typ = CALCS[field[1:]][3]
        name = f"[usr:{C[field[1:]]}:{'nk' if typ == 'nominal' else 'qk'}]"
        return name, f"<column-instance column='[{C[field[1:]]}]' derivation='User' name='{name}' pivot='key' type='{typ}' />", field
    deriv, prefix, suffix, typ = {
        "none_nk": ("None", "none", "nk", "nominal"), "none_qk": ("None", "none", "qk", "quantitative"),
        "sum": ("Sum", "sum", "qk", "quantitative"), "tmn": ("Month-Trunc", "tmn", "qk", "quantitative"),
        "mn": ("Month", "mn", "ok", "ordinal"), "yr": ("Year", "yr", "ok", "ordinal"),
    }[kind]
    name = f"[{prefix}:{field}:{suffix}]"
    return name, f"<column-instance column='[{esc(field)}]' derivation='{deriv}' name='{esc(name)}' pivot='key' type='{typ}' />", field


def q(name: str) -> str:
    return f"[{DS}].{esc(name)}"


SHARED_FILTERS = [  # (instance kind, field, filter-group)
    ("none_qk", "Month Date", 2), ("none_nk", "Manufacturer", 3), ("none_nk", "Product", 4),
    ("none_nk", "Region", 5), ("none_nk", "State", 6),
]


def filters_xml() -> str:
    out = []
    for kind, field, grp in SHARED_FILTERS:
        name, _, _ = inst(kind, field)
        if kind == "none_qk":
            out.append(f"<filter class='quantitative' column='{q(name)}' filter-group='{grp}' included-values='in-range'>\n"
                       f"            <min>#2020-01-01#</min>\n            <max>#2026-06-01#</max>\n          </filter>")
        else:
            out.append(f"<filter class='categorical' column='{q(name)}' filter-group='{grp}'>\n"
                       f"            <groupfilter function='level-members' level='{esc(name)}' user:ui-enumeration='all' user:ui-marker='enumerate' />\n"
                       f"          </filter>")
    return "\n          ".join(out)


def worksheet(name: str, title: str, mark: str, rows: str = "", cols: str = "", encodings: list[tuple[str, str]] = (),
              instances: list[tuple[str, str]] = (), cell_formats: list[tuple[str, str]] = (), big_label: str | None = None,
              caption: str = "", is_map: bool = False) -> str:
    all_inst = list(instances) + [(k, f) for k, f, _ in SHARED_FILTERS]
    names, inst_xml, fields = {}, [], []
    for kind, field in all_inst:
        n, x, f = inst(kind, field)
        if n not in names:
            names[n] = True
            inst_xml.append(x)
            fields.append(f)
    base, calcs, param = closure(fields)
    deps = [base_col_xml(b) for b in base] + [calc_col_xml(k) for k in calcs] + inst_xml
    deps_xml = "\n            ".join(deps)
    param_ds = "\n            <datasource name='Parameters' />" if param else ""
    param_deps = (f"\n          <datasource-dependencies datasource='Parameters'>\n            {PARAM}\n          </datasource-dependencies>"
                  if param else "")
    mapsrc = "\n          <mapsources>\n            <mapsource name='Tableau' />\n          </mapsources>" if is_map else ""
    map_filters = ""
    slices = [q(inst(k, f)[0]) for k, f, _ in SHARED_FILTERS]
    if is_map:
        map_filters = (f"<filter class='quantitative' column='[{DS}].[Latitude (generated)]' included-values='non-null' />\n          "
                       f"<filter class='quantitative' column='[{DS}].[Longitude (generated)]' included-values='non-null' />\n          ")
        slices = [f"[{DS}].[Longitude (generated)]", f"[{DS}].[Latitude (generated)]"] + slices
    slices_xml = "\n            ".join(f"<column>{s}</column>" for s in slices)
    enc = "".join(f"\n              <{tag} column='{col}' />" for tag, col in encodings)
    enc_xml = f"\n            <encodings>{enc}\n            </encodings>" if encodings else ""
    label = ""
    if big_label:
        label = (f"\n            <customized-label>\n              <formatted-text>\n"
                 f"                <run fontcolor='#6b6f78' fontsize='10'>{esc(caption)}</run>\n                <run>Æ&#10;</run>\n"
                 f"                <run bold='true' fontsize='22'>&lt;</run>\n                <run bold='true' fontsize='22'>{big_label}</run>\n"
                 f"                <run bold='true' fontsize='22'>&gt;</run>\n              </formatted-text>\n            </customized-label>"
                 f"\n            <style>\n              <style-rule element='cell'>\n                <format attr='text-align' value='center' />\n"
                 f"              </style-rule>\n              <style-rule element='mark'>\n"
                 f"                <format attr='mark-labels-show' value='true' />\n              </style-rule>\n            </style>")
    fmt = "\n        <style />"
    if cell_formats:
        rules = "\n".join(f"            <format attr='text-format' field='{f}' value='{esc(v)}' />" for f, v in cell_formats)
        fmt = f"\n        <style>\n          <style-rule element='cell'>\n{rules}\n          </style-rule>\n        </style>"
    rows_xml = f"\n        <rows>{rows}</rows>" if rows else "\n        <rows />"
    cols_xml = f"\n        <cols>{cols}</cols>" if cols else "\n        <cols />"
    return f"""    <worksheet name='{esc(name)}'>
      <layout-options>
        <title>
          <formatted-text>
            <run bold='true'>{esc(title)}</run>
          </formatted-text>
        </title>
      </layout-options>
      <table>
        <view>
          <datasources>
            <datasource caption='{DS_CAPTION}' name='{DS}' />{param_ds}
          </datasources>{mapsrc}
          <datasource-dependencies datasource='{DS}'>
            {deps_xml}
          </datasource-dependencies>{param_deps}
          {map_filters}{filters_xml()}
          <slices>
            {slices_xml}
          </slices>
          <aggregation value='true' />
        </view>{fmt}
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='{mark}' />{enc_xml}{label}
          </pane>
        </panes>{rows_xml}{cols_xml}
      </table>
      <simple-id uuid='{uid()}' />
    </worksheet>"""


def build_worksheets() -> tuple[list[str], list[str]]:
    usr = lambda k: q(f"[usr:{C[k]}:qk]")
    sheets = [
        ("KPI Units", worksheet("KPI Units", "Units", "Text",
                                encodings=[("text", q("[sum:Units:qk]"))], instances=[("sum", "Units")],
                                big_label=q("[sum:Units:qk]"), caption="Units, selected brands and months")),
        ("KPI Change", worksheet("KPI Change", "Change vs a year earlier", "Text",
                                 encodings=[("text", usr("chg"))], instances=[("usr", "@chg")],
                                 big_label=usr("chg"), caption="Change vs a year earlier")),
        ("Brand Share", worksheet("Brand Share", "Brand share of units", "Line",
                                  rows=usr("share"), cols=q("[tmn:Month Date:qk]"),
                                  encodings=[("color", q("[none:Manufacturer:nk]"))],
                                  instances=[("usr", "@share"), ("tmn", "Month Date"), ("none_nk", "Manufacturer")])),
        ("Tier Mix", worksheet("Tier Mix", "Tier mix of units", "Line",
                               rows=usr("tier_share"), cols=q("[tmn:Month Date:qk]"),
                               encodings=[("color", q("[none:Product:nk]"))],
                               instances=[("usr", "@tier_share"), ("tmn", "Month Date"), ("none_nk", "Product")])),
        ("Change Drivers", worksheet("Change Drivers", "What drove the change: market size vs share", "Bar",
                                     rows=q("[none:Manufacturer:nk]"), cols=f"({usr('mkt_fx')} + {usr('sh_fx')})",
                                     encodings=[("color", q("[none:Manufacturer:nk]"))],
                                     instances=[("none_nk", "Manufacturer"), ("usr", "@mkt_fx"), ("usr", "@sh_fx")])),
        ("Seasonality", worksheet("Seasonality", "Seasonal curve by year", "Line",
                                  rows=q("[sum:Units:qk]"), cols=q("[mn:Month Date:ok]"),
                                  encodings=[("color", q("[yr:Month Date:ok]"))],
                                  instances=[("sum", "Units"), ("mn", "Month Date"), ("yr", "Month Date")])),
        ("State Map", worksheet("State Map", "Units by state", "Multipolygon",
                                rows=f"[{DS}].[Latitude (generated)]", cols=f"[{DS}].[Longitude (generated)]",
                                encodings=[("color", q("[sum:Units:qk]")), ("lod", q("[none:State:nk]")),
                                           ("geometry", f"[{DS}].[Geometry (generated)]")],
                                instances=[("sum", "Units"), ("none_nk", "State")], is_map=True)),
        ("Brand x Tier", worksheet("Brand x Tier", "Unit change by brand and tier, over units a year earlier", "Text",
                                   rows=q("[none:Manufacturer:nk]"), cols=q("[none:Product:nk]"),
                                   encodings=[("text", usr("chg_safe")), ("text", q(f"[usr:{C['low_label']}:nk]")),
                                              ("text", q("[sum:Units Year Earlier:qk]"))],
                                   instances=[("none_nk", "Manufacturer"), ("none_nk", "Product"), ("usr", "@chg_safe"),
                                              ("usr", "@low_label"), ("sum", "Units Year Earlier")],
                                   cell_formats=[(usr("chg_safe"), "p0.0%"), (q("[sum:Units Year Earlier:qk]"), "n#,##0")])),
    ]
    return [n for n, _ in sheets], [x for _, x in sheets]


def datasource_xml() -> str:
    cols = "\n".join(f"            <column datatype='{dt}' name='{esc(n)}' ordinal='{i}' />"
                     for i, (n, dt, *_rest) in enumerate(BASE))
    md = []
    for i, (n, dt, _role, _typ, rt, agg, _x) in enumerate(BASE):
        md.append(f"""          <metadata-record class='column'>
            <remote-name>{esc(n)}</remote-name>
            <remote-type>{rt}</remote-type>
            <local-name>[{esc(n)}]</local-name>
            <parent-name>[market_share_tableau.csv]</parent-name>
            <remote-alias>{esc(n)}</remote-alias>
            <ordinal>{i}</ordinal>
            <local-type>{dt}</local-type>
            <aggregation>{agg}</aggregation>
            <contains-null>true</contains-null>
          </metadata-record>""")
    base_cols = "\n      ".join(base_col_xml(n) for n, *_ in BASE)
    calc_cols = "\n      ".join(calc_col_xml(k).replace("\n            </column>", "\n      </column>")
                                .replace("\n              <calc", "\n        <calc") for k in CALCS)

    def palette(field: str, colors: dict) -> str:
        maps = "\n".join(f"            <map to='{c}'>\n              <bucket>&quot;{esc(v)}&quot;</bucket>\n            </map>"
                         for v, c in colors.items())
        return f"          <encoding attr='color' field='[none:{field}:nk]' type='palette'>\n{maps}\n          </encoding>"

    return f"""    <datasource hasconnection='false' inline='true' name='Parameters' version='18.1'>
      <aliases enabled='yes' />
      {PARAM}
    </datasource>
    <datasource caption='{DS_CAPTION}' inline='true' name='{DS}' version='18.1'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='{DS_CAPTION}' name='{TEXT_CONN}'>
            <connection class='textscan' directory='{DATA_DIR}' filename='market_share_tableau.csv' password='' server='' />
          </named-connection>
        </named-connections>
        <relation connection='{TEXT_CONN}' name='market_share_tableau.csv' table='[market_share_tableau#csv]' type='table'>
          <columns character-set='UTF-8' header='yes' locale='en_US' separator=','>
{cols}
          </columns>
        </relation>
        <metadata-records>
          <metadata-record class='capability'>
            <remote-name />
            <remote-type>0</remote-type>
            <parent-name>[market_share_tableau.csv]</parent-name>
            <remote-alias />
            <aggregation>Count</aggregation>
            <contains-null>true</contains-null>
            <attributes>
              <attribute datatype='string' name='character-set'>&quot;UTF-8&quot;</attribute>
              <attribute datatype='string' name='collation'>&quot;en_US&quot;</attribute>
              <attribute datatype='string' name='field-delimiter'>&quot;,&quot;</attribute>
              <attribute datatype='string' name='header-row'>&quot;true&quot;</attribute>
              <attribute datatype='string' name='locale'>&quot;en_US&quot;</attribute>
              <attribute datatype='string' name='single-char'>&quot;&quot;</attribute>
            </attributes>
          </metadata-record>
{chr(10).join(md)}
        </metadata-records>
      </connection>
      <aliases enabled='yes' />
      {base_cols}
      {calc_cols}
      <column-instance column='[Manufacturer]' derivation='None' name='[none:Manufacturer:nk]' pivot='key' type='nominal' />
      <column-instance column='[Product]' derivation='None' name='[none:Product:nk]' pivot='key' type='nominal' />
      <layout dim-ordering='alphabetic' dim-percentage='0.5' measure-ordering='alphabetic' measure-percentage='0.4' show-structure='true' />
      <style>
        <style-rule element='mark'>
{palette('Manufacturer', BRAND_COLORS)}
{palette('Product', TIER_COLORS)}
        </style-rule>
      </style>
      <semantic-values>
        <semantic-value key='[Country].[Name]' value='&quot;United States&quot;' />
      </semantic-values>
    </datasource>"""


def zone_style() -> str:
    return ("\n            <zone-style>\n              <format attr='border-color' value='#000000' />\n"
            "              <format attr='border-style' value='none' />\n              <format attr='border-width' value='0' />\n"
            "              <format attr='margin' value='4' />\n            </zone-style>\n          ")


def dashboard_xml(sheet_names: list[str]) -> str:
    zid = iter(range(3, 100))
    Z = []
    X0, X1 = 667, 100000 - 667          # 8 px side padding on a 1200 px wide dashboard
    Y0, Y1 = 800, 100000 - 800          # 8 px top/bottom padding on a 1000 px tall dashboard

    def split(fracs):
        edges, acc = [X0], 0.0
        for f in fracs[:-1]:
            acc += f
            edges.append(X0 + round((X1 - X0) * acc))
        edges.append(X1)
        return [(edges[i], edges[i + 1] - edges[i]) for i in range(len(fracs))]

    def sheet(name, xw, y, h, title=True):
        x, w = xw
        Z.append(f"<zone h='{h}' id='{next(zid)}' name='{esc(name)}' show-title='{'true' if title else 'false'}' w='{w}' x='{x}' y='{y}'>{zone_style()}</zone>")

    def text(runs, xw, y, h):
        x, w = xw
        r = "\n".join(f"              <run{a}>{esc(t)}</run>" for t, a in runs)
        Z.append(f"<zone forceUpdate='true' h='{h}' id='{next(zid)}' type='text' w='{w}' x='{x}' y='{y}'>\n"
                 f"            <formatted-text>\n{r}\n            </formatted-text>{zone_style()}</zone>")

    def filt(kind, field, xw, y, h, mode="checkdropdown"):
        x, w = xw
        name, _, _ = inst(kind, field)
        m = f" mode='{mode}'" if mode else ""
        vals = "database" if kind == "none_qk" else "cascading"
        Z.append(f"<zone h='{h}' id='{next(zid)}'{m} name='Brand Share' param='{q(name)}' type='filter' values='{vals}' "
                 f"w='{w}' x='{x}' y='{y}'>{zone_style()}</zone>")

    heights = [6000, 6500, 10000, 25000, 25000]
    ys = [Y0]
    for h in heights:
        ys.append(ys[-1] + h)
    heights.append(Y1 - ys[-1])          # last row takes the remainder
    full = split([1.0])[0]
    text([("Four-Brand Share Monitor", " bold='true' fontsize='18'"), ("Æ\n", ""),
          ("Synthetic data, Jan 2020 – Jun 2026. 2026 covers Jan–Jun only, so compare it with the same months of 2025.", " fontcolor='#6b6f78' fontsize='10'")],
         full, ys[0], heights[0])
    fx = split([0.26, 0.17, 0.15, 0.13, 0.15, 0.14])
    filt("none_qk", "Month Date", fx[0], ys[1], heights[1], mode=None)
    filt("none_nk", "Manufacturer", fx[1], ys[1], heights[1])
    filt("none_nk", "Product", fx[2], ys[1], heights[1])
    filt("none_nk", "Region", fx[3], ys[1], heights[1])
    filt("none_nk", "State", fx[4], ys[1], heights[1])
    Z.append(f"<zone h='{heights[1]}' id='{next(zid)}' mode='slider' param='[Parameters].[Parameter 1]' type='paramctrl' "
             f"w='{fx[5][1]}' x='{fx[5][0]}' y='{ys[1]}'>{zone_style()}</zone>")
    kx = split([0.22, 0.22, 0.56])
    sheet("KPI Units", kx[0], ys[2], heights[2], title=False)
    sheet("KPI Change", kx[1], ys[2], heights[2], title=False)
    text([("How to read this", " bold='true' fontsize='10'"), ("Æ\n", ""),
          ("Brand share is measured against all four brands, so the brand filter hides lines without changing shares. "
           "Changes compare the selected months with the same months a year earlier. "
           "Barefoot is the remainder brand: read its moves in share points. "
           "Min units hides a % change when either period has fewer units than the threshold.", " fontcolor='#6b6f78' fontsize='9'")],
         kx[2], ys[2], heights[2])
    cx = split([0.5, 0.5])
    sheet("Brand Share", cx[0], ys[3], heights[3])
    sheet("Tier Mix", cx[1], ys[3], heights[3])
    ex = split([1 / 3, 1 / 3, 1 / 3])
    sheet("Change Drivers", ex[0], ys[4], heights[4])
    sheet("Seasonality", ex[1], ys[4], heights[4])
    sheet("State Map", ex[2], ys[4], heights[4])
    sheet("Brand x Tier", full, ys[5], heights[5])
    zones = "\n          ".join(Z)
    deps = "\n        ".join(inst(k, f)[1] for k, f, _ in SHARED_FILTERS)
    base = "\n        ".join(base_col_xml(f) for _, f, _ in SHARED_FILTERS)
    return f"""  <dashboards>
    <dashboard name='Share Monitor'>
      <style />
      <size maxheight='1000' maxwidth='1200' minheight='1000' minwidth='1200' sizing-mode='fixed' />
      <datasources>
        <datasource name='Parameters' />
        <datasource caption='{DS_CAPTION}' name='{DS}' />
      </datasources>
      <datasource-dependencies datasource='Parameters'>
        {PARAM}
      </datasource-dependencies>
      <datasource-dependencies datasource='{DS}'>
        {base}
        {deps}
      </datasource-dependencies>
      <zones>
        <zone h='100000' id='2' type='layout-basic' w='100000' x='0' y='0'>
          {zones}
        </zone>
      </zones>
      <simple-id uuid='{uid()}' />
    </dashboard>
  </dashboards>"""


def windows_xml(sheet_names: list[str]) -> str:
    ws = []
    for n in sheet_names:
        ws.append(f"""    <window class='worksheet' hidden='true' name='{esc(n)}'>
      <cards>
        <edge name='left'>
          <strip size='160'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
          </strip>
        </edge>
        <edge name='top'>
          <strip size='2147483647'>
            <card type='columns' />
          </strip>
          <strip size='2147483647'>
            <card type='rows' />
          </strip>
          <strip size='31'>
            <card type='title' />
          </strip>
        </edge>
      </cards>
      <simple-id uuid='{uid()}' />
    </window>""")
    fit = {"KPI Units", "KPI Change", "Brand x Tier"}
    vps = "\n".join(f"        <viewpoint name='{esc(n)}'>\n          <zoom type='entire-view' />\n        </viewpoint>" if n in fit
                     else f"        <viewpoint name='{esc(n)}' />" for n in sheet_names)
    ws.append(f"""    <window class='dashboard' maximized='true' name='Share Monitor'>
      <viewpoints>
{vps}
      </viewpoints>
      <active id='-1' />
      <simple-id uuid='{uid()}' />
    </window>""")
    return "  <windows source-height='30'>\n" + "\n".join(ws) + "\n  </windows>"


def build() -> str:
    names, sheets = build_worksheets()
    return f"""<?xml version='1.0' encoding='utf-8' ?>

<!-- build 20191.19.0213.2333                               -->
<workbook original-version='18.1' source-build='2019.1.0 (20191.19.0213.2333)' source-platform='win' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-format-change-manifest>
    <SheetIdentifierTracking />
    <WindowsPersistSimpleIdentifiers />
  </document-format-change-manifest>
  <preferences>
    <preference name='ui.encoding.shelf.height' value='24' />
    <preference name='ui.shelf.height' value='26' />
  </preferences>
  <datasources>
{datasource_xml()}
  </datasources>
  <mapsources>
    <mapsource name='Tableau' />
  </mapsources>
  <worksheets>
{chr(10).join(sheets)}
  </worksheets>
{dashboard_xml(names)}
{windows_xml(names)}
</workbook>
"""


if __name__ == "__main__":
    assert CSV.exists(), "run analysis/build_dashboard.py first"
    twb = build()
    ElementTree.fromstring(twb.encode("utf-8"))  # well-formed XML or raise
    (ROOT / "tableau" / TWB_NAME).write_text(twb, encoding="utf-8")
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(TWB_NAME, twb)
        z.write(CSV, f"{DATA_DIR}/market_share_tableau.csv")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024 / 1024:.1f} MB) and tableau/{TWB_NAME}")
