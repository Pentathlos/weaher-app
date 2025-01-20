import logging
import datetime

logging.basicConfig(
    filename='access.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

def log_request(handler):
    log_message = f"Requête reçue : {handler.path} à {datetime.datetime.now()}"
    ip_address = handler.client_address[0]
    logging.info(log_message)
    logging.info(f"Adresse IP du client : {ip_address}")
