import jinja2

import utils


HTML_FILE = utils.CURRENT_FOLDER / 'scores.html'
SCORERS = (
    'vila',
    'musiq',
)
ORDER_BY = SCORERS[0]


print('Loading scores...')
SCORES = utils.load_scores()
results = list(SCORES.items())
results.sort(key=lambda result: result[1][ORDER_BY], reverse=True)


print('Generating HTML...')
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader('templates'),
    autoescape=jinja2.select_autoescape()
)
template = env.get_template('output.tpl')
html = template.render(
    scorers=SCORERS,
    results=results,
    path_prefix=utils.IMAGE_FOLDER.relative_to(utils.CURRENT_FOLDER),
)

print('Saving HTML...')
with HTML_FILE.open('w') as f:
  f.write(html)

print('Done!')
