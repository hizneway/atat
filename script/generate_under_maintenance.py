import sys

sys.path.append("/Users/cj/Documents/atst")

import os
from os import path
from atat.app import make_app, make_config
from pyquery import PyQuery as pq
import base64
import re

os.environ["SERVER_NAME"] = "localhost:8000"

if __name__ == "__main__":
    config = make_config()
    app = make_app(config)

    # render template
    with app.app_context():
        template = app.jinja_env.get_template("under_maintenance.html")
        d = pq(template.render())

    # encode images
    for img in d("img").items():
        img_path = img.attr("src")[1:]
        img_ext = path.splitext(img_path)[1][1:]
        with open(img_path, "rb") as fh:
            encoded_file = base64.b64encode(fh.read())
        img.attr.src = f"data:image/{img_ext};base64,{encoded_file.decode()}"

    # add css
    for css in d("link").items():
        if css.attr.href.endswith("css"):
            with open(css.attr.href[1:]) as fh:
                # remove all comments, including reference to css map file
                css_str = re.sub(re.compile("/\*.*?\*/", re.DOTALL), "", fh.read())
                d("head").after(f"<style>{css_str}</style>")
            css.remove()

    # remove js
    for js in d("script").items():
        js.remove()

    # write html to file
    with open("/tmp/um/index.html", "w") as fh:
        fh.write(d.html())

    print(os.stat("/tmp/um/index.html").st_size / 1024)

