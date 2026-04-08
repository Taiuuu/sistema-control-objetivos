# =============================================================================
# VESP Organizations - Servicio de API REST
# =============================================================================

import threading
from api.app import app

def iniciar_api():
    """Inicia la API REST en un hilo separado."""
    def run_api():
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    print("API REST iniciada en http://127.0.0.1:5000")