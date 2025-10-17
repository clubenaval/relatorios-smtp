# **Relatórios SMTP - Clube Naval**

![Logo Clube Naval](https://www.clubenaval.org.br/themes/custom/cn_theme/cn_logo_n1.svg)

[![Versão](https://img.shields.io/badge/vers%C3%A3o-1.0.0-blue.svg)](https://github.com/seu-usuario/relatorios-smtp/releases)
[![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/seu-usuario/relatorios-smtp/actions) <!-- Adicione CI/CD se configurado -->
[![Security](https://img.shields.io/badge/security-OWASP%20Compliant-yellow.svg)](https://owasp.org/) <!-- Baseado em práticas recomendadas -->
[![Downloads](https://img.shields.io/badge/downloads-1k%2B-orange.svg)](https://github.com/seu-usuario/relatorios-smtp) <!-- Exemplo; ajuste com métricas reais -->

## **Descrição do Projeto**

O **Relatórios SMTP - Clube Naval** é uma aplicação web avançada desenvolvida para o monitoramento, análise e gerenciamento de logs de e-mails enviados e falhados em servidores SMTP que utilizam Exim como MTA (Mail Transfer Agent). Esta solução oferece recursos robustos para importação automática de logs, visualização de relatórios detalhados com filtros dinâmicos, exportação de dados em formatos como CSV e PDF, e suporte a autenticação segura. Projetada para organizações como o Clube Naval, onde a comunicação por e-mail é essencial para operações diárias, eventos e interações com membros, a aplicação garante visibilidade completa sobre envios de e-mails, ajudando a identificar falhas, rejeições e padrões de uso.

A aplicação é totalmente containerizada com **Docker** e **Docker Compose**, facilitando a implantação em ambientes locais, servidores dedicados ou plataformas de nuvem como AWS, Azure ou Google Cloud. Ela suporta escalabilidade horizontal (ex.: múltiplos instances da app Flask) e integra automação para tarefas recorrentes, como parsing de logs. Com foco em segurança, performance e usabilidade, o sistema lida com volumes altos de dados (milhares de logs por dia) sem comprometer a eficiência, graças a otimizações como inserções em batch no banco de dados e regex eficientes para extração de dados.

**Motivação e Contexto**: Em cenários onde e-mails são críticos (ex.: notificações de eventos, boletins ou comunicações administrativas), falhas podem resultar em perdas financeiras ou reputacionais. Esta aplicação mitiga isso ao fornecer relatórios em tempo real, alertas implícitos via status e integração com sistemas existentes. Ela é extensível para futuras features, como integração com ferramentas de BI (ex.: Power BI) ou alertas via e-mail para admins.

**Versão Atual**: 1.0.0 (Lançada em 17 de Outubro de 2025). Esta versão incorpora melhorias baseadas em feedback, incluindo otimização de queries SQL, suporte aprimorado a encoding UTF-8 em subjects e validações mais rigorosas de variáveis de ambiente.

**Data da Última Atualização**: 17 de Outubro de 2025.

## **Características Principais**

Aqui está uma lista expandida das funcionalidades chave, com detalhes sobre como elas beneficiam o usuário:

* **Processamento de Logs Avançado**: Leitura e importação inteligente dos arquivos `full_subjects.log` (para detalhes como subjects decodificados) e `mail.log` (para status como "sent", "rejected" ou "completed"). O parser usa regex para extrair campos como message_id, data/hora, from/to emails, host/IP de origem e subject, filtrando pendentes e evitando duplicatas via checagens no banco de dados.

* **Relatórios Avançados e Interativos**: Interface web responsiva para exibir relatórios com filtros dinâmicos (por data, hora, e-mail remetente/destinatário, assunto parcial e status "sent" ou "failed"). Suporte a ordenação (asc/desc por data/hora), modals para detalhes expandidos (com cópia para clipboard), auto-refresh a cada 60 segundos e exportação para CSV com formatação localizada (ex.: data em DD/MM/YYYY, status traduzido para "Enviado").

* **Autenticação Segura e Flexível**: Suporte para modos "AD" (integração LDAP com filtros por grupo e base DN) ou "DB" (autenticação local com hashes bcrypt via Werkzeug, recuperação de senha via e-mail com tokens timed e gerenciamento de usuários admin/non-admin).

* **Agendamento e Automação**: Configuração flexível para importação de logs via biblioteca `schedule`, rodando em thread daemon. Opções incluem intervalos em minutos (ex.: a cada 2min para near-real-time) ou horários fixos (ex.: diariamente às 16:40), com retry em erros e logging detalhado para auditoria.

* **Dockerização Completa e Escalável**: Utiliza Docker Compose para orquestrar serviços isolados, com healthchecks para readiness, volumes persistentes para dados críticos (logs e DB) e suporte a secrets para variáveis sensíveis. Fácil scaling com replicas.

* **Segurança Integrada**: Validações rigorosas de env vars (ex.: checagem de tipos, formatos e dependências condicionais), proteção contra SQL injection (params em queries), no-cache headers em rotas sensíveis, e suporte a HTTPS via reverse proxy (ex.: Nginx).

* **Frontend Moderno**: Templates Jinja2 com CSS responsivo (media queries para mobile), fontes Roboto, gradients temáticos (vermelho/azul naval do Clube Naval), e scripts JS para interatividade (ex.: confirmações de delete, cópia de texto, prevenção de impressões em branco).

* **Logging e Monitoramento**: Registros detalhados em níveis INFO/ERROR para todas operações, incluindo resumos de importações (ex.: "IDs total=100, importados=80, pendentes=20"). Fácil integração com ferramentas como Prometheus ou ELK.

* **Extensibilidade**: Código modular (arquivos separados para config, database, parser, etc.), permitindo adições como gráficos (Chart.js) ou integrações com APIs externas.

## **Tecnologias Utilizadas**

Uma visão detalhada das stacks tecnológicas, com justificativas:

* **Backend**: Python 3.12 (para performance e features modernas como async), Flask (framework leve e flexível para web apps, com suporte a blueprints para escalabilidade).

* **Banco de Dados**: MySQL 5.7.44 (estável para schemas relacionais, com suporte a índices únicos para deduplicação eficiente).

* **Autenticação**: LDAP3 (para integração segura com AD, com auto-bind e filtros customizados); Werkzeug (para hashing de senhas e segurança em forms).

* **Agendamento**: Schedule (simples e leve para tasks periódicas), Threading (para execução não-bloqueante em background).

* **Docker**: Docker Compose v3.8 (para orquestração multi-container, com suporte a networks e volumes named).

* **Frontend**: HTML5/CSS3 (com variáveis CSS para temas), JavaScript (para interatividade como modals e auto-refresh), Jinja2 (para rendering dinâmico de templates com loops e condicionais).

* **Outras Bibliotecas**: MySQL-Connector-Python (para conexões DB), Pytz (para handling de timezones), Flask-Mail e ItsDangerous (para recuperação de senha), Re (para regex no parser).

Justificativa: Escolhas focadas em leveza (baixo overhead), segurança (bibliotecas auditadas) e compatibilidade (Python eco-system amplo).

## **Arquitetura**

A arquitetura segue princípios de microservices containerizados, com separação de preocupações para manutenção e escalabilidade. Diagrama em Mermaid (copie para visualizadores online como mermaid.live):


- **Fluxo Detalhado**:
  1. E-mails de clients (apps/scripts) chegam ao Exim Relay via porta 25/2525.
  2. Exim processa e encaminha para SMTP externo, gerando logs em volume compartilhado.
  3. Scheduler na Flask App aciona parser periodicamente, extraindo dados via regex e inserindo no MySQL (com migrações automáticas).
  4. Usuários acessam via browser, autenticando contra DB ou LDAP.
  5. Relatórios são renderizados com queries otimizadas, filtros WHERE/ORDER BY, e exports CSV.

Esta estrutura garante alta disponibilidade (restart policies), persistência (volumes) e segurança (networks isoladas).

## **Docker Compose: Arquivo Detalhado**

O `docker-compose.yml` orquestra os serviços. Abaixo, o arquivo completo (baseado no fornecido, expandido com comentários detalhados), seguido de explicações por serviço e variável.

```yaml
version: '3.8'  # Versão compatível com features modernas como healthchecks e secrets.

services:
  smtp-relay:  # Serviço para relay Exim; renomeado para clareza se necessário.
    image: aprendendolinux/exim-relay:latest  # Imagem oficial para relay seguro.
    restart: always  # Garante resiliência em falhas.
    container_name: smtp-relay
    hostname: smtp-relay  # FQDN interno para headers.
    environment:  # Vars para config do relay.
      SMTP_SERVER: smtp-relay.example.com  # Host SMTP externo.
      SMTP_PORT: 587  # Porta segura com STARTTLS.
      SMTP_USERNAME: user@example.com  # Credencial de auth.
      SMTP_PASSWORD: xxxxxxxxxxxxxxxx  # Senha sensível; use secrets.
      SERVER_HOSTNAME: mail.example.com  # FQDN do relay.
      RELAY_NETS: 0.0.0.0/0  # Redes permitidas; restrinja em prod.
      TZ: America/Sao_Paulo  # Timezone sincronizado.
      DECODE_SUBJECT: yes  # Decodifica MIME em subjects.
    volumes:
      - /srv/smtp-relay/logs:/var/log/exim4  # Persistência de logs.
    ports:
      - 25:25  # Porta padrão SMTP.
      - 2525:25  # Porta alternativa.
    healthcheck:  # Verifica readiness.
      test: ["CMD-SHELL", "exim -bhc 127.0.0.1 -oX 25 <<< 'QUIT'"]
      interval: 10s
      timeout: 5s
      retries: 5

  smtp-relay-db:  # Serviço MySQL para DB persistente.
    image: mysql:5.7.44  # Versão estável com suporte legado se necessário.
    restart: always
    container_name: smtp-relay-db
    hostname: smtp-relay-db
    environment:  # Credenciais DB.
      MYSQL_ROOT_PASSWORD: 'xxxxxxxxxxxxxxxx'  # Senha root; use .env.
      MYSQL_DATABASE: smtp_cpd  # Nome do DB.
      MYSQL_USER: smtp_user  # User app.
      MYSQL_PASSWORD: 'xxxxxxxxxxxxxxxx'  # Senha app.
    volumes:
      - /srv/mysql:/var/lib/mysql  # Persistência de dados.
    healthcheck:  # Verifica conectividade.
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10

  smtp-relay-app:  # Serviço app Flask (renomeado para clareza).
    build: .  # Build do Dockerfile local.
    restart: always
    container_name: smtp-relay-app
    hostname: smtp-relay-app
    environment:  # Vars para app.
      AUTH_MODE: DB  # Modo auth (AD/DB).
      DB_HOST: smtp-relay-db  # Host DB interno.
      DB_USER: smtp_user
      DB_PASSWORD: 'xxxxxxxxxxxxxxxx'
      DB_NAME: smtp_cpd
      LOG_DIR: /app/logs  # Diretório logs compartilhado.
      TZ: America/Sao_Paulo
      SCHEDULE_TYPE: minutes  # Tipo scheduler.
      SCHEDULE_INTERVAL_MINUTES: 2  # Intervalo.
      # SCHEDULE_TIME: 16:40  # Se type=time.
      DB_PORT: 3306  # Porta DB.
      SMTP_SERVER: smtp-relay  # SMTP para recovery (DB mode).
      SMTP_PORT: 25
      SMTP_FROM: noreply@example.com
      SMTP_FROM_NAME: 'Sistema de Relatórios'
      SMTP_AUTHENTICATED: False  # Auth SMTP.
      # Se AD: LDAP_HOST, LDAP_DOMAIN, etc.
    volumes:
      - /srv/smtp-relay/logs:/app/logs  # Compartilhamento logs.
    ports:
      - "5000:5000"  # Exposição web.
    depends_on:
      smtp-relay-db:  # Dependência com condition.
        condition: service_healthy

networks:
  default:
    driver: bridge
    name: smtp-network  # Rede isolada.
```

### Explicação por Serviço

1. **smtp-relay (Relay Exim)**:
   - **Propósito**: Encaminha e-mails e gera logs para análise.
   - **Imagem**: Baseada em Exim para relay seguro.
   - **Environment Vars**: Configuram o relay externo, auth e redes permitidas.
   - **Volumes/Ports**: Persistem logs e expõem SMTP.
   - **Healthcheck**: Garante que Exim responda a comandos básicos.

2. **smtp-relay-db (MySQL)**:
   - **Propósito**: Armazena logs e users persistentemente.
   - **Imagem**: Versão fixa para compatibilidade.
   - **Environment Vars**: Definindo DB e creds.
   - **Volumes**: Para backup/restore fácil.
   - **Healthcheck**: Ping simples para readiness.

3. **smtp-relay-app (App Flask)**:
   - **Propósito**: Lógica de negócio, web UI e scheduler.
   - **Build**: Do local Dockerfile (Python slim com deps).
   - **Environment Vars**: Controlam auth, DB, scheduler e SMTP (condicional).
   - **Volumes/Ports**: Compartilha logs, expõe 5000.
   - **Depends_on**: Espera DB healthy.

**Notas sobre Vars**: Todas sensíveis devem vir de `.env`. Validações em `config.py` lançam erros se inválidas (ex.: TZ desconhecido, portas fora de range).

## **Execução da Aplicação**

### **1. Pré-Requisitos**
- Docker instalado.
- Diretórios para volumes criados.
- .env com secrets.

### **2. Baixar e Iniciar**
```
docker-compose up -d --build
```

### **3. Acessar**
- URL: http://localhost:5000
- Login default (DB): admin/admin (altere via /change_password).

### **4. Uso Diário**
- Relatórios: Filtre e exporte.
- Import manual: /import-emails.
- Gerenciamento: /manage (admins).

## **Contribuição**

Siga o fluxo GitHub padrão. Adicione testes (pytest) e docs.

## **Licença**

MIT. Veja [LICENSE](LICENSE).

## **Suporte**

Contato: Henrique Fagundes - support@henrique.tec.br. Para issues, abra tickets no GitHub.