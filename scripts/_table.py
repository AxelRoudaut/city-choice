"""Remplacement sûr d'un tableau à l'intérieur d'une section donnée.

Chercher « </table></div> » par index() depuis le début d'un tableau peut sauter
par-dessus sa vraie fin et avaler la section suivante — c'est ce qui a détruit
le critère 9. On borne donc toujours la recherche à la section courante.
"""


def bornes_section(src, ancre):
    """Début et fin de la <section> contenant `ancre`."""
    i = src.index(ancre)
    d = src.rindex('<section', 0, i)
    f = src.index('</section>', i)
    return d, f


def remplace_table(src, ancre, nouveau):
    """Remplace le premier <div class="tscroll">…</div> de la section de `ancre`."""
    d, f = bornes_section(src, ancre)
    section = src[d:f]
    i = section.index('<div class="tscroll">')
    # fin = balise fermante appariée du div, comptée dans la seule section
    prof, j = 0, i
    while j < len(section):
        if section.startswith('<div', j):
            prof += 1
        elif section.startswith('</div>', j):
            prof -= 1
            if prof == 0:
                j += len('</div>')
                break
        j += 1
    else:
        raise ValueError("</div> appariée introuvable dans la section")
    return src[:d] + section[:i] + nouveau + section[j:] + src[f:]
