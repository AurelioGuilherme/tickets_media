import sqlite3

def main():
    conn = sqlite3.connect('tickets_database.db')
    cursor = conn.cursor()

    # --- Pessoas atendentes --- #
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pessoas (
            ra TEXT PRIMARY KEY UNIQUE,
            nome TEXT,
            senha TEXT
        )
    ''')
    
    # --- Notas --- #
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notas (
            ticket TEXT PRIMARY KEY UNIQUE,
            agente TEXT,
            data DATE,
            nota INTEGER CHECK(nota >= 0 AND nota <= 10),
            FOREIGN KEY(agente) REFERENCES pessoas(ra)
        )
    ''')


    conn.commit()
    conn.close()

    
if __name__ == "__main__":
    main()
