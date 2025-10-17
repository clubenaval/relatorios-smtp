import mysql.connector
from mysql.connector import Error
import logging
from werkzeug.security import generate_password_hash

def get_conn(host, user, password, database, port=3306):
    return mysql.connector.connect(host=host, user=user, password=password, database=database, port=port)

def setup_database(auth_mode, db_host, db_user, db_password, db_name, db_port=3306):
    """Cria/ajusta tabelas e semeia admin (modo DB)."""
    try:
        # Garante DB
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password, port=db_port)
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        conn.commit()
        cur.close()
        conn.close()

        conn = get_conn(db_host, db_user, db_password, db_name, db_port)
        cur = conn.cursor()

        # email_logs com message_id e índice único por message_id+to_email+status
        cur.execute("""
            CREATE TABLE IF NOT EXISTS email_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                message_id VARCHAR(64) NOT NULL,
                log_date DATE,
                log_time TIME,
                from_email VARCHAR(255),
                to_email VARCHAR(255),
                status VARCHAR(50),
                origin_host VARCHAR(255),
                origin_ip VARCHAR(45),
                subject VARCHAR(255),
                inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_email_log (message_id, to_email, status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        conn.commit()

        # Migração leve (caso já existisse)
        try:
            cur.execute("SHOW COLUMNS FROM email_logs LIKE 'message_id'")
            has_msgid = cur.fetchone()
            if not has_msgid:
                cur.execute("ALTER TABLE email_logs ADD COLUMN message_id VARCHAR(64) NOT NULL DEFAULT ''")
                conn.commit()
            cur.execute("SHOW INDEX FROM email_logs WHERE Key_name='unique_email_log'")
            if cur.fetchall():
                cur.execute("ALTER TABLE email_logs DROP INDEX unique_email_log")
                conn.commit()
            cur.execute("SHOW INDEX FROM email_logs WHERE Key_name='uq_email_log'")
            if not cur.fetchall():
                cur.execute("ALTER TABLE email_logs ADD UNIQUE KEY uq_email_log (message_id, to_email, status)")
                conn.commit()
        except Error as e:
            logging.info(f"Ajuste de esquema (migr.) ok/ignorado: {e}")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS app_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) NOT NULL UNIQUE,
                email VARCHAR(255),
                password_hash VARCHAR(255) NOT NULL,
                is_admin TINYINT(1) NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reset_token VARCHAR(255),
                reset_expires DATETIME
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        conn.commit()

        # Migração para adicionar email e renomear is_default_admin para is_admin, se necessário
        try:
            cur.execute("SHOW COLUMNS FROM app_users LIKE 'email'")
            if not cur.fetchone():
                cur.execute("ALTER TABLE app_users ADD COLUMN email VARCHAR(255)")
                conn.commit()
            cur.execute("SHOW COLUMNS FROM app_users LIKE 'is_default_admin'")
            if cur.fetchone():
                cur.execute("ALTER TABLE app_users CHANGE is_default_admin is_admin TINYINT(1) NOT NULL DEFAULT 0")
                conn.commit()
            cur.execute("SHOW COLUMNS FROM app_users LIKE 'reset_token'")
            if not cur.fetchone():
                cur.execute("ALTER TABLE app_users ADD COLUMN reset_token VARCHAR(255)")
                conn.commit()
            cur.execute("SHOW COLUMNS FROM app_users LIKE 'reset_expires'")
            if not cur.fetchone():
                cur.execute("ALTER TABLE app_users ADD COLUMN reset_expires DATETIME")
                conn.commit()
        except Error as e:
            logging.info(f"Ajuste de esquema em app_users ok/ignorado: {e}")

        if auth_mode == 'DB':
            cur.execute("SELECT id FROM app_users WHERE username=%s", ('admin',))
            row = cur.fetchone()
            if not row:
                pwd_hash = generate_password_hash('admin')
                cur.execute(
                    "INSERT INTO app_users (username, email, password_hash, is_admin) VALUES (%s, %s, %s, 1)",
                    ('admin', 'admin@example.com', pwd_hash)
                )
                conn.commit()
                logging.info("Usuário padrão 'admin' criado com senha 'admin' e privilégios de admin.")

        cur.close()
        conn.close()
        logging.info("Banco de dados configurado com sucesso.")
    except Error as e:
        logging.error(f"Erro ao configurar o banco de dados: {e}")

def insert_database(emails, host, user, password, database, db_port=3306):
    if not emails:
        logging.info("Nenhum e-mail novo para inserir.")
        return False
    try:
        conn = get_conn(host, user, password, database, db_port)
        cursor = conn.cursor()
        insert_query = """
            INSERT IGNORE INTO email_logs 
            (message_id, log_date, log_time, from_email, to_email, status, origin_host, origin_ip, subject) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        cursor.executemany(insert_query, emails)
        conn.commit()
        rowcount = cursor.rowcount
        logging.info(f"{rowcount} novos logs inseridos no banco de dados.")
        return rowcount
    except Error as e:
        logging.error(f"Erro ao inserir no banco de dados: {e}")
        return False
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass