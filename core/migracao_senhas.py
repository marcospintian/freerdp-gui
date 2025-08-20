import configparser
from core.utils_crypto import encrypt_password
import logging

def migrar_senhas_ini(ini_path: str, logger=None):
    """
    Migra senhas em texto claro no arquivo INI para formato criptografado (hexadecimal).
    Se o campo 'senha' já estiver criptografado, não faz nada.
    """
    config = configparser.ConfigParser()
    config.read(ini_path, encoding='utf-8')
    alterado = False
    for secao in config.sections():
        senha = config[secao].get('senha')
        if senha:
            # Heurística: se não for hexadecimal válido, criptografa
            try:
                bytes.fromhex(senha)
                # Já está criptografado
                continue
            except Exception:
                senha_cripto = encrypt_password(senha)
                config[secao]['senha'] = senha_cripto
                alterado = True
                if logger:
                    logger.info(f"Senha migrada para criptografia na seção [{secao}]")
    if alterado:
        with open(ini_path, 'w', encoding='utf-8') as f:
            config.write(f)
        if logger:
            logger.info("Arquivo INI atualizado com senhas criptografadas.")
    return alterado
