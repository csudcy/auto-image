import json
import pathlib

import utils


HTML_FILE = utils.CURRENT_FOLDER / 'scores.html'


print('Loading scores...')
SCORES = utils.load_scores()
results = list(SCORES.items())
results.sort(key=lambda result: result[1], reverse=True)

print('Generating HTML...')
html = [
    '<table border="1">',
    '<thead>',
    '<tr>',
    '<th>File</th>',
    '<th>Score</th>',
    '<th>Image</th>',
    '</tr>',
    '</thead>',
    '<tbody>',
]
html.append('<ul>')
for file_id, score in results:
  path = utils.IMAGE_FOLDER / file_id
  relative_path = path.relative_to(utils.CURRENT_FOLDER)
  html.extend([
      '<tr>',
      f'<td>{file_id}</td>',
      f'<td>{score}</td>',
      f'<td><img src="{relative_path}" style="max-height: 100px;"></td>',
      '</tr>',
  ])
html.extend([
    '</tbody>',
    '</table>',
])

print('Saving HTML...')
with HTML_FILE.open('w') as f:
  f.write('\n'.join(html))

print('Done!')
