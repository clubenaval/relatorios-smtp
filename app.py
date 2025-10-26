import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import validate_environment_variables
from database import get_conn, setup_database, insert_database
from log_parser import parse_log
from scheduler import update_job, run_scheduler
from auth import authenticate, login_required
from datetime import datetime, timedelta
import pytz
import threading
import csv
import io
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

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
    if AUTH_MODE == 'DB':
        app.config['MAIL_SERVER'] = env_vars['SMTP_SERVER']
        app.config['MAIL_PORT'] = env_vars['SMTP_PORT']
        app.config['MAIL_DEFAULT_SENDER'] = (env_vars['SMTP_FROM_NAME'], env_vars['SMTP_FROM'])
        if env_vars['SMTP_AUTHENTICATED']:
            app.config['MAIL_USERNAME'] = env_vars['SMTP_USERNAME']
            app.config['MAIL_PASSWORD'] = env_vars['SMTP_PASSWORD']
            app.config['MAIL_USE_TLS'] = env_vars['SMTP_USE_TLS']
            app.config['MAIL_USE_SSL'] = env_vars['SMTP_USE_SSL']
        mail = Mail(app)
        serializer = URLSafeTimedSerializer(app.secret_key)
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
        auth_result = authenticate(username, password, AUTH_MODE, 
                        ldap_host=LDAP_HOST if AUTH_MODE == 'AD' else None,
                        ldap_domain=LDAP_DOMAIN if AUTH_MODE == 'AD' else None,
                        ldap_base_dn=LDAP_BASE_DN if AUTH_MODE == 'AD' else None,
                        ldap_group_dn=LDAP_GROUP_DN if AUTH_MODE == 'AD' else None,
                        db_host=DB_HOST, db_user=DB_USER, db_password=DB_PASSWORD, db_name=DB_NAME, db_port=DB_PORT)
        if AUTH_MODE == 'AD':
            if auth_result:
                session['logged_in'] = True
                session['username'] = username
                session['is_admin'] = False  # No modo AD, assumimos que não há admins DB; ajuste se necessário
                session.pop('_flashes', None)  # Limpa mensagens flash após login
                return redirect(url_for('index'))
        else:
            if auth_result:
                session['logged_in'] = True
                session['username'] = username
                session['is_admin'] = bool(auth_result['is_admin'])
                session.pop('_flashes', None)  # Limpa mensagens flash após login
                return redirect(url_for('index'))
        flash('Credenciais inválidas. Tente novamente.')
    return render_template('login.html', auth_mode=AUTH_MODE)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if AUTH_MODE != 'DB':
        return redirect(url_for('login'))
    if request.method == 'POST':
        email = request.form['email']
        try:
            conn = get_conn(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id FROM app_users WHERE email=%s", (email,))
            user = cur.fetchone()
            if user:
                token = serializer.dumps({'user_id': user['id']}, salt='password-reset')
                expires = datetime.now(pytz.timezone(TZ)) + timedelta(hours=1)
                cur.execute("UPDATE app_users SET reset_token=%s, reset_expires=%s WHERE id=%s", (token, expires, user['id']))
                conn.commit()
                msg = Message('Recuperação de Senha - Clube Naval', recipients=[email])
                msg.body = f'Para resetar sua senha, acesse o link: {url_for("reset_password", token=token, _external=True)}\nEste link expira em 1 hora. Se você não solicitou isso, ignore este e-mail.'
                mail.send(msg)
                flash('Um e-mail com instruções para resetar a senha foi enviado.')
            else:
                flash('E-mail não cadastrado na base de dados.')
            cur.close()
            conn.close()
        except Exception as e:
            flash('Erro ao processar a solicitação.')
            logging.error(f"Erro em forgot_password: {e}")
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if AUTH_MODE != 'DB':
        return redirect(url_for('login'))
    try:
        data = serializer.loads(token, salt='password-reset', max_age=3600)
        user_id = data['user_id']
        conn = get_conn(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT reset_expires FROM app_users WHERE id=%s AND reset_token=%s", (user_id, token))
        user = cur.fetchone()
        tz = pytz.timezone(TZ)
        now_aware = datetime.now(tz)
        if not user or (user['reset_expires'] is not None and tz.localize(user['reset_expires']) < now_aware):
            flash('O link de recuperação expirou ou é inválido.')
            cur.close()
            conn.close()
            return redirect(url_for('login'))
    except SignatureExpired:
        flash('O link de recuperação expirou.')
        return redirect(url_for('login'))
    except BadSignature:
        flash('Link de recuperação inválido.')
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('As senhas não coincidem.')
            return redirect(url_for('reset_password', token=token))
        try:
            conn = get_conn(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
            cur = conn.cursor()
            pwd_hash = generate_password_hash(new_password)
            cur.execute("UPDATE app_users SET password_hash=%s, reset_token=NULL, reset_expires=NULL WHERE id=%s", (pwd_hash, user_id))
            conn.commit()
            flash('Senha atualizada com sucesso. Faça login.')
            cur.close()
            conn.close()
            return redirect(url_for('login'))
        except Exception as e:
            flash('Erro ao atualizar a senha.')
            logging.error(f"Erro em reset_password: {e}")
    return render_template('reset_password.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Logout realizado com sucesso.')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    start_date = request.args.get('start_date', datetime.now(pytz.timezone(TZ)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now(pytz.timezone(TZ)).strftime('%Y-%m-%d'))
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    search_email = request.args.get('search_email')
    search_subject = request.args.get('search_subject')
    status_filter = request.args.get('status_filter', 'all')
    sort_by = request.args.get('sort_by', 'date')
    sort_order = request.args.get('sort_order', 'desc')
    auto_refresh = request.args.get('auto_refresh', 'false') == 'true'

    use_date_filter = start_date and end_date
    use_time_filter = start_time and end_time

    if use_date_filter:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de data inválido.')
            return redirect(url_for('index'))

    if use_time_filter:
        try:
            start_time = datetime.strptime(start_time, '%H:%M').time()
            end_time = datetime.strptime(end_time, '%H:%M').time()
        except ValueError:
            flash('Formato de hora inválido.')
            return redirect(url_for('index'))

    try:
        conn = get_conn(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
        cur = conn.cursor(dictionary=True)
        count_query = "SELECT COUNT(*) as total FROM email_logs"
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
            count_query += " WHERE " + " AND ".join(where)
        cur.execute(count_query, params)
        total = cur.fetchone()['total']
        total_pages = (total + per_page - 1) // per_page

        query = "SELECT id, message_id, log_date, log_time, from_email, to_email, subject, status, origin_host, origin_ip FROM email_logs"
        if where:
            query += " WHERE " + " AND ".join(where)

        order_direction = "ASC" if sort_order == 'asc' else "DESC"
        if sort_by == 'date':
            query += f" ORDER BY log_date {order_direction}, id {order_direction}"
        elif sort_by == 'time':
            query += f" ORDER BY log_time {order_direction}, id {order_direction}"
        else:
            query += f" ORDER BY log_date DESC, id DESC"

        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])

        cur.execute(query, params)
        logs = cur.fetchall()
        cur.close()
        conn.close()

        now = datetime.now(pytz.timezone(TZ)).strftime('%d/%m/%Y %H:%M:%S')

        return render_template('report.html',
                               logs=logs,
                               page=page,
                               total_pages=total_pages,
                               start_date=start_date.strftime('%Y-%m-%d') if use_date_filter else datetime.now(pytz.timezone(TZ)).strftime('%Y-%m-%d'),
                               end_date=end_date.strftime('%Y-%m-%d') if use_date_filter else datetime.now(pytz.timezone(TZ)).strftime('%Y-%m-%d'),
                               start_time=start_time.strftime('%H:%M') if use_time_filter else '',
                               end_time=end_time.strftime('%H:%M') if use_time_filter else '',
                               search_email=search_email or '',
                               search_subject=search_subject or '',
                               status_filter=status_filter,
                               sort_by=sort_by,
                               sort_order=sort_order,
                               auto_refresh=auto_refresh,
                               auth_mode=AUTH_MODE,
                               now=now)
    except Exception as e:
        flash(f'Erro ao consultar o banco de dados: {e}')
        return redirect(url_for('index'))

@app.route('/import_emails', methods=['GET'])
@login_required
def import_emails():
    rowcount = update_job(LOG_DIR, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
    if rowcount is not False:
        flash(f'{rowcount} novos logs importados com sucesso.')
    else:
        flash('Nenhum novo log encontrado ou erro na importação.')
    return redirect(url_for('index'))

@app.route('/manage', methods=['GET'])
@login_required
def manage():
    if AUTH_MODE != 'DB' or not session.get('is_admin'):
        flash('Acesso negado.')
        return redirect(url_for('index'))
    try:
        conn = get_conn(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, username, email, is_admin FROM app_users")
        users = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('manage.html', users=users, current_username=session['username'], auth_mode=AUTH_MODE)
    except Exception as e:
        flash(f'Erro ao listar usuários: {e}')
        return redirect(url_for('index'))

@app.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    if AUTH_MODE != 'DB' or not session.get('is_admin'):
        flash('Acesso negado.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        is_admin = 'is_admin' in request.form
        if password != confirm_password:
            flash('As senhas não coincidem.')
            return redirect(url_for('create_user'))
        try:
            conn = get_conn(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
            cur = conn.cursor()
            pwd_hash = generate_password_hash(password)
            cur.execute(
                "INSERT INTO app_users (username, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)",
                (username, email or None, pwd_hash, int(is_admin))
            )
            conn.commit()
            flash('Usuário criado com sucesso.')
            cur.close()
            conn.close()
            return redirect(url_for('manage'))
        except Error as e:
            if 'Duplicate entry' in str(e):
                flash('Usuário já existe.')
            else:
                flash('Erro ao criar usuário.')
            return redirect(url_for('create_user'))
    return render_template('create_user.html')

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if AUTH_MODE != 'DB' or not session.get('is_admin'):
        flash('Acesso negado.')
        return redirect(url_for('index'))
    try:
        conn = get_conn(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, username, email, is_admin FROM app_users WHERE id=%s", (user_id,))
        user = cur.fetchone()
        if not user:
            flash('Usuário não encontrado.')
            return redirect(url_for('manage'))
        if request.method == 'POST':
            email = request.form['email']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            is_admin = 'is_admin' in request.form
            if new_password and new_password != confirm_password:
                flash('As senhas não coincidem.')
                return redirect(url_for('edit_user', user_id=user_id))
            update_query = "UPDATE app_users SET email=%s, is_admin=%s"
            params = [email or None, int(is_admin)]
            if new_password:
                pwd_hash = generate_password_hash(new_password)
                update_query += ", password_hash=%s"
                params.append(pwd_hash)
            update_query += " WHERE id=%s"
            params.append(user_id)
            cur.execute(update_query, params)
            conn.commit()
            flash('Usuário atualizado com sucesso.')
            return redirect(url_for('manage'))
        return render_template('edit_user.html', user=user)
    except Exception as e:
        flash(f'Erro ao editar usuário: {e}')
        return redirect(url_for('manage'))
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if AUTH_MODE != 'DB' or not session.get('is_admin'):
        flash('Acesso negado.')
        return redirect(url_for('index'))
    try:
        conn = get_conn(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
        cur = conn.cursor()
        cur.execute("SELECT username FROM app_users WHERE id=%s", (user_id,))
        user = cur.fetchone()
        if user and user[0] == session['username']:
            flash('Não é possível excluir o próprio usuário.')
            return redirect(url_for('manage'))
        cur.execute("DELETE FROM app_users WHERE id=%s", (user_id,))
        conn.commit()
        flash('Usuário excluído com sucesso.')
    except Exception as e:
        flash(f'Erro ao excluir usuário: {e}')
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass
    return redirect(url_for('manage'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if AUTH_MODE != 'DB':
        flash('Alteração de senha não disponível no modo AD.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('As novas senhas não coincidem.')
            return redirect(url_for('change_password'))
        try:
            conn = get_conn(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT password_hash FROM app_users WHERE username=%s", (session['username'],))
            user = cur.fetchone()
            if not check_password_hash(user['password_hash'], current_password):
                flash('Senha atual incorreta.')
                return redirect(url_for('change_password'))
            pwd_hash = generate_password_hash(new_password)
            cur.execute("UPDATE app_users SET password_hash=%s WHERE username=%s", (pwd_hash, session['username']))
            conn.commit()
            flash('Senha alterada com sucesso.')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Erro ao alterar senha: {e}')
        finally:
            try:
                cur.close()
                conn.close()
            except:
                pass
    return render_template('change_password.html')

@app.route('/print-report')
@login_required
def print_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    search_email = request.args.get('search_email')
    search_subject = request.args.get('search_subject')
    status_filter = request.args.get('status_filter', 'all')
    sort_by = request.args.get('sort_by', 'date')
    sort_order = request.args.get('sort_order', 'desc')

    use_date_filter = start_date and end_date
    use_time_filter = start_time and end_time

    if use_date_filter:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de data inválido.')
            return redirect(url_for('index'))

    if use_time_filter:
        try:
            start_time = datetime.strptime(start_time, '%H:%M').time()
            end_time = datetime.strptime(end_time, '%H:%M').time()
        except ValueError:
            flash('Formato de hora inválido.')
            return redirect(url_for('index'))

    try:
        conn = get_conn(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
        cur = conn.cursor(dictionary=True)

        query = "SELECT id, message_id, log_date, log_time, from_email, to_email, subject, status, origin_host, origin_ip FROM email_logs"
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
            query += f" ORDER BY log_date {order_direction}, id {order_direction}"
        elif sort_by == 'time':
            query += f" ORDER BY log_time {order_direction}, id {order_direction}"
        else:
            query += f" ORDER BY log_date DESC, id DESC"

        cur.execute(query, params)
        logs = cur.fetchall()
        cur.close()
        conn.close()

        return render_template('print_report.html', logs=logs)
    except Exception as e:
        return f"Erro ao consultar o banco de dados: {e}"

@app.route('/export-csv')
@login_required
def export_csv():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    search_email = request.args.get('search_email')
    search_subject = request.args.get('search_subject')
    status_filter = request.args.get('status_filter', 'all')
    sort_by = request.args.get('sort_by', 'date')
    sort_order = request.args.get('sort_order', 'desc')

    use_date_filter = start_date and end_date
    use_time_filter = start_time and end_time

    if use_date_filter:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return "Formato de data inválido."

    if use_time_filter:
        try:
            start_time = datetime.strptime(start_time, '%H:%M').time()
            end_time = datetime.strptime(end_time, '%H:%M').time()
        except ValueError:
            return "Formato de hora inválido."

    try:
        conn = get_conn(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
        cur = conn.cursor(dictionary=True)

        query = "SELECT id, message_id, log_date, log_time, from_email, to_email, subject, status, origin_host, origin_ip FROM email_logs"
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
            query += f" ORDER BY log_date {order_direction}, id {order_direction}"
        elif sort_by == 'time':
            query += f" ORDER BY log_time {order_direction}, id {order_direction}"
        else:
            query += f" ORDER BY log_date DESC, id DESC"

        cur.execute(query, params)
        logs = cur.fetchall()

        # Gerar CSV
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['ID', 'Data', 'Hora', 'De', 'Para', 'Host Origem', 'IP Origem', 'Assunto', 'Status'])

        for log in logs:
            # Converter status 'sent' para 'Enviado'
            status = 'Enviado' if log['status'] == 'sent' else log['status']
            # Converter formato da data de YYYY-MM-DD para DD/MM/YYYY
            log_date = datetime.strptime(str(log['log_date']), '%Y-%m-%d').strftime('%d/%m/%Y')
            writer.writerow([
                log['id'],
                log_date,
                log['log_time'],
                log['from_email'],
                log['to_email'],
                log['origin_host'],
                log['origin_ip'],
                log['subject'],
                status
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
    from database import wait_for_db
    wait_for_db(DB_HOST, DB_USER, DB_PASSWORD, DB_PORT)
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