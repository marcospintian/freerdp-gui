import os
import tempfile
import configparser
from core.utils_crypto import encrypt_password, decrypt_password

def test_senha_nunca_em_texto_claro():
    senha_teste = "MinhaSenhaUltraSecreta123!"
    nome_servidor = "ServidorTeste"
    usuario = "usuario"
    ip = "192.168.0.1:3389"

    # Cria arquivo INI temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ini') as tmp:
        ini_path = tmp.name
    try:
        config = configparser.ConfigParser()
        senha_cripto = encrypt_password(senha_teste)
        config[nome_servidor] = {"ip": ip, "usuario": usuario, "senha": senha_cripto}
        with open(ini_path, 'w') as f:
            config.write(f)

        # Verifica se a senha em texto claro NÃO aparece no arquivo
        with open(ini_path, 'r') as f:
            conteudo = f.read()
            assert senha_teste not in conteudo, "A senha em texto claro foi encontrada no arquivo!"
            assert senha_cripto in conteudo, "A senha criptografada não foi encontrada no arquivo!"

        # Testa se a descriptografia funciona
        config2 = configparser.ConfigParser()
        config2.read(ini_path)
        senha_lida = config2[nome_servidor]['senha']
        senha_descriptografada = decrypt_password(senha_lida)
        assert senha_descriptografada == senha_teste, "A senha descriptografada não bate com a original!"
    finally:
        os.remove(ini_path)

def run():
    test_senha_nunca_em_texto_claro()
    print("Teste de segurança de senha passou com sucesso!")

if __name__ == "__main__":
    run()
