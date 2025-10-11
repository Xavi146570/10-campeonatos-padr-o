import os
import threading
from datetime import datetime
from flask import Flask, request, jsonify

# Import direto - ambos estão na raiz
from processor import FootballProcessor

app = Flask(__name__)

# Configurações
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your-secret-key")
ADMIN_MODE = os.getenv("ADMIN_MODE", "false").lower() == "true"

# Processador global
processor = FootballProcessor()

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "active",
        "service": "Football Alerts Bot",
        "timestamp": datetime.now().isoformat(),
        "leagues_configured": 10,
        "version": "2.0"
    })

@app.route("/webhook/daily-trigger", methods=["POST"])
def daily_trigger():
    try:
        # Verificar autenticação
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token necessário"}), 401
        
        token = auth_header.split("Bearer ")[1]
        if token != WEBHOOK_SECRET:
            return jsonify({"error": "Token inválido"}), 403
        
        # Verificar se já está processando
        if processor.is_processing():
            return jsonify({
                "status": "already_running",
                "message": "Processamento já em andamento"
            }), 202
        
        # Iniciar processamento em thread separada
        thread = threading.Thread(target=processor.process_all_leagues)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "status": "started",
            "message": "Processamento iniciado",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status", methods=["GET"])
def get_status():
    return jsonify({
        "system": {
            "is_processing": processor.is_processing(),
            "last_execution": processor.last_execution
        },
        "execution_history": processor.get_execution_history()
    })

@app.route("/logs", methods=["GET"])
def get_logs():
    if not ADMIN_MODE:
        return jsonify({"error": "Acesso negado"}), 403
    
    lines = int(request.args.get("lines", 50))
    return jsonify({
        "logs": processor.get_recent_logs(lines)
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    
    print(f"🚀 Football Alerts Bot iniciado na porta {port}")
    print(f"🔧 Modo Admin: {'ATIVO' if ADMIN_MODE else 'INATIVO'}")
    
    app.run(host="0.0.0.0", port=port, debug=False)
