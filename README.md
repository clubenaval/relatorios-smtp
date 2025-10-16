# Relatórios SMTP - Clube Naval

## Visão Geral

O **Relatórios SMTP - Clube Naval** é uma aplicação web desenvolvida para processar e exibir relatórios de logs de e-mails enviados e falhados, extraídos exclusivamente do arquivo `mail.log` gerado por um servidor SMTP Exim. A aplicação é construída com Flask (Python), utiliza um banco de dados MySQL para armazenar os logs processados e suporta autenticação via banco local (DB) ou Active Directory/LDAP. O sistema é conteinerizado com Docker, facilitando sua implantação e manutenção.

Esta solução foi projetada para funcionar especificamente com a imagem `aprendendolinux/exim-relay:latest`, que inclui customizações essenciais, como a decodificação automática de assuntos MIME/octais no arquivo `mail.log`, necessária para o correto processamento dos logs pela aplicação.

### Funcionalidades Principais
- **Processamento de Logs**: Lê exclusivamente o arquivo `mail.log` de um diretório configurável, extrai informações de e-mails (data, hora, remetente, destinatário, assunto, status, host/IP de origem) e armazena no banco de dados, evitando duplicatas com base no `message_id`.
- **Relatórios Web**: Interface web para consulta de logs com filtros por data, e-mail destinatário, assunto e status (enviados/falhados), incluindo paginação e ordenação por data ou hora (padrão: mais recentes primeiro).
- **Autenticação**: Suporta autenticação local via MySQL (padrão: usuário `admin`, senha `admin`) ou Active Directory/LDAP, restringindo acesso a membros de um grupo específico.
- **Agendamento Automático**: Processa logs automaticamente com duas opções configuráveis:
  - **Por Intervalo de Minutos**: Executa a cada X minutos, definido pela variável `SCHEDULE_INTERVAL_MINUTES`.
  - **Em Horário Específico**: Executa diariamente em um horário específico (formato HH:MM), definido pela variável `SCHEDULE_TIME`.
  - **Nota**: A aplicação **não modifica, trunca ou reescreve** o arquivo `mail.log`. O gerenciamento do tamanho do arquivo deve ser feito externamente via `logrotate`.
- **Segurança**: Proteção contra cache de páginas sensíveis, validação rigorosa de variáveis de ambiente e mensagens de erro amigáveis.

## Tecnologias Utilizadas
- **Backend**: Python 3.12, Flask
- **Banco de Dados**: MySQL 5.7.44
- **Autenticação**: LDAP/Active Directory (biblioteca `ldap3`) ou autenticação local via MySQL
- **Outras Bibliotecas**: `mysql-connector-python`, `schedule`, `pytz`, `werkzeug`
- **Conteinerização**: Docker, Docker Compose
- **Frontend**: HTML, CSS, Jinja2 (templates Flask), fontes Google (Roboto)
- **SMTP**: Exim4 (via imagem `aprendendolinux/exim-relay:latest`)

## Pré-requisitos
- **Docker** e **Docker Compose** instalados.
- Servidor SMTP Exim configurado usando a imagem `aprendendolinux/exim-relay:latest`, que gera o arquivo `mail.log` com assuntos decodificados (requer variável `DECODE_SUBJECT=yes`).
- Opcionalmente, um servidor LDAP/Active Directory configurado e acessível (se `AUTH_MODE=AD`).
- Arquivo `mail.log` no formato compatível com Exim, contendo linhas com `message_id`, `from=`, `to=`, `status=`, `client=`, e `T=` (assunto decodificado).
- Diretórios para armazenar logs e dados do MySQL com permissões adequadas (ex.: `/srv/smtp-relay/logs`, `/srv/smtp-relay/db`).

## Estrutura do Projeto
```
relatorios-smtp/
├── Dockerfile
├── docker-compose.yml
├── app.py
├── templates/
│   ├── login.html
│   ├── report.html
├── static/
│   ├── logo.png
```

- **`Dockerfile`**: Define a imagem Docker para a aplicação Flask.
- **`docker-compose.yml`**: Configura os serviços `smtp-relay` (Exim), `smtp-relay-db` (MySQL) e `smtp-relay-frontend` (Flask).
- **`app.py`**: Código principal da aplicação Flask, responsável por ler o `mail.log`, importar para o banco e servir a interface web.
- **`templates/`**: Contém os templates HTML (`login.html` e `report.html`).
- **`static/`**: Arquivos estáticos, como o `logo.png`.

