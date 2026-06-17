from .dev import *

# Run Celery tasks inline (no broker/worker needed in tests).
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
