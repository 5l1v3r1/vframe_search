"""
Generate API documentation for the app
"""

import click

from app.models import types
from operator import attrgetter

_header = """
# API Routes

The VFrame Search application incorporates a RESTful API for running searches
and talking to the database.  APIs either process commandline parameters directly,
or accept POST/PUT input as JSON.  For the most part, APIs return JSON with the
following structure:

```
{ 'status': 'ok', 'res': ... }
{ 'status': 'error', 'error': ... }
```
"""
_footer = """

---
This documentation was automatically generated by running `python cli_docs.py routes`
"""

_jsonparams = {
  'Collection': "title, username, notes, archived (boolean)",
  'Feature': "active (boolean), modelzoo_name, index_type, username",
}

@click.command("")
@click.option(
    "--sort",
    "-s",
    type=click.Choice(("endpoint", "methods", "rule", "match")),
    default="rule",
    help=(
        'Method to sort routes by. "match" is the order that Flask will match '
        "routes when dispatching a request."
    ),
)
@click.pass_context
def cli(ctx, sort):
  from app.server.web import create_app
  import app.sql.common as models

  current_app = create_app()

  rules = filter(lambda rule: 'api' in rule.rule, list(current_app.url_map.iter_rules()))
  if not rules:
    click.echo("No routes were registered.")
    return

  ignored_methods = ("HEAD", "OPTIONS")

  if sort in ("endpoint", "rule"):
    rules = sorted(rules, key=attrgetter(sort))
  elif sort == "methods":
    rules = sorted(rules, key=lambda rule: sorted(rule.methods))

  rule_methods = [", ".join(sorted(filter(lambda m: m not in ignored_methods, rule.methods))) for rule in rules]

  last_model = ""

  text = []
  text.append(_header)
  for rule, methods in zip(rules, rule_methods):
    view_class, view_method = rule.endpoint.split(":")
    view_model = view_class[:-4]
    view_func = current_app.view_functions[rule.endpoint]
    if view_model in _jsonparams:
      view_jsonparams = _jsonparams[view_model]
    else:
      view_jsonparams = ""
    doc = view_func.__doc__ or ""
    doc = doc.strip().replace('{model}', view_model.lower()).replace('{jsonparams}', view_jsonparams)
    lines = [line.strip() for line in doc.split("\n")]
    view_class = view_func.__class__
    heading = "### {} {}".format(methods, rule.rule.replace("<", "[").replace(">", "]"))

    if last_model != view_model:
      last_model = view_model
      text.append("")
      text.append("## {} API".format(view_model))
      text.append("")
    text.append(heading)
    text.append("")
    for line in lines:
      text.append(line)
    if len(lines) == 1:
      text.append("")
    text.append("* Implemented in {}".format(rule.endpoint))
    text.append("")

  text.append(_footer)
  print("\n".join(text))