## Configuração

### 1. Clonar o Repositório
```bash
git clone https://github.com/clubenaval/relatorios-smtp.git
cd relatorios-smtp
```

### 2. Configurar Variáveis de Ambiente
Edite o arquivo `docker-compose.yml` com as variáveis de ambiente necessárias. Um exemplo está abaixo (substitua os valores fictícios pelos reais, preferencialmente usando um arquivo `.env` para dados sensíveis):

```yaml
services:
  smtp-relay:
    image: aprendendolinux/exim-relay:latest
    restart: always
    container_name: smtp-relay
    hostname: smtp-relay
    environment:
      - SMTP_SERVER=smtp-relay.example.com
      - SMTP_PORT=587
      - SMTP_USERNAME=user@example.com
      - SMTP_PASSWORD=xxxxxxxxxxxxxxxx
      - SERVER_HOSTNAME=mail.example.com
      - RELAY_NETS=0.0.0.0/0
      - TZ=America/Sao_Paulo
      - DECODE_SUBJECT=yes
      - DECODE_DEBUG=yes
    volumes:
      - /srv/smtp-relay/logs:/var/log/exim4
    ports:
      - 25:25

  smtp-relay-db:
    image: mysql:5.7.44
    restart: always
    container_name: smtp-relay-db
    hostname: smtp-relay-db
    environment:
      - MYSQL_ROOT_PASSWORD=senha_forte_123
      - MYSQL_DATABASE=smtp_cpd
      - MYSQL_USER=app_user
      - MYSQL_PASSWORD=senha_forte_456
    volumes:
      - /srv/smtp-relay/db:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10

  smtp-relay-frontend:
    image: clubenaval/relatorios-smtp:latest
    restart: always
    container_name: smtp-relay-frontend
    hostname: smtp-relay-frontend
    environment:
      - DB_HOST=smtp-relay-db
      - DB_USER=root
      - DB_PASSWORD=senha_forte_123
      - DB_NAME=smtp_cpd
      - LOG_DIR=/app/logs
      - TZ=America/Sao_Paulo
      - AUTH_MODE=DB
      - SCHEDULE_TYPE=minutes
      - SCHEDULE_INTERVAL_MINUTES=2
    volumes:
      - /srv/smtp-relay/logs/mail.log:/app/logs/mail.log
    ports:
      - "5000:5000"
    depends_on:
      smtp-relay-db:
        condition: service_healthy
```

#### Variáveis de Ambiente Obrigatórias
| Variável                    | Descrição                                              | Exemplo                          |
|-----------------------------|-------------------------------------------------------|----------------------------------|
| `SMTP_SERVER`               | Hostname do servidor SMTP externo para relay           | `smtp-relay.example.com`         |
| `SMTP_PORT`                 | Porta do servidor SMTP externo (587 para STARTTLS)     | `587`                            |
| `SMTP_USERNAME`             | Usuário para autenticação SMTP                        | `user@example.com`               |
| `SMTP_PASSWORD`             | Senha ou app password para autenticação SMTP           | `xxxxxxxxxxxxxxxx`               |
| `SERVER_HOSTNAME`           | FQDN do servidor Exim para HELO/EHLO                  | `mail.example.com`               |
| `RELAY_NETS`                | Redes permitidas para relay (ex.: CIDR)                | `0.0.0.0/0` (restrinja em produção) |
| `TZ`                        | Fuso horário para timestamps (Exim e app)             | `America/Sao_Paulo`              |
| `DECODE_SUBJECT`            | Ativa decodificação de assuntos no `mail.log`          | `yes`                            |
| `DECODE_DEBUG`              | Ativa logs de depuração para decodificação             | `yes`                            |
| `MYSQL_ROOT_PASSWORD`       | Senha do usuário root do MySQL                        | `senha_forte_123`                |
| `MYSQL_DATABASE`            | Nome do banco de dados MySQL                          | `smtp_cpd`                       |
| `MYSQL_USER`                | Usuário adicional do MySQL                            | `app_user`                       |
| `MYSQL_PASSWORD`            | Senha do usuário adicional do MySQL                   | `senha_forte_456`                |
| `DB_HOST`                   | Host do banco de dados MySQL                          | `smtp-relay-db`                  |
| `DB_USER`                   | Usuário para conexão ao MySQL                         | `root`                           |
| `DB_PASSWORD`               | Senha do usuário MySQL                                | `senha_forte_123`                |
| `DB_NAME`                   | Nome do banco de dados a conectar                     | `smtp_cpd`                       |
| `LOG_DIR`                   | Diretório interno onde o `mail.log` é montado          | `/app/logs`                      |
| `AUTH_MODE`                 | Modo de autenticação (`DB` ou `AD`)                   | `DB`                             |
| `LDAP_HOST`                 | Endereço do servidor LDAP/AD (se `AUTH_MODE=AD`)      | `192.168.1.100`                  |
| `LDAP_DOMAIN`               | Domínio do LDAP (se `AUTH_MODE=AD`)                   | `@example.com`                   |
| `LDAP_BASE_DN`              | Base DN para buscas LDAP (se `AUTH_MODE=AD`)          | `DC=example,DC=com`              |
| `LDAP_GROUP_DN`             | DN do grupo que autoriza acesso (se `AUTH_MODE=AD`)   | `CN=Users,DC=example,DC=com`     |
| `SCHEDULE_TYPE`             | Tipo de agendamento: `minutes` ou `time`              | `minutes`                        |
| `SCHEDULE_INTERVAL_MINUTES` | Intervalo em minutos (se `SCHEDULE_TYPE=minutes`)     | `2`                              |
| `SCHEDULE_TIME`             | Horário diário (se `SCHEDULE_TYPE=time`)              | `02:00`                          |

