import mysql.connector
from mysql.connector import Error
import ldap3
import logging
from database import get_conn
from werkzeug.security import check_password_hash

def authenticate_ad(username, password, ldap_host, ldap_domain, ldap_base_dn, ldap_group_dn):
    if not password:
        return False
    user_dn = f"{username}{ldap_domain}"
    try:
        server = ldap3.Server(ldap_host)
        conn = ldap3.Connection(server, user=user_dn, password=password, auto_bind=True)
        if not conn.bind():
            return False
        search_filter = f"(&(objectClass=user)(memberOf={ldap_group_dn})(sAMAccountName={username}))"
        conn.search(ldap_base_dn, search_filter, attributes=['cn'])
        return bool(conn.entries)
    except Exception:
        return False

def authenticate_db(username, password, db_host, db_user, db_password, db_name, db_port=3306):
    try:
        conn = get_conn(db_host, db_user, db_password, db_name, db_port)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, username, password_hash, is_admin FROM app_users WHERE username=%s", (username,))
        user = cur.fetchone()
        if not user:
            return None
        if check_password_hash(user['password_hash'], password):
            return user  # Retorna o dict completo do usuário, incluindo is_admin
        return None
    except Error:
        return None
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

def authenticate(username, password, auth_mode, **kwargs):
    if auth_mode == 'AD':
        return authenticate_ad(
            username, password, 
            kwargs.get('ldap_host'), 
            kwargs.get('ldap_domain'), 
            kwargs.get('ldap_base_dn'), 
            kwargs.get('ldap_group_dn')
        )
    else:
        return authenticate_db(
            username, password, 
            kwargs.get('db_host'), 
            kwargs.get('db_user'), 
            kwargs.get('db_password'), 
            kwargs.get('db_name'),
            kwargs.get('db_port', 3306)
        )

def login_required(f):
    def wrap(*args, **kwargs):
        from flask import session, flash, redirect, url_for
        if 'logged_in' not in session:
            flash('Por favor, faça login para acessar.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap