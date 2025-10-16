# **Relatórios SMTP - Clube Naval**

## **Descrição do Projeto**

O **Relatórios SMTP - Clube Naval** é uma aplicação web desenvolvida para o monitoramento e análise de logs de e-mails enviados e falhados em servidores SMTP que utilizam Exim. A solução oferece recursos avançados de importação de logs, visualização de relatórios detalhados e exportação de dados. A aplicação é ideal para organizações que necessitam de um sistema robusto e escalável para gerenciar grandes volumes de logs de e-mail.

Esta aplicação foi projetada com **Docker** para facilitar a implantação e o gerenciamento de ambientes, além de contar com suporte a múltiplos modos de autenticação e agendamento automatizado de tarefas.

---

## **Características Principais**

* **Processamento de Logs**: Leitura e importação de dados dos arquivos `full_subjects.log` e `mail.log`, extraindo informações de e-mails como remetente, destinatário, assunto e status.
* **Relatórios Avançados**: Interface web para exibir relatórios de e-mails enviados, falhados e rejeitados com filtros dinâmicos (data, e-mail, assunto e status).
* **Autenticação Segura**: Suporte para autenticação via **Active Directory (AD)** ou **MySQL**.
* **Agendamento e Automação**: Agendamento de importação de logs em intervalos de minutos ou horários fixos, com execução automática em segundo plano.
* **Dockerização Completa**: Utiliza **Docker** e **Docker Compose** para facilitar a implantação, tanto em ambientes locais quanto em nuvem.

---

## **Tecnologias Utilizadas**

* **Backend**: Python 3.x, Flask
* **Banco de Dados**: MySQL
* **Autenticação**: LDAP (para AD) ou MySQL
* **Agendamento**: `schedule` e `threading` para execução em segundo plano
* **Docker**: Docker Compose para orquestrar os contêineres
* **Frontend**: HTML5, CSS3, JavaScript, Jinja2 (para templates dinâmicos)

---

## **Arquitetura**

A arquitetura do projeto é baseada em contêineres Docker, com a seguinte estrutura:

1. **Backend**: Responsável pelo processamento dos logs, autenticação de usuários e apresentação dos relatórios.
2. **Banco de Dados**: Utiliza MySQL para armazenar os logs de e-mails e as credenciais dos usuários.
3. **Servidor SMTP (Exim)**: Usado para emular um servidor de envio de e-mails, necessário para gerar logs de e-mails no formato Exim.

---

## **Docker Compose: Arquivo Detalhado**

A configuração do **docker-compose.yml** define os serviços que compõem a aplicação, incluindo o **Flask**, o **MySQL** e o **Exim**. Abaixo segue o arquivo `docker-compose.yml` detalhado, com todas as variáveis e explicações sobre cada configuração.

```yaml
version: '3.8'

services:
  # Serviço de Banco de Dados MySQL
  smtp-relay-db:
    image: mysql:5.7
    container_name: smtp-relay-db
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}          # Senha do usuário root do MySQL
      MYSQL_DATABASE: ${DB_NAME}                   # Nome do banco de dados
      MYSQL_USER: ${DB_USER}                       # Usuário do banco de dados
      MYSQL_PASSWORD: ${DB_PASSWORD}               # Senha do usuário do banco de dados
    volumes:
      - smtp-relay-db-data:/var/lib/mysql          # Volume persistente para dados do MySQL
    networks:
      - smtp-relay-network                         # Rede para comunicação entre contêineres

  # Serviço de Backend (Flask)
  smtp-relay-backend:
    build:
      context: .
      dockerfile: Dockerfile                       # Caminho para o Dockerfile que constrói a imagem do backend
    container_name: smtp-relay-backend
    environment:
      DB_HOST: smtp-relay-db                      # Nome do serviço de banco de dados
      DB_USER: ${DB_USER}                          # Usuário para acessar o banco de dados
      DB_PASSWORD: ${DB_PASSWORD}                  # Senha para o banco de dados
      DB_NAME: ${DB_NAME}                          # Nome do banco de dados
      DB_PORT: ${DB_PORT}                          # Porta do banco de dados (default: 3306)
      LOG_DIR: ${LOG_DIR}                          # Diretório onde os logs são armazenados
      TZ: ${TZ}                                    # Fuso horário para a aplicação (exemplo: America/Sao_Paulo)
      SCHEDULE_TYPE: ${SCHEDULE_TYPE}              # Tipo de agendamento: 'minutes' ou 'time'
      SCHEDULE_INTERVAL_MINUTES: ${SCHEDULE_INTERVAL_MINUTES} # Intervalo de agendamento (em minutos)
      SCHEDULE_TIME: ${SCHEDULE_TIME}              # Hora específica do agendamento (caso SCHEDULE_TYPE = 'time')
      AUTH_MODE: ${AUTH_MODE}                      # Modo de autenticação: 'DB' ou 'AD'
      LDAP_HOST: ${LDAP_HOST}                      # Host do servidor LDAP (necessário se AUTH_MODE=AD)
      LDAP_DOMAIN: ${LDAP_DOMAIN}                  # Domínio LDAP (necessário se AUTH_MODE=AD)
      LDAP_BASE_DN: ${LDAP_BASE_DN}                # Base DN do LDAP (necessário se AUTH_MODE=AD)
      LDAP_GROUP_DN: ${LDAP_GROUP_DN}              # Grupo DN do LDAP (necessário se AUTH_MODE=AD)
    depends_on:
      - smtp-relay-db                              # O serviço de backend depende do banco de dados
    ports:
      - "5000:5000"                                # Exposição da porta 5000 para a aplicação Flask
    networks:
      - smtp-relay-network                         # Rede de comunicação entre contêineres
    volumes:
      - ./app:/app                                 # Volume para o código-fonte da aplicação

  # Serviço Exim (SMTP Relay)
  smtp-relay-exim:
    image: learnlinux/exim-relay:latest           # Imagem do servidor SMTP Exim
    container_name: smtp-relay-exim
    environment:
      SMTP_PASSWORD: ${SMTP_PASSWORD}             # Senha do servidor SMTP
    ports:
      - "25:25"                                   # Exposição da porta 25 (SMTP)
    networks:
      - smtp-relay-network                         # Rede de comunicação entre contêineres

# Definição das redes de comunicação entre os contêineres
networks:
  smtp-relay-network:
    driver: bridge                                 # Rede de tipo bridge (padrão do Docker)

# Volumes persistentes para dados do MySQL
volumes:
  smtp-relay-db-data:
    driver: local                                   # Volume persistente para dados do banco de dados
```

