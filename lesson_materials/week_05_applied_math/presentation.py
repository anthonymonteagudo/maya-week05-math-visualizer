"""Neutral math display with separate explanations and collapsible calculations."""
from html import escape, unescape
import re
from .calculations import number, vector
from .math_core import add
from .notation import worked_lines

HEADERS = ("SUBTRACTION", "ADDITION", "MAGNITUDE", "NORMALIZATION", "DOT ->", "PROJECTION ->", "CROSS ->", "ARM REACH", "LOCAL POINT", "ORIENTATION INTERPOLATION", "ATTACHMENT", "DRIVEN CHANNELS", "SYMBOLS", "ACTUAL ORIENTATION", "DIRECTION ->", "POSITION INTERPOLATION")
PROSE = ("APPLICATION:", "Displayed values", "FK is active", "Teal and gold", "Blue has", "Purple ends", "Reversing input", "A point has", "Maya convention:", "This point is", "XYZ rotation order", "Compare t=", "This is the slider", "Quaternion component order", "Quaternion arc angle", "No blue", "No projection", "No red", "This distance check", "Attachment:")


def pretty(text):
    result = escape(text.replace(" -> ", " → ").replace(" dot ", " · ").replace(" x b", " × b").replace("*", "×").replace("^2", "²").replace("sqrt", "√").replace("theta", "θ").replace("omega", "ω").replace("<=", "≤"))
    terms=re.match(r"^(c[xyz]) = (.+?)×(.+?) - (.+?)×(.+?) = (.+)$",result)
    if terms and not any(letter in terms[2] for letter in "ab"):
        c,a1,b1,a2,b2,value=terms.groups()
        result=(c+' = <span style="color:#65c9ba">'+a1+'</span>×<span style="color:#e0bc60">'+b1+
                '</span> - <span style="color:#65c9ba">'+a2+'</span>×<span style="color:#e0bc60">'+b2+'</span> = '+value)
    # Semantic operand colors: a is teal, b gold; output components use axis colors.
    result=re.sub(r"\b([ab])([xyz])\b",lambda m:'<span style="color:{}">{}<sub>{}</sub></span>'.format("#65c9ba" if m[1]=="a" else "#e0bc60",m[1],m[2]),result)
    result=re.sub(r"\bc([xyz])\b",lambda m:'<span style="color:{}">c<sub>{}</sub></span>'.format({"x":"#ff8888","y":"#8ddd96","z":"#8fbaff"}[m[1]],m[1]),result)
    result = re.sub(r'\b([pqveMxyzw])_(world|local|actual)\b', r'\1<sub>\2</sub>', result)
    result = re.sub(r'\bm([0-3])([0-3])\b', r'm<sub>\1\2</sub>', result)
    result = re.sub(r'\b([pqeL])([012])\b', r'\1<sub>\2</sub>', result)
    result = result.replace('acos', 'arccos').replace(' degrees', '°')
    result = result.replace(' - ', ' − ')
    return result



def split(worked):
    sections, notes, current = [], [], None
    for line in worked.splitlines():
        if line.startswith(HEADERS):
            current = [line, []]
            sections.append(current)
        elif line.startswith(PROSE + ("Numerical guard:",)):
            # Keep narration out of the equations; available in the Explanations panel.
            notes.append(line)
        elif current is not None and line.strip():
            current[1].append(line.strip())
    return sections or [["Calculation", worked.splitlines()]], notes


def result_summary(data, topic):
    if topic == "Step 1: S to E":
        return "a = E − S = " + vector(data["upper"])
    if topic == "Vectors":
        return "a + b = W − S = " + vector(add(data["upper"], data["lower"]))
    if topic == "Normalize":
        return "u = " + (vector(data["upper_unit"]) if data["upper_unit"] else "undefined (zero length)")
    if topic == "Dot / alignment":
        return "a · b = " + number(data["dot"]) + " | unit dot = " + (number(data["cosine"]) if data["cosine"] is not None else "undefined")
    if topic == "Dot / projection":
        h = vector(data["projection"]) if data["projection"] is not None else "undefined (S = W)"
        return "Scalar a · b = {}     |     Projected point H = {}".format(number(data["dot"]), h)
    if topic == "Cross / plane":
        n = vector(data["normal"]) if data["normal"] is not None else "undefined (no unique plane)"
        return "a × b = {}     |     n = {}".format(vector(data["cross"]), n)
    return "L1 + L2 = {} + {} = {} {}".format(number(data["upper_length"]),number(data["lower_length"]),number(data["upper_length"]+data["lower_length"]), data["units"])


