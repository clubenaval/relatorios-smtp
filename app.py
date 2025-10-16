import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import validate_environment_variables
from database import get_conn, setup_database, insert_database
from log_parser import parse_log
from scheduler import update_job, run_scheduler
from auth import authenticate, login_required
from datetime import datetime
import pytz
import threading
import csv
import io

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key')

# Configuração de variáveis de ambiente
try:
    env_vars = validate_environment_variables()
    AUTH_MODE = env_vars['AUTH_MODE']
    DB_HOST = env_vars['DB_HOST']
    DB_USER = env_vars['DB_USER']
    DB_PASSWORD = env_vars['DB_PASSWORD']
    DB_NAME = env_vars['DB_NAME']
    LOG_DIR = env_vars['LOG_DIR']
    TZ = env_vars['TZ']
    SCHEDULE_TYPE = env_vars['SCHEDULE_TYPE']
    DB_PORT = env_vars['DB_PORT']
    if AUTH_MODE == 'AD':
        LDAP_HOST = env_vars['LDAP_HOST']
        LDAP_DOMAIN = env_vars['LDAP_DOMAIN']
        LDAP_BASE_DN = env_vars['LDAP_BASE_DN']
        LDAP_GROUP_DN = env_vars['LDAP_GROUP_DN']
    if SCHEDULE_TYPE == 'minutes':
        SCHEDULE_INTERVAL_MINUTES = env_vars['SCHEDULE_INTERVAL_MINUTES']
    else:
        SCHEDULE_TIME = env_vars['SCHEDULE_TIME']
except EnvironmentError as e:
    logging.error(str(e))
    exit(1)

