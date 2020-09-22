import sys

sys.path.append("/Users/cj/Documents/atst")

import os
from atat.app import make_app, make_config
from pathlib import Path
from pyquery import PyQuery as pq
from itertools import chain
from shutil import copyfile

os.environ["SERVER_NAME"] = "localhost:8000"

if __name__ == "__main__":
    config = make_config()
    app = make_app(config)

    with app.app_context():
        template = app.jinja_env.get_template("under_maintenance.html")
        html = template.render()

        Path("/tmp/um/static/assets").mkdir(parents=True, exist_ok=True)
        Path("/tmp/um/static/img").mkdir(parents=True, exist_ok=True)

        with open("/tmp/um/index.html", "w") as fh:
            fh.write(html)

        d = pq(html)
        files = chain(
            (l.attr("href") for l in d("link").items()),
            (s.attr("src") for s in d("script, img").items()),
        )
        for f in files:
            copyfile("." + f.strip(), "/tmp/um" + f)
