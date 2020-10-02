import os
import sys

script_directory = os.path.dirname(__file__)
project_directory = os.path.join(script_directory, "../")
parent_dir = os.path.abspath(project_directory)
sys.path.append(parent_dir)

from os import path, stat
from atat.app import make_app, make_config
from pyquery import PyQuery as pq
import base64
import re
from pathlib import Path
from urllib.parse import urlparse
import argparse


# how large the html file can be before showing a warning message
html_file_size_limit = 1024 * 1024

# refer to https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
# for additional mime types
mime_types = {
    ".png": "image/png",
    ".eot": "application/vnd.ms-fontobject",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".ttf": "font/ttf",
    ".svg": "image/svg+xml",
    ".ico": "image/vnd.microsoft.icon",
}

css_asset_whitelist = [
    "sourcesanspro-bold-webfont.*woff2",
    "sourcesanspro-regular-webfont.*woff2",
    "sourcesanspro-light-webfont.*woff2",
    "sourcesanspro-italic-webfont.*woff2",
]


def relative_path(file_path):
    return urlparse(file_path.strip()).path[1:]


def file_ext(file_path):
    return path.splitext(file_path)[1]


def make_base64(file_path):
    print(f"  {file_path}")

    file_path = relative_path(file_path)
    mime_type = mime_types[file_ext(file_path)]

    with open(file_path, "rb") as fh:
        data = fh.read()

    if mime_types[".svg"] == mime_type:
        encoding = "utf-8"
    else:
        data = base64.b64encode(data)
        encoding = "base64"

    return f"data:{mime_type};{encoding},{data.decode('utf-8')}"


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate Under Maintenance Page")
    parser.add_argument(
        "--output",
        help="Directory where file will be written. (default: ./)",
        type=Path,
        default="./",
    )
    args = parser.parse_args()

    config = make_config()
    app = make_app(config)

    css_whitelist_pattern = "|".join(css_asset_whitelist)

    # render template
    with app.app_context():
        template = app.jinja_env.get_template("under_maintenance.html")
        d = pq(template.render())

    # encode images
    print("Encoding img assets...")
    for img in d("img").items():
        img.attr.src = make_base64(img.attr.src)

    # filtered link elements
    css_link_elements = filter(
        lambda l: file_ext(l.attr.href) == ".css", d("link").items()
    )
    non_css_link_elements = filter(
        lambda l: file_ext(l.attr.href) != ".css", d("link").items()
    )

    # add css to html
    print("Encoding css assets...")
    for link in css_link_elements:
        with open(relative_path(link.attr.href)) as fh:
            # remove all comments, including reference to css map file
            css_str = re.sub(r"/\*.*?\*/", "", fh.read().strip())

        # encode all css assets that have been whitelisted
        urls = re.findall(r"url\(\"*([A-Za-z0-9/.\-#?]+)\"*\)", css_str)
        for url in urls:
            if re.search(css_whitelist_pattern, url):
                css_str = css_str.replace(url, f"url({make_base64(url)})")

        # inject css into head of html
        d("head").append(f"<style type='text/css'>{css_str}</style>")

        # remove css element from html
        link.remove()

    # this is usually the ico file...
    print("Encoding other link assets...")
    for link in non_css_link_elements:
        link.attr.href = make_base64(link.attr.href)

    # write html to file
    args.output.mkdir(parents=True, exist_ok=True)
    html_file = path.join(args.output, "index.html")
    with open(html_file, "w") as fh:
        fh.write(d.html(method="html"))

    if stat(html_file).st_size > html_file_size_limit:
        print(
            f"Warning: Under Maintenance HTML file is larger then {html_file_size_limit} Bytes.",
            file=sys.stderr,
        )