def clipboard_text(worked, data=None, topic="Vectors", summary_only=False):
    """Linear text for slide text boxes, independent of the HTML table layout."""
    def plain(line):
        return unescape(re.sub(r'<[^>]*>', '', pretty(line)))

    output = []
    if data:
        output.append("World space ({})".format(data["units"]))
        count = 2 if topic in ("Step 1: S to E", "Normalize") else 3
        output.extend(label + " = " + vector(point)
                      for label, point in list(zip("SEW", data["points"]))[:count])
        if summary_only:
            output.append(result_summary(data, topic))
            return "\n".join(output)
    sections, _ = split(worked)
    for title, lines in sections:
        if title.startswith("SYMBOLS"):
            continue
        output.extend(["", plain(title.replace(" -> ", ": ").capitalize())])
        output.extend(plain(line) for line in lines)
    return "\n".join(output).strip()


def document(worked, data=None, topic="Vectors", collapsed=(), interactive=True):
    sections, _ = split(worked)
    body = []
    if data:
        pairs = list(zip("SEW",data["points"]))[:2 if topic in ("Step 1: S to E", "Normalize") else 3]
        inputs = " &nbsp;&nbsp; ".join('<span style="color:{}"><b>{}</b> = {}</span>'.format({"S":"#ff6666","E":"#66ff73","W":"#66a6ff"}[label],label,escape(vector(point))) for label,point in pairs)
        legend = '<span style="color:#65c9ba">a = E − S</span>'
        if topic not in ("Step 1: S to E", "Normalize"):
            legend += ' &nbsp; <span style="color:#e0bc60">b = W − E</span>'
        body.append('<p>World space ({})<br>{}<br>{}</p>'.format(escape(data["units"]),inputs,legend))
        color = {"Vectors":"#b9d783","Normalize":"#8bb2d9","Dot / projection":"#c2acd9","Cross / plane":"#df9fa7"}.get(topic,"#eeeeee")
        body.append('<p style="font-size:14pt;color:{}"><b>{}</b></p>'.format(color,escape(result_summary(data,topic))))
    cards=[]
    for index,(title,lines) in enumerate(sections):
        # Definitions belong in contextual help; exports retain the full lesson.
        if interactive and title.startswith("SYMBOLS"):
            continue
        short_titles = {
            "SUBTRACTION": "Displacement", "ADDITION": "Vector sum", "MAGNITUDE": "Length",
            "NORMALIZATION": "Unit direction", "DOT": "Dot product", "PROJECTION": "Projection",
            "CROSS": "Cross product", "LOCAL POINT": "Local → world", "DIRECTION": "Direction · w = 0",
            "ACTUAL ORIENTATION": "Actual orientation", "ARM REACH": "Reach",
        }
        original_title = title
        prefix = title.split(" -> ")[0]
        title = short_titles.get(prefix, title.replace(" -> ", " · ").title().replace("Xyz", "XYZ").replace("| T =", "| t ="))
        color = "#b9d783" if title == "Vector sum" else "#eeeeee"
        indicator = "▸" if index in collapsed else "▾"
        content = '' if index in collapsed else '<div style="font-family:Cambria Math,Cambria,serif;font-size:14pt">' + worked_lines(lines, pretty) + '</div>'
        heading = '<a href="section:{}" title="{}" style="color:{};text-decoration:none"><b>{} {}</b></a>'.format(index,escape(original_title,quote=True),color,indicator,escape(title)) if interactive else '<b style="color:{}">{}</b>'.format(color,escape(title))
        cards.append('<td valign="top" bgcolor="#363636" style="padding:12px"><p>{}</p>{}</td>'.format(heading,content))
    # Matrix substitutions and quaternion equations need the full panel width.
    columns = 1 if any(title.startswith(("LOCAL POINT", "SYMBOLS")) for title, _ in sections) else 2
    for i in range(0,len(cards),columns):
        body.append('<table width="100%" cellspacing="8" cellpadding="8"><tr>'+''.join(cards[i:i+columns])+'</tr></table>')
    return '<html><head><meta charset="utf-8"></head><body style="background-color:#292929;color:#ededed;font-family:Segoe UI;font-size:12pt">'+''.join(body)+'</body></html>'
