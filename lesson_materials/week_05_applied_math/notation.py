"""Small equation-layout helpers for Maya's QTextBrowser and saved HTML.

Qt supports HTML tables, but not browser MathJax or CSS grid. These helpers use
that shared subset so the live lesson and exported notes show the same math.
The calculations remain in math_core.py; this file only arranges their text.
"""
from html import escape
import re


def fraction(numerator, denominator):
    """Stack already-formatted expressions above and below a fraction bar."""
    return ('<table cellspacing="0" cellpadding="3">'
            '<tr><td align="center" style="border-bottom:1px solid #dddddd">'
            + numerator + '</td></tr><tr><td align="center">'
            + denominator + '</td></tr></table>')


def equation(*parts):
    """Arrange symbols, fractions, and matrices on one mathematical line."""
    cells = ''.join('<td valign="middle">' + part + '</td>' for part in parts)
    return '<table cellspacing="0" cellpadding="5"><tr>' + cells + '</tr></table>'


def matrix(rows, label):
    """Draw a bracketed matrix, with x/y/z column colors and a neutral w."""
    colors = ('#ffaaaa', '#a9dfb0', '#a9c8ff', '#eeeeee')
    brackets = [('⎡', '⎤')] + [('⎢', '⎥')] * (len(rows) - 2) + [('⎣', '⎦')]
    output = []
    for row, (left, right) in zip(rows, brackets):
        cells = '<td>' + left + '</td>'
        for entry, color in zip(row, colors):
            cells += '<td align="right" style="color:{}">{}</td>'.format(color, escape(entry))
        output.append('<tr>' + cells + '<td>' + right + '</td></tr>')
    grid = '<table cellspacing="0" cellpadding="5">' + ''.join(output) + '</table>'
    return equation(label + ' =', grid)


def symbolic_fraction(line, pretty):
    """Recognize lesson formulas explicitly, rather than guess slash precedence."""
    formulas = {
        'u = a / |a|': ('u =', 'a', '|a|'),
        'u = g / |g|': ('u =', 'g', '|g|'),
        'cos(theta) = (a dot b) / (|a| |b|)': ('cos(theta) =', 'a dot b', '|a| |b|'),
        'n = (a x b) / |a x b|': ('n =', 'a x b', '|a x b|'),
    }
    if line in formulas:
        lhs, numerator, denominator = formulas[line]
        return equation(pretty(lhs), fraction(pretty(numerator), pretty(denominator)))
    if line.startswith('q(t) = sin('):
        return equation('q(t) =', fraction('sin((1 − t)ω)', 'sin(ω)'),
                        pretty('q0 +'), fraction('sin(tω)', 'sin(ω)'), pretty('q1'))
    # Numeric substitutions from the two division lessons. Parentheses delimit
    # the numerator/denominator, so this does not rewrite arbitrary prose.
    substitution = re.fullmatch(r'= (.+) / (.+) = (.+)', line)
    if substitution:
        numerator, denominator, result = substitution.groups()
        return equation('=', fraction(pretty(numerator), pretty(denominator)), '=', pretty(result))
    angle = re.fullmatch(r'theta = acos\(clamp\(cos\(theta\), -1, 1\)\) = (.+) degrees', line)
    if angle:
        return equation('θ =', 'arccos(cos θ)', '=', escape(angle[1]) + '°')
    return None


def worked_lines(lines, pretty):
    """Render a section, collecting four matrix rows into one bracketed object."""
    output = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line == 'M_world =' and index + 4 < len(lines):
            rows = [row.strip('() ').split(', ') for row in lines[index + 1:index + 5]]
            if all(len(row) == 4 for row in rows):
                output.append(matrix(rows, pretty('M_world')))
                index += 5
                continue
        formatted = symbolic_fraction(line, pretty)
        if formatted is None:
            # An equality has an explicit left and right side, including worked
            # continuation lines whose left side is intentionally blank.
            left, separator, right = line.partition(' = ')
            if line.startswith('= '):
                left, separator, right = '', '=', line[2:]
            if separator:
                formatted = equation(pretty(left), '=', pretty(right))
            else:
                formatted = '<p>' + pretty(line) + '</p>'
        output.append(formatted)
        index += 1
    return ''.join(output)