> **Nota**:
> - Todas as variáveis devem ser definidas e não vazias.
> - `SCHEDULE_TYPE` deve ser `minutes` ou `time`.
> - Se `SCHEDULE_TYPE=minutes`, `SCHEDULE_INTERVAL_MINUTES` deve ser um número inteiro positivo (ex.: `2`, `15`, `30`).
> - Se `SCHEDULE_TYPE=time`, `SCHEDULE_TIME` deve estar no formato `HH:MM` (ex.: `02:00`).
> - `DECODE_SUBJECT=yes` é necessário para que a imagem `aprendendolinux/exim-relay:latest` gere um `mail.log` com assuntos decodificados, compatível com o processamento da aplicação.
> - Variáveis ausentes ou inválidas causam falha na inicialização com erro registrado no log do contêiner.

### 3. Configurar Diretórios de Volume
- Crie os diretórios para os volumes do MySQL e logs:
  ```bash
  mkdir -p /srv/smtp-relay/db /srv/smtp-relay/logs
  chmod -R 777 /srv/smtp-relay  # Ajuste permissões conforme necessário
  ```
- O arquivo `mail.log` gerado pelo serviço `smtp-relay` será automaticamente criado em `/srv/smtp-relay/logs` e montado no serviço `smtp-relay-frontend` para leitura.

### 4. Construir e Executar
```bash
docker compose up -d
```

- Acesse os logs para verificar a inicialização:
  ```bash
  docker logs smtp-relay-frontend
  ```

### 5. Acessar a Aplicação
- Abra o navegador em `http://localhost:5000`.
- Para `AUTH_MODE=DB`, use as credenciais padrão: usuário `admin`, senha `admin`.
- Para `AUTH_MODE=AD`, use credenciais válidas do Active Directory (sem o domínio, ex.: `usuario` ao invés de `usuario@dominio.com`).

## Uso
1. **Tela de Login**:
   - Insira o nome de usuário e a senha (DB ou AD, conforme configurado).
   - Para AD, apenas usuários do grupo especificado em `LDAP_GROUP_DN` terão acesso.

2. **Tela de Relatórios**:
   - **Filtros**:
     - **Data Inicial/Final**: Filtre logs por intervalo de datas.
     - **E-mail Destinatário**: Busque por parte do endereço de e-mail (ex.: `example.com`).
     - **Assunto**: Busque por parte do assunto do e-mail (ex.: `Reunião`).
     - **Apenas Falhados**: Exiba apenas logs com status diferente de `sent`.
     - **Limpar Busca**: Restaura a exibição padrão (logs do dia atual).
   - **Ordenação**: Clique nos botões `↑↓` nas colunas "Data" ou "Hora" para ordenar (padrão: data descendente, ou seja, mais recentes primeiro).
   - **Paginação**: Navegue por páginas de resultados (50 logs por página).
   - **Informações de Origem**: Clique em uma célula de "De", "Para" ou "Assunto" para ver detalhes em um modal (ex.: IP e host de origem para "De").

