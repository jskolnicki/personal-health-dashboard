from models import get_database_engine, create_tables

if __name__ == "__main__":
    engine = get_database_engine()
    create_tables(engine)