### **Explicação das Variáveis no `docker-compose.yml`**

1. **`smtp-relay-db` (Banco de Dados MySQL)**:

   * **image**: A imagem Docker utilizada para o banco de dados MySQL (versão 5.7).
   * **container_name**: Nome do contêiner de banco de dados.
   * **environment**:

     * **MYSQL_ROOT_PASSWORD**: Senha do usuário root no MySQL, definida como uma variável de ambiente.
     * **MYSQL_DATABASE**: Nome do banco de dados utilizado pela aplicação.
     * **MYSQL_USER** e **MYSQL_PASSWORD**: Credenciais para o usuário de acesso ao banco de dados.
   * **volumes**: Define o volume persistente para armazenar os dados do banco de dados MySQL, garantindo que os dados sejam mantidos entre reinicializações de contêineres.
   * **networks**: O contêiner se conecta à rede interna definida no Docker Compose.

2. **`smtp-relay-backend` (Backend Flask)**:

   * **build**:

     * **context**: Diretório onde o Dockerfile está localizado, necessário para a construção da imagem Docker do backend.
     * **dockerfile**: Nome do Dockerfile a ser utilizado.
   * **container_name**: Nome do contêiner que executa a aplicação Flask.
   * **environment**: Variáveis de ambiente que são passadas para o contêiner, configurando aspectos importantes da aplicação, como a conexão com o banco de dados, o agendamento e a autenticação. A maioria dessas variáveis será lida a partir do arquivo `.env` (não é mais necessário, pois tudo está configurado no próprio `docker-compose.yml`):

     * **DB_HOST**: Nome do serviço MySQL (conforme configurado no Docker Compose).
     * **DB_USER, DB_PASSWORD, DB_NAME**: Credenciais de acesso ao banco de dados MySQL.
     * **LOG_DIR**: Diretório onde os logs da aplicação serão armazenados.
     * **TZ**: Fuso horário da aplicação.
     * **SCHEDULE_TYPE**: Tipo de agendamento para a importação de logs (em minutos ou horário fixo).
     * **SCHEDULE_INTERVAL_MINUTES**: Intervalo em minutos para o agendamento, se o tipo for `minutes`.
     * **SCHEDULE_TIME**: Horário específico para o agendamento, se o tipo for `time`.
     * **AUTH_MODE**: Modo de autenticação da aplicação (DB ou AD).
   * **depends_on**: Define que o backend depende do serviço de banco de dados **smtp-relay-db**.
   * **ports**: A aplicação Flask é exposta na porta 5000.
   * **volumes**: O volume mapeado para o código da aplicação, permitindo que o código-fonte seja persistente entre reinicializações.

3. **`smtp-relay-exim` (Exim SMTP Relay)**:

   * **image**: A imagem Docker utilizada para emular um servidor Exim SMTP.
   * **container_name**: Nome do contêiner Exim.
   * **environment**: Definindo a senha do servidor SMTP, necessária para o funcionamento do Exim.
   * **ports**: A porta 25 (SMTP) é exposta para comunicação com clientes externos.

---

## **Execução da Aplicação**

### **1. Baixar e Iniciar a Aplicação**

Após configurar o `docker-compose.yml`, execute o seguinte comando para construir e iniciar a aplicação:

```bash
docker-compose up -d --build
```

Isso irá criar os contêineres para a aplicação Flask, o banco de dados MySQL e o servidor Exim, e inicializar os serviços automaticamente.

### **2. Acessar a Aplicação**

A aplicação estará disponível em **[http://localhost:5000](http://localhost:5000)**. Utilize o navegador para acessar a interface de login.

---

## **Contribuição**

Contribuições são bem-vindas! Para contribuir:

1. **Faça um fork** deste repositório.
2. **Crie uma branch** para sua feature: `git checkout -b feature/nova-feature`.
3. **Faça o commit** das suas alterações: `git commit -m 'Adicionando nova feature'`.
4. **Envie um push** para sua branch: `git push origin feature/nova-feature`.
5. **Abra um pull request**.

---

## **Licença**

Este projeto é licenciado sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## **Suporte**

Para suporte, entre em contato com **Henrique Fagundes** ou envie um e-mail para **[support@henrique.tec.br](mailto:support@henrique.tec.br)**.