3. **Alterar Senha** (somente para `AUTH_MODE=DB`):
   - Acesse `/change-password` para alterar a senha do usuário logado.
   - Requer senha atual, nova senha e confirmação (mínimo 4 caracteres).

4. **Logout**:
   - Clique em "Logout" para encerrar a sessão. As mensagens de flash são limpas, e o cache do navegador é evitado para proteger dados sensíveis.

## Processamento de Logs
- A aplicação processa **apenas o arquivo `mail.log`** no diretório configurado (`LOG_DIR`) conforme o tipo de agendamento:
  - **Por Intervalo (`SCHEDULE_TYPE=minutes`)**: Executa a cada `SCHEDULE_INTERVAL_MINUTES` minutos (ex.: a cada 2 minutos).
  - **Por Horário (`SCHEDULE_TYPE=time`)**: Executa diariamente no horário especificado em `SCHEDULE_TIME` (ex.: `02:00`).
- Formato esperado do `mail.log` (gerado pela imagem `aprendendolinux/exim-relay:latest` com `DECODE_SUBJECT=yes`):
  ```
  2025-10-10 14:30:45 1v8dZA-00004I-4W <= sender@example.com H=host.example.com [192.168.1.1] T="Reunião Mensal"
  2025-10-10 14:30:46 1v8dZA-00004I-4W => recipient@example.com status=sent
  2025-10-10 14:30:47 1v8dZA-00004I-4W Completed
  ```
- **Critérios para importação**:
  - O `message_id` (ex.: `1v8dZA-00004I-4W`) não pode existir no banco de dados.
  - A mensagem deve ter uma linha de origem (`<=`) com remetente, host e IP.
  - Deve ter pelo menos uma linha de entrega (`=>` ou `->`) ou rejeição (`**`) com destinatário.
  - Deve ter uma linha `Completed` para o mesmo `message_id`.
- **Comportamento**:
  - Mensagens completas são importadas para o banco MySQL.
  - Mensagens pendentes (sem `Completed` ou com origem/destino incompleto) são registradas nos logs do contêiner e permanecem no `mail.log` para reavaliação futura.
  - O arquivo `mail.log` **não é modificado, truncado ou reescrito** pela aplicação. O gerenciamento do tamanho do arquivo deve ser feito via `logrotate`.

## Configuração do Logrotate
Para gerenciar o tamanho do arquivo `mail.log`, configure o `logrotate` no host. Exemplo de configuração em `/etc/logrotate.d/exim`:
```plaintext
/srv/smtp-relay/logs/mail.log {
    daily
    size 10M
    rotate 7
    missingok
    compress
    delaycompress
    notifempty
    create 0640 root root
    postrotate
        /usr/bin/killall -USR1 exim
    endscript
}
```
- **Teste**: `logrotate -f /etc/logrotate.d/exim`
- **Verificação**: Confirme que o Exim continua gravando com `tail -f /srv/smtp-relay/logs/mail.log`.

## Solução de Problemas
- **Erro de Variáveis de Ambiente**:
  - Verifique os logs com `docker logs smtp-relay-frontend`. Mensagens como `Host do banco de dados (DB_HOST) não definida ou vazia`, `Tipo de agendamento inválido`, ou `Horário específico inválido: <valor> (deve ser no formato HH:MM)` indicam variáveis ausentes ou inválidas no `docker-compose.yml`.
- **Erro de Conexão LDAP** (se `AUTH_MODE=AD`):
  - Confirme que o `LDAP_HOST` está acessível:
    ```bash
    docker exec -it smtp-relay-frontend ping <SEU_IP_OU_HOST_LDAP>
    ```
  - Verifique as configurações de `LDAP_DOMAIN`, `LDAP_BASE_DN` e `LDAP_GROUP_DN`.
- **Erro de Conexão com MySQL**:
  - Certifique-se de que o serviço `smtp-relay-db` está saudável:
    ```bash
    docker ps
    ```
  - Verifique as credenciais no `docker-compose.yml` (`DB_USER`, `DB_PASSWORD`, `DB_NAME`).
- **Logs Não Processados**:
  - Confirme que o arquivo `mail.log` existe em `/srv/smtp-relay/logs` e tem permissões de leitura:
    ```bash
    ls -l /srv/smtp-relay/logs/mail.log
    ```
  - Verifique se `DECODE_SUBJECT=yes` está configurado no serviço `smtp-relay` para gerar assuntos legíveis.
  - Veja os logs do contêiner para erros de parsing:
    ```bash
    docker logs smtp-relay-frontend
    ```
- **Exim Não Grava no `mail.log`**:
  - Verifique permissões do arquivo:
    ```bash
    chmod 640 /srv/smtp-relay/logs/mail.log
    chown exim:root /srv/smtp-relay/logs/mail.log
    ```
  - Reinicie o Exim, se necessário:
    ```bash
    docker exec smtp-relay systemctl restart exim
    ```
  - Teste o relay:
    ```bash
    swaks --to test@example.com --from user@example.com --server localhost:25
    ```
- **Intervalo ou Horário de Importação**:
  - Confirme que `SCHEDULE_TYPE` é `minutes` ou `time`.
  - Se `SCHEDULE_TYPE=minutes`, verifique se `SCHEDULE_INTERVAL_MINUTES` é um número inteiro positivo (ex.: `2`).
  - Se `SCHEDULE_TYPE=time`, verifique se `SCHEDULE_TIME` está no formato `HH:MM` (ex.: `02:00`).
  - Nos logs, confira a mensagem de inicialização do scheduler (ex.: "Scheduler: a cada 2 min." ou "Scheduler: diariamente às 02:00.").

## Segurança
- **Autenticação**: Para `AUTH_MODE=DB`, use senhas fortes e altere a senha padrão `admin` via `/change-password`. Para `AUTH_MODE=AD`, apenas usuários do grupo especificado em `LDAP_GROUP_DN` têm acesso.
- **Cache**: Páginas sensíveis (relatórios) têm cabeçalhos anti-cache para evitar acesso a dados após logout.
- **Variáveis de Ambiente**: Todas as variáveis são validadas na inicialização, incluindo `SCHEDULE_TYPE`, `SCHEDULE_INTERVAL_MINUTES` e `SCHEDULE_TIME`.
- **Senhas**: Use um arquivo `.env` para armazenar dados sensíveis (ex.: `SMTP_PASSWORD`, `DB_PASSWORD`). Exemplo:
  ```plaintext
  SMTP_PASSWORD=xxxxxxxxxxxxxxxx
  DB_PASSWORD=senha_forte_123
  ```
- **Portas**: Restrinja a porta 25 do `smtp-relay` a IPs confiáveis via firewall.

## Desenvolvimento
Para modificar a aplicação:
1. Edite o `app.py`, os templates em `templates/` ou o `docker-compose.yml`.
2. Reconstrua a imagem:
   ```bash
   docker compose build
   ```
3. Teste localmente antes de enviar ao repositório.

## Publicação no DockerHub
A imagem está disponível como `clubenaval/relatorios-smtp:latest`. Para atualizar:
```bash
docker build -t clubenaval/relatorios-smtp:latest .
docker push clubenaval/relatorios-smtp:latest
```

## Dependência com Exim
Esta solução foi projetada para funcionar com a imagem `aprendendolinux/exim-relay:latest`, que inclui customizações críticas:
- Gera o arquivo `mail.log` com assuntos decodificados (via `DECODE_SUBJECT=yes`), essencial para o parsing correto pela aplicação.
- Produz logs no formato esperado, com `message_id`, `from`, `to`, `status`, e `Completed`.
- Suporta autenticação SMTP e relay para provedores externos como Gmail.
Consulte o repositório [https://github.com/AprendendoLinux/exim-relay](https://github.com/AprendendoLinux/exim-relay) para detalhes adicionais sobre configuração e troubleshooting.

## Contribuição
1. Faça um fork do repositório.
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`).
3. Commit suas alterações (`git commit -m 'Adiciona nova funcionalidade'`).
4. Envie para o repositório remoto (`git push origin feature/nova-funcionalidade`).
5. Abra um Pull Request.

## Licença
Desenvolvido por Henrique Fagundes. Todos os direitos reservados.

## Contato
Para suporte, entre em contato via [henrique.tec.br](https://www.henrique.tec.br).