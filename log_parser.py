import os
import re
from datetime import datetime
import logging
from database import get_conn

EXIM_ID_RE = re.compile(r'\b([0-9A-Za-z]{6,}(?:-[0-9A-Za-z]{2,}){2})\b')
DATE_TIME_RE = re.compile(r'^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})')
COMPLETED_RE = re.compile(r'\bCompleted\b')

def parse_full_subjects(log_path: str) -> dict:
    """Parseia o arquivo full_subjects.log e retorna dict de message_id -> details."""
    messages = {}
    try:
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                # Divide apenas nos primeiros 6 pipes, preservando o Subject
                fields = line.split('|', 6)
                if len(fields) < 7:
                    continue
                fields = [field.strip() for field in fields]
                details = {}
                for field in fields[:-1]:  # Exclui Subject por enquanto
                    if ':' in field:
                        key, value = field.split(':', 1)
                        key = key.strip().lower().replace('-', '_')
                        value = value.strip()
                        details[key] = value
                # Subject é o último campo, após o último pipe
                subject = fields[-1].split(':', 1)[-1].strip() if ':' in fields[-1] else fields[-1].strip()
                if 'message_id' not in details:
                    continue
                msg_id = details['message_id']
                date_str = details.get('date', '')
                try:
                    dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                    log_date = dt.date()
                    log_time = dt.time().strftime("%H:%M:%S")
                except ValueError:
                    logging.warning(f"Formato de data inválido para ID {msg_id}: {date_str}")
                    continue
                from_email = details.get('from', '')
                from_m = re.search(r'<([^>]+)>', from_email)
                if from_m:
                    from_email = from_m.group(1)
                to_email = details.get('to', '')
                host = details.get('origin_host', '')
                ip = details.get('origin_ip', '')
                has_origin = bool(from_email) and bool(host) and bool(ip) and bool(to_email)
                if not has_origin:
                    logging.info(f"ID {msg_id} com origem incompleta ou sem to_email no full_subjects.log; ignorando.")
                    continue
                messages[msg_id] = {
                    'log_date': log_date,
                    'log_time': log_time,
                    'from_email': from_email,
                    'to_email': to_email,
                    'host': host,
                    'ip': ip,
                    'subject': subject
                }
    except FileNotFoundError:
        logging.warning("Arquivo full_subjects.log não encontrado.")
        return {}
    return messages

def list_log_files(log_dir: str):
    """Retorna apenas o arquivo mail.log, se existir."""
    log_path = os.path.join(log_dir, 'mail.log')
    if os.path.exists(log_path):
        return [log_path]
    return []

def parse_log(log_dir, db_host, db_user, db_password, db_name, db_port=3306):
    """
    Importa dados principais (incluindo from, to e subject) do full_subjects.log e confirma status/Completed do mail.log.
    Importa por ID apenas quando:
      - Tem dados completos de origem (incluindo to_email) no full_subjects.log
      - Tem pelo menos uma linha de resultado de envio (=>, -> para sent; ** para rejected) no mail.log
      - Tem linha 'Completed' do mesmo ID no mail.log
    Status agregado: 'rejected' se houver qualquer reject; senão 'sent'.
    Verifica se o message_id já existe no DB; se sim, ignora o ID.
    NÃO modifica, grava, renomeia ou apaga os arquivos.
    Gera apenas um registro por ID.
    """
    records = []
    imported_ids = set()
    pending_ids = set()

    # Parseia full_subjects.log para dados principais
    full_path = os.path.join(log_dir, 'full_subjects.log')
    messages = parse_full_subjects(full_path)
    if not messages:
        logging.warning("Nenhum dado válido encontrado em full_subjects.log.")
        return records, pending_ids, imported_ids

    logging.info(f"{len(messages)} IDs encontrados em full_subjects.log.")

    # Parseia mail.log para status e Completed
    all_logs = list_log_files(log_dir)
    if not all_logs:
        logging.warning("Arquivo mail.log não encontrado em LOG_DIR.")
        return records, pending_ids, imported_ids

    groups = {}  # msg_id -> {'has_delivery': bool, 'has_reject': bool, 'completed': bool}

    for log_path in all_logs:
        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                for raw in f:
                    line = raw.rstrip('\n').rstrip('\r')
                    if not line.strip():
                        continue
                    dtm = DATE_TIME_RE.match(line)
                    if not dtm:
                        continue
                    idm = EXIM_ID_RE.search(line)
                    if not idm:
                        continue
                    msg_id = idm.group(1)
                    kind = 'other'
                    if ' ** ' in line:
                        kind = 'reject'
                    elif ' => ' in line or ' -> ' in line:
                        kind = 'delivery'
                    elif COMPLETED_RE.search(line):
                        kind = 'completed'
                    if kind == 'other':
                        continue
                    groups.setdefault(msg_id, {'has_delivery': False, 'has_reject': False, 'completed': False})
                    if kind == 'completed':
                        groups[msg_id]['completed'] = True
                    elif kind == 'delivery':
                        groups[msg_id]['has_delivery'] = True
                    elif kind == 'reject':
                        groups[msg_id]['has_reject'] = True
        except FileNotFoundError:
            continue

    # Verificação de existência no DB (em batch)
    if messages:
        try:
            conn = get_conn(db_host, db_user, db_password, db_name, db_port)
            cur = conn.cursor()
            ids = list(messages.keys())
            placeholders = ','.join(['%s'] * len(ids))
            cur.execute(f"SELECT DISTINCT message_id FROM email_logs WHERE message_id IN ({placeholders})", ids)
            existing_ids = set(row[0] for row in cur.fetchall())
            cur.close()
            conn.close()
        except Exception as e:
            logging.error(f"Erro ao verificar IDs existentes no DB: {e}")
            existing_ids = set()
    else:
        existing_ids = set()

    # Consolidação por ID com critérios
    for msg_id, details in messages.items():
        if msg_id in existing_ids:
            logging.debug(f"ID {msg_id} já existe no DB; ignorando.")
            continue
        if msg_id not in groups or not groups[msg_id]['completed']:
            pending_ids.add(msg_id)
            logging.info(f"ID pendente {msg_id}: sem Completed no mail.log.")
            continue
        has_result = groups[msg_id]['has_delivery'] or groups[msg_id]['has_reject']
        if not has_result:
            pending_ids.add(msg_id)
            logging.info(f"ID pendente {msg_id}: sem resultado de envio (delivery ou reject).")
            continue
        status = 'rejected' if groups[msg_id]['has_reject'] else 'sent'
        log_date = details['log_date']
        log_time = details['log_time']
        from_email = details['from_email']
        to_email = details['to_email']
        host = details['host']
        ip = details['ip']
        subject = details['subject']
        records.append((msg_id, log_date, log_time, from_email, to_email, status, host, ip, subject))
        imported_ids.add(msg_id)

    logging.info(
        f"Resumo: IDs total={len(messages)}, importados={len(imported_ids)}, pendentes={len(pending_ids)}, registros={len(records)}"
    )
    return records, pending_ids, imported_ids