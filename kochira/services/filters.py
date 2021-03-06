import functools
import random
import re
import unicodedata

from ..service import Service

service = Service(__name__)


def benisify(s):
    return functools.reduce(lambda acc, f: f(acc), [
        lambda s: s.lower(),
        lambda s: unicodedata.normalize('NFKD', s),
        lambda s: s.replace('x', 'cks'),
        lambda s: re.sub(r'ing','in', s),
        lambda s: re.sub(r'you', 'u', s),
        lambda s: re.sub(r'oo', 'u', s),
        lambda s: re.sub(r'ck\b', 'g', s),
        lambda s: re.sub(r'ck', 'gg', s),
        lambda s: re.sub(r'(t+)(?=[aeiouys]|\b)', lambda x: 'd' * len(x.group(1)), s),
        lambda s: s.replace('p', 'b'),
        lambda s: re.sub(r'\bthe\b', 'da', s),
        lambda s: re.sub(r'\bc', 'g', s),
        lambda s: re.sub(r'\bis\b', 'are', s),
        lambda s: re.sub(r'c+(?![eiy])', 'g', s),
        lambda s: re.sub(r'[qk]+(?=[aeiouy]|\b)', 'g', s),
        lambda s: re.sub(r'([?!.]|$)+', lambda x: (x.group(0) * random.randint(2, 5)) + " " + "".join((":" * random.randint(1, 2)) + ("D" * random.randint(1, 4)) for _ in range(random.randint(2, 5))), s),
    ], s)



FABULOUS_COLORS = [4, 5, 8, 9, 10, 12, 13, 6]

def fabulousify(s):
    buf = ""

    for i, x in enumerate(s):
        if x == " ":
            buf += x
        else:
            buf += "\x03{:02}{}".format(FABULOUS_COLORS[i % len(FABULOUS_COLORS)], x)

    return buf


def run_filter(f, client, target, origin, text=None):
    if text is None:
        if len(client.backlogs[target]) == 1:
            return

        _, text = client.backlogs[target][1]

    text = f(text)

    client.message(target, "{origin}: {text}".format(
        origin=origin,
        text=text
    ))


def bind_filter(name, f):
    @service.command(r"!{}(?: (?P<text>.+))?$".format(name))
    @service.command(r"{}(?: (?P<text>.+))?$".format(name), mention=True)
    def benis(client, target, origin, text=None):
        run_filter(f, client, target, origin, text)


bind_filter("benis", benisify)
bind_filter("fabulous", fabulousify)
