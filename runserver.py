import sys
from funnel import app, models, init_for, init_nodular
init_for('dev')
init_nodular()

try:
    port = int(sys.argv[1])
except (IndexError, ValueError):
    port = 3000
app.run('0.0.0.0', port=port, debug=True)
