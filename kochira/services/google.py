import requests
from urllib.parse import urlencode, unquote
from html.parser import HTMLParser

from ..service import Service, background

service = Service(__name__)

html_parser = HTMLParser()


@service.command(r"\?\?(?P<term>.+?)(?: (?P<num>\d+))?$")
@service.command(r"!g (?P<term>.+?)(?: (?P<num>\d+))?$")
@service.command(r"(?:search|google)(?: for)? (?P<term>.+?)(?: \((?P<num>\d+)\))?\??$", mention=True)
@background
def search(client, target, origin, term, num: int=None):
    r = requests.get("https://ajax.googleapis.com/ajax/services/search/web?" + urlencode({
        "v": "1.0",
        "q": term
    })).json()

    results = r.get("responseData", {}).get("results", [])

    if not results:
        client.message(target, "{origin}: Couldn't find anything matching \"{term}\".".format(
            origin=origin,
            term=term
        ))
        return

    if num is None:
        num = 1

    num -= 1
    total = len(results)

    if num >= total or num < 0:
        client.message(target, "{origin}: Can't find that definition of \"{term}\".".format(
            origin=origin,
            term=term
        ))

    client.message(target, "{origin}: {title}: {url} ({num} of {total})".format(
        origin=origin,
        title=html_parser.unescape(results[num]["titleNoFormatting"]),
        url=unquote(results[num]["url"]),
        num=num + 1,
        total=total
    ))
