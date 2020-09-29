import sys

sys.path.append("/Users/cj/Documents/atst")

from os import path, environ, stat
from atat.app import make_app, make_config
from pyquery import PyQuery as pq
import base64
import re
from pathlib import Path
from urllib.parse import urlparse

environ["SERVER_NAME"] = "localhost:8000"

# how large the html file can be before showing a warning message
html_file_limit_mb = 1

# refer to https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
# for additional mime types
mime_types = {
    ".png": "image/png",
    ".eot": "application/vnd.ms-fontobject",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".ttf": "font/ttf",
    ".svg": "image/svg+xml",
}


def relative_path(file_path):
    return urlparse(file_path).path[1:]


def make_mime_type(file_path):
    file_ext = path.splitext(file_path)[1]
    return mime_types[file_ext]


def make_base64(file_path):
    file_path = relative_path(file_path)
    mime_type = make_mime_type(file_path)
    with open(file_path, "rb") as fh:
        encoded_file = base64.b64encode(fh.read())
    return f"data:{mime_type};base64,{encoded_file.decode()}"


if __name__ == "__main__":
    config = make_config()
    app = make_app(config)

    # render template
    with app.app_context():
        template = app.jinja_env.get_template("under_maintenance.html")
        d = pq(template.render())

    # encode images
    for img in d("img").items():
        img.attr.src = make_base64(img.attr.src)

    # add css to html
    for css in d("link").items():
        if css.attr.href.endswith("css"):
            with open(relative_path(css.attr.href)) as fh:
                # remove all comments, including reference to css map file
                css_str = re.sub(re.compile("/\*.*?\*/", re.DOTALL), "", fh.read())

            # encode all assets from css
            urls = re.findall(r"url\([A-Za-z0-9/.\-#?]*\)", css_str.strip())
            for url in urls:
                css_str = css_str.replace(url, f"url({make_base64(url[4:-1])})")

            # inject css into head of html
            d("head").after(f"<style>{css_str}</style>")

            # remove link element from html
            css.remove()

    # remove javascript
    for js in d("script").items():
        js.remove()

    # write html to file
    Path("/tmp/um").mkdir(parents=True, exist_ok=True)
    with open("/tmp/um/index.html", "w") as fh:
        fh.write(d.html())

    if stat("/tmp/um/index.html").st_size / (1024 * 1024) > html_file_limit_mb:
        print(
            f"Warning: Under Maintenance HTML file is larger then {html_file_limit_mb} MB.",
            file=sys.stderr,
        )

