# Package initialization: support import both as package and as script
try:
	# when imported as package (e.g., import app_vet)
	from .extensions import db, login_manager
	from . import models, services
except Exception:
	# fallback when file is executed directly (python __init__.py)
	from extensions import db, login_manager
	import models, services
