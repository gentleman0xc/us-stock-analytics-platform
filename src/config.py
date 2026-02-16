import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Carrega variáveis de ambiente do arquivo .env
# Isso garante que suas senhas não fiquem expostas no código
load_dotenv()

# 2. Caminhos do Projeto (Project Paths)
# Define a raiz do projeto para que funcione em qualquer computador
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
SQL_DIR = PROJECT_ROOT / 'sql'

# 3. Configuração do Banco de Dados
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'stock_analytics'), 
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'default_pass'),
}

# String de conexão para o SQLAlchemy
DB_CONNECTION_STRING = (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

# 4. Ativos para rastrear (Portfolio 2026)
STOCKS = [
    # Magnificent 7 + AI Leaders
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA',
    # Finance & Payment
    'JPM', 'BAC', 'V', 'MA',
    # Consumer & Retail
    'WMT', 'COST', 'HD',
    # Healthcare
    'JNJ', 'UNH', 'LLY',
    # ETFs (Market & Small Caps)
    'SPY', 'QQQ', 'IWM',
]

# Configurações de Análise
DATA_PERIOD = '2y'      # Período de histórico para baixar
RISK_FREE_RATE = 0.045  # Taxa livre de risco (Treasury 10y ~4.5%)

# Bloco de Teste Rápido
if __name__ == "__main__":
    print(f" Configuração carregada com sucesso!")
    print(f" Raiz do Projeto: {PROJECT_ROOT}")
    print(f" Banco de Dados Alvo: {DB_CONFIG['database']}")
    print(f" Total de Ativos monitorados: {len(STOCKS)}")