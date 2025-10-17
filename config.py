import os
import re
import pytz
import logging

def validate_environment_variables():
    auth_mode = os.environ.get('AUTH_MODE', 'AD').upper()
    if auth_mode not in ['AD', 'DB']:
        raise EnvironmentError("AUTH_MODE inválido. Use 'AD' ou 'DB'.")

    required_common = {
        'DB_HOST': 'Host do banco de dados',
        'DB_USER': 'Usuário do banco de dados',
        'DB_PASSWORD': 'Senha do banco de dados',
        'DB_NAME': 'Nome do banco de dados',
        'LOG_DIR': 'Diretório de logs',
        'TZ': 'Fuso horário',
        'SCHEDULE_TYPE': 'Tipo de agendamento (minutes ou time)',
    }

    required_ldap = {
        'LDAP_HOST': 'Host do servidor LDAP',
        'LDAP_DOMAIN': 'Domínio LDAP',
        'LDAP_BASE_DN': 'Base DN do LDAP',
        'LDAP_GROUP_DN': 'Grupo DN do LDAP',
    } if auth_mode == 'AD' else {}

    required_smtp = {
        'SMTP_SERVER': 'Servidor SMTP',
        'SMTP_PORT': 'Porta SMTP',
        'SMTP_FROM': 'E-mail de origem SMTP',
        'SMTP_FROM_NAME': 'Nome do remetente SMTP',
    } if auth_mode == 'DB' else {}

    required_smtp_authenticated = {
        'SMTP_USERNAME': 'Usuário SMTP',
        'SMTP_PASSWORD': 'Senha SMTP',
        'SMTP_USE_TLS': 'Usar TLS para SMTP (True/False)',
        'SMTP_USE_SSL': 'Usar SSL para SMTP (True/False)',
    } if auth_mode == 'DB' and os.environ.get('SMTP_AUTHENTICATED', 'True') == 'True' else {}

    missing = []
    all_required = {**required_common, **required_ldap, **required_smtp, **required_smtp_authenticated}
    for var, desc in all_required.items():
        v = os.environ.get(var)
        if not v or v.strip() == '':
            missing.append(f"{desc} ({var}) não definida ou vazia")

    tz_value = os.environ.get('TZ')
    if tz_value:
        try:
            pytz.timezone(tz_value)
        except pytz.exceptions.UnknownTimeZoneError:
            missing.append(f"Fuso horário inválido: {tz_value}")

    st = os.environ.get('SCHEDULE_TYPE')
    if st not in ['minutes', 'time']:
        missing.append(f"Tipo de agendamento inválido: {st} (deve ser 'minutes' ou 'time')")

    if st == 'minutes':
        iv = os.environ.get('SCHEDULE_INTERVAL_MINUTES')
        if not iv:
            missing.append("Intervalo (SCHEDULE_INTERVAL_MINUTES) não definido para 'minutes'")
        else:
            try:
                if int(iv) <= 0:
                    missing.append("Intervalo de importação deve ser inteiro positivo")
            except ValueError:
                missing.append("Intervalo de importação deve ser inteiro")
    elif st == 'time':
        tm = os.environ.get('SCHEDULE_TIME')
        if not tm:
            missing.append("Horário específico (SCHEDULE_TIME) não definido para 'time'")
        else:
            if not re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$').match(tm):
                missing.append(f"Horário específico inválido: {tm} (formato HH:MM)")

    # Validação para DB_PORT (opcional, default 3306)
    db_port = os.environ.get('DB_PORT', '3306')
    try:
        db_port_int = int(db_port)
        if not (1 <= db_port_int <= 65535):
            missing.append(f"Porta do banco de dados (DB_PORT) inválida: {db_port} (deve ser entre 1 e 65535)")
    except ValueError:
        missing.append(f"Porta do banco de dados (DB_PORT) deve ser um inteiro: {db_port}")

    if auth_mode == 'DB':
        smtp_port = os.environ.get('SMTP_PORT')
        if not smtp_port or smtp_port.strip() == '':
            missing.append("Porta SMTP (SMTP_PORT) não definida ou vazia")
        else:
            try:
                smtp_port_int = int(smtp_port)
                if not (1 <= smtp_port_int <= 65535):
                    missing.append(f"Porta SMTP inválida: {smtp_port} (deve ser entre 1 e 65535)")
            except ValueError:
                missing.append(f"Porta SMTP deve ser um inteiro: {smtp_port}")

    if missing:
        for m in missing:
            logging.error(m)
        raise EnvironmentError("Falha na inicialização: variáveis de ambiente ausentes ou inválidas.")

    env = {
        'AUTH_MODE': auth_mode,
        'DB_HOST': os.environ['DB_HOST'],
        'DB_USER': os.environ['DB_USER'],
        'DB_PASSWORD': os.environ['DB_PASSWORD'],
        'DB_NAME': os.environ['DB_NAME'],
        'LOG_DIR': os.environ['LOG_DIR'],
        'TZ': os.environ['TZ'],
        'SCHEDULE_TYPE': os.environ['SCHEDULE_TYPE'],
        'DB_PORT': int(db_port),  # Usa o valor validado
    }
    if auth_mode == 'AD':
        env.update({
            'LDAP_HOST': os.environ['LDAP_HOST'],
            'LDAP_DOMAIN': os.environ['LDAP_DOMAIN'],
            'LDAP_BASE_DN': os.environ['LDAP_BASE_DN'],
            'LDAP_GROUP_DN': os.environ['LDAP_GROUP_DN'],
        })
    if auth_mode == 'DB':
        env.update({
            'SMTP_SERVER': os.environ['SMTP_SERVER'],
            'SMTP_PORT': int(os.environ['SMTP_PORT']),
            'SMTP_FROM': os.environ['SMTP_FROM'],
            'SMTP_FROM_NAME': os.environ['SMTP_FROM_NAME'],
            'SMTP_AUTHENTICATED': os.environ.get('SMTP_AUTHENTICATED', 'True') == 'True',
        })
        if env['SMTP_AUTHENTICATED']:
            env.update({
                'SMTP_USERNAME': os.environ['SMTP_USERNAME'],
                'SMTP_PASSWORD': os.environ['SMTP_PASSWORD'],
                'SMTP_USE_TLS': os.environ['SMTP_USE_TLS'] == 'True',
                'SMTP_USE_SSL': os.environ['SMTP_USE_SSL'] == 'True',
            })
    if env['SCHEDULE_TYPE'] == 'minutes':
        env['SCHEDULE_INTERVAL_MINUTES'] = int(os.environ['SCHEDULE_INTERVAL_MINUTES'])
    else:
        env['SCHEDULE_TIME'] = os.environ['SCHEDULE_TIME']
    return env