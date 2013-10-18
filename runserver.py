import sys
from funnel import app, models, init_for, load_root
init_for('dev')
load_root()

try:
    port = int(sys.argv[1])
except (IndexError, ValueError):
    port = 3000
app.run('0.0.0.0', port=port, debug=True)