@app.after_request
def add_no_cache_headers(response):
    if request.path == '/':
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if authenticate(username, password, AUTH_MODE, 
                        ldap_host=LDAP_HOST if AUTH_MODE == 'AD' else None,
                        ldap_domain=LDAP_DOMAIN if AUTH_MODE == 'AD' else None,
                        ldap_base_dn=LDAP_BASE_DN if AUTH_MODE == 'AD' else None,
                        ldap_group_dn=LDAP_GROUP_DN if AUTH_MODE == 'AD' else None,
                        db_host=DB_HOST, db_user=DB_USER, db_password=DB_PASSWORD, db_name=DB_NAME, db_port=DB_PORT):
            session['logged_in'] = True
            session['username'] = username
            flash('Login bem-sucedido!')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha inválidos, ou sem permissão.')
    return render_template('login.html', auth_mode=AUTH_MODE)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('_flashes', None)
    flash('Logout realizado.')
    return redirect(url_for('login'))

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if AUTH_MODE != 'DB':
        flash('Alteração de senha indisponível quando autenticando via Active Directory.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        current_pwd = request.form.get('current_password', '')
        new_pwd = request.form.get('new_password', '')
        confirm_pwd = request.form.get('confirm_password', '')

        if not new_pwd or len(new_pwd) < 4:
            flash('Nova senha deve ter pelo menos 4 caracteres.')
            return redirect(url_for('change_password'))
        if new_pwd != confirm_pwd:
            flash('Confirmação de senha não confere.')
            return redirect(url_for('change_password'))

        username = session.get('username')
        try:
            from werkzeug.security import generate_password_hash, check_password_hash
            conn = get_conn(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id, password_hash FROM app_users WHERE username=%s", (username,))
            user = cur.fetchone()
            if not user or not check_password_hash(user['password_hash'], current_pwd):
                flash('Senha atual incorreta.')
                return redirect(url_for('change_password'))
            new_hash = generate_password_hash(new_pwd)
            cur.execute("UPDATE app_users SET password_hash=%s, is_default_admin=0 WHERE id=%s", (new_hash, user['id']))
            conn.commit()
            flash('Senha alterada com sucesso.')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Erro ao atualizar senha: {e}')
            return redirect(url_for('change_password'))
        finally:
            try:
                cur.close()
                conn.close()
            except:
                pass

    return render_template('change_password.html')

@app.route('/import-emails', methods=['GET'])
@login_required
def import_emails():
    try:
        rowcount = update_job(LOG_DIR, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
        if rowcount is False:
            flash('Nenhum e-mail novo para importar.')
        else:
            flash(f'Importação realizada com sucesso. {rowcount} novos logs inseridos.')
    except Exception as e:
        logging.error(f"Erro ao executar importação manual: {e}")
        flash(f'Erro ao executar importação: {e}')
    return redirect(url_for('index'))

@app.route('/', methods=['GET'])
@login_required
def index():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    search_email = request.args.get('search_email', '').strip()
    search_subject = request.args.get('search_subject', '').strip()
    status_filter = request.args.get('status_filter')
    sort_by = request.args.get('sort_by', 'date')
    sort_order = request.args.get('sort_order', 'desc')

    today = datetime.now(pytz.timezone(TZ)).date().isoformat()

    use_date_filter = bool(start_date or end_date)
    if use_date_filter:
        if start_date and end_date and start_date > end_date:
            logging.warning("Data inicial maior que final; ignorando filtro de data.")
            use_date_filter = False
            start_date = None
            end_date = None
        if start_date and not end_date:
            end_date = start_date
        elif end_date and not start_date:
            start_date = end_date

    use_time_filter = bool(start_time or end_time)
    if use_time_filter:
        if start_time and end_time and start_time > end_time:
            logging.warning("Horário inicial maior que final; ignorando filtro de horário.")
            use_time_filter = False
            start_time = None
            end_time = None
        if start_time and not end_time:
            end_time = start_time
        elif end_time and not start_time:
            start_time = end_time

    is_search = bool(search_email or search_subject)
    if not is_search and not use_date_filter:
        start_date = today
        end_date = today
        use_date_filter = True

    try:
        conn = get_conn(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
        cur = conn.cursor(dictionary=True)

        query = "SELECT * FROM email_logs"
        params = []
        where = []
        if use_date_filter:
            where.append("log_date BETWEEN %s AND %s")
            params.extend([start_date, end_date])
        if use_time_filter:
            where.append("log_time BETWEEN %s AND %s")
            params.extend([start_time, end_time])
        if search_email:
            where.append("to_email LIKE %s")
            params.append(f"%{search_email}%")
        if search_subject:
            where.append("subject LIKE %s")
            params.append(f"%{search_subject}%")
        if status_filter == 'failed':
            where.append("status != 'sent'")
        if where:
            query += " WHERE " + " AND ".join(where)

        order_direction = "ASC" if sort_order == 'asc' else "DESC"
        if sort_by == 'date':
            query += f" ORDER BY log_date {order_direction}, log_time {order_direction}"
        else:
            query += f" ORDER BY log_time {order_direction}, log_date {order_direction}"

        cur.execute(query, params)
        logs = cur.fetchall()
        return render_template('report.html', logs=logs, start_date=start_date, end_date=end_date, start_time=start_time, end_time=end_time,
                               search_email=search_email, search_subject=search_subject, status_filter=status_filter, 
                               sort_by=sort_by, sort_order=sort_order, use_date_filter=use_date_filter, use_time_filter=use_time_filter, auth_mode=AUTH_MODE)

    except Exception as e:
        flash(f'Erro ao consultar o banco de dados: {e}')
        return redirect(url_for('index'))
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

@app.route('/print-report')
@login_required
def print_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    search_email = request.args.get('search_email', '').strip()
    search_subject = request.args.get('search_subject', '').strip()
    status_filter = request.args.get('status_filter')
    sort_by = request.args.get('sort_by', 'date')
    sort_order = request.args.get('sort_order', 'desc')

    today = datetime.now(pytz.timezone(TZ)).date().isoformat()

    use_date_filter = bool(start_date or end_date)
    if use_date_filter:
        if start_date and end_date and start_date > end_date:
            logging.warning("Data inicial maior que final; ignorando filtro de data.")
            use_date_filter = False
            start_date = None
            end_date = None
        if start_date and not end_date:
            end_date = start_date
        elif end_date and not start_date:
            start_date = end_date

    use_time_filter = bool(start_time or end_time)
    if use_time_filter:
        if start_time and end_time and start_time > end_time:
            logging.warning("Horário inicial maior que final; ignorando filtro de horário.")
            use_time_filter = False
            start_time = None
            end_time = None
        if start_time and not end_time:
            end_time = start_time
        elif end_time and not start_time:
            start_time = end_time

    is_search = bool(search_email or search_subject)
    if not is_search and not use_date_filter:
        start_date = today
        end_date = today
        use_date_filter = True

    try:
        conn = get_conn(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
        cur = conn.cursor(dictionary=True)

        query = "SELECT * FROM email_logs"
        params = []
        where = []
        if use_date_filter:
            where.append("log_date BETWEEN %s AND %s")
            params.extend([start_date, end_date])
        if use_time_filter:
            where.append("log_time BETWEEN %s AND %s")
            params.extend([start_time, end_time])
        if search_email:
            where.append("to_email LIKE %s")
            params.append(f"%{search_email}%")
        if search_subject:
            where.append("subject LIKE %s")
            params.append(f"%{search_subject}%")
        if status_filter == 'failed':
            where.append("status != 'sent'")
        if where:
            query += " WHERE " + " AND ".join(where)

        order_direction = "ASC" if sort_order == 'asc' else "DESC"
        if sort_by == 'date':
            query += f" ORDER BY log_date {order_direction}, log_time {order_direction}"
        else:
            query += f" ORDER BY log_time {order_direction}, log_date {order_direction}"

        # Não aplica LIMIT ou OFFSET para incluir todos os resultados
        cur.execute(query, params)
        logs = cur.fetchall()
        return render_template('print_report.html', logs=logs)

    except Exception as e:
        return f"Erro ao consultar o banco de dados: {e}"
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

@app.route('/export-csv')
@login_required
def export_csv():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    search_email = request.args.get('search_email', '').strip()
    search_subject = request.args.get('search_subject', '').strip()
    status_filter = request.args.get('status_filter')
    sort_by = request.args.get('sort_by', 'date')
    sort_order = request.args.get('sort_order', 'desc')

    today = datetime.now(pytz.timezone(TZ)).date().isoformat()

    use_date_filter = bool(start_date or end_date)
    if use_date_filter:
        if start_date and end_date and start_date > end_date:
            logging.warning("Data inicial maior que final; ignorando filtro.")
            use_date_filter = False
            start_date = None
            end_date = None
        if start_date and not end_date:
            end_date = start_date
        elif end_date and not start_date:
            start_date = end_date

    use_time_filter = bool(start_time or end_time)
    if use_time_filter:
        if start_time and end_time and start_time > end_time:
            logging.warning("Horário inicial maior que final; ignorando filtro de horário.")
            use_time_filter = False
            start_time = None
            end_time = None
        if start_time and not end_time:
            end_time = start_time
        elif end_time and not start_time:
            start_time = end_time

    is_search = bool(search_email or search_subject)
    if not is_search and not use_date_filter:
        start_date = today
        end_date = today
        use_date_filter = True

    try:
        conn = get_conn(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
        cur = conn.cursor(dictionary=True)

        query = "SELECT * FROM email_logs"
        params = []
        where = []
        if use_date_filter:
            where.append("log_date BETWEEN %s AND %s")
            params.extend([start_date, end_date])
        if use_time_filter:
            where.append("log_time BETWEEN %s AND %s")
            params.extend([start_time, end_time])
        if search_email:
            where.append("to_email LIKE %s")
            params.append(f"%{search_email}%")
        if search_subject:
            where.append("subject LIKE %s")
            params.append(f"%{search_subject}%")
        if status_filter == 'failed':
            where.append("status != 'sent'")
        if where:
            query += " WHERE " + " AND ".join(where)

        order_direction = "ASC" if sort_order == 'asc' else "DESC"
        if sort_by == 'date':
            query += f" ORDER BY log_date {order_direction}, log_time {order_direction}"
        else:
            query += f" ORDER BY log_time {order_direction}, log_date {order_direction}"

        cur.execute(query, params)
        logs = cur.fetchall()

        # Gerar CSV
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Message ID', 'Data', 'Hora', 'De', 'Para', 'Status', 'Host Origem', 'IP Origem', 'Assunto'])

        for log in logs:
            writer.writerow([
                log['message_id'],
                log['log_date'],
                log['log_time'],
                log['from_email'],
                log['to_email'],
                log['status'],
                log['origin_host'],
                log['origin_ip'],
                log['subject']
            ])

        response = app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=relatorio_emails.csv'}
        )
        return response

    except Exception as e:
        return f"Erro ao consultar o banco de dados: {e}"
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

if __name__ == '__main__':
    setup_database(AUTH_MODE, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
    # Execução inicial
    recs, pend, imp = parse_log(LOG_DIR, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
    insert_database(recs, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
    # Scheduler
    try:
        scheduler_thread = threading.Thread(
            target=run_scheduler, 
            args=(SCHEDULE_TYPE, SCHEDULE_INTERVAL_MINUTES if SCHEDULE_TYPE == 'minutes' else None, 
                  SCHEDULE_TIME if SCHEDULE_TYPE == 'time' else None, LOG_DIR, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT),
            daemon=True
        )
        scheduler_thread.start()
        logging.info("Thread do agendador iniciada com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao iniciar a thread do agendador: {e}")
        raise
    app.run(host='0.0.0.0', port=5000, debug=True)