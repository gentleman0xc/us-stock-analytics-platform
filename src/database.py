from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from src.config import DB_CONNECTION_STRING, DB_CONFIG

def get_engine():
    """Create SQLAlchemy engine (Connection Pool)"""
    # O engine gerencia as conexões de forma eficiente
    return create_engine(
        DB_CONNECTION_STRING,
        pool_pre_ping=True, # Verifica se a conexão está viva antes de usar
        pool_size=5,        # Mantém 5 conexões abertas
        max_overflow=10
    )

def test_connection():
    """Test database connection"""
    try:
        engine = get_engine()
        # A sintaxe 'with engine.connect()' garante que a conexão fecha sozinha
        with engine.connect() as conn:
            # Teste 1: Versão do Banco
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            
            # Teste 2: Nome do Banco Atual
            result_db = conn.execute(text("SELECT current_database()"))
            db_name = result_db.fetchone()[0]
            
            print(f"   PostgreSQL Connected Successfully!")
            print(f"   Host: {DB_CONFIG['host']}")
            print(f"   Database: {db_name}") # Deve aparecer 'stock_analytics'
            print(f"   Version: {version.split()[0]} {version.split()[1]}")
            
        return True
        
    except SQLAlchemyError as e:
        print(f"Connection failed: {e}")
        print(f"Dica: Verifique se sua senha no .env está correta e se o PostgreSQL está rodando.")
        return False

def save_dataframe(df, table_name, if_exists='append'):
    """Save DataFrame to database"""
    try:
        engine = get_engine()
        # index=False porque nossas tabelas têm IDs próprios ou chaves compostas
        df.to_sql(table_name, engine, if_exists=if_exists, index=False)
        print(f"Saved {len(df):,} rows to '{table_name}'")
        return True
    except SQLAlchemyError as e:
        print(f"Failed to save to {table_name}: {e}")
        return False

def query_to_df(sql_query):
    """Execute query and return DataFrame"""
    try:
        engine = get_engine()
        # O Pandas moderno já usa o SQLAlchemy engine nativamente
        df = pd.read_sql(sql_query, engine)
        return df
    except SQLAlchemyError as e:
        print(f"Query failed: {e}")
        return None

if __name__ == "__main__":
    test_connection()