import schedule
import time
import logging
from log_parser import parse_log
from database import insert_database

def update_job(log_dir, db_host, db_user, db_password, db_name, db_port=3306):
    records, pending_ids, imported_ids = parse_log(log_dir, db_host, db_user, db_password, db_name, db_port)
    return insert_database(records, db_host, db_user, db_password, db_name, db_port)

def run_scheduler(schedule_type, schedule_interval_minutes, schedule_time, log_dir, db_host, db_user, db_password, db_name, db_port=3306):
    try:
        if schedule_type == 'minutes':
            schedule.every(schedule_interval_minutes).minutes.do(
                update_job, log_dir=log_dir, db_host=db_host, db_user=db_user, db_password=db_password, db_name=db_name, db_port=db_port
            )
            logging.info(f"Scheduler configurado: a cada {schedule_interval_minutes} minutos.")
        else:
            schedule.every().day.at(schedule_time).do(
                update_job, log_dir=log_dir, db_host=db_host, db_user=db_user, db_password=db_password, db_name=db_name, db_port=db_port
            )
            logging.info(f"Scheduler configurado: diariamente às {schedule_time}.")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except Exception as e:
                logging.error(f"Erro ao executar schedule.run_pending(): {e}")
                time.sleep(60)  # Aguarda antes de tentar novamente
    except Exception as e:
        logging.error(f"Erro ao iniciar o agendador: {e}")
        raise