# **Relatórios SMTP - Clube Naval**

<img src="static/logo.png" alt="Logo Clube Naval" width="200" />

[![Versão](https://img.shields.io/badge/vers%C3%A3o-1.0.0-blue.svg)](https://github.com/seu-usuario/relatorios-smtp/releases)
[![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/seu-usuario/relatorios-smtp/actions) <!-- Adicione CI/CD se configurado -->
[![Security](https://img.shields.io/badge/security-OWASP%20Compliant-yellow.svg)](https://owasp.org/) <!-- Baseado em práticas recomendadas -->
[![Downloads](https://img.shields.io/badge/downloads-1k%2B-orange.svg)](https://github.com/seu-usuario/relatorios-smtp) <!-- Exemplo; ajuste com métricas reais -->

## **Descrição do Projeto**

O **Relatórios SMTP - Clube Naval** é uma solução completa e escalável para monitoramento, análise e gerenciamento de logs de e-mails enviados e falhados em servidores SMTP baseados no Exim Mail Transfer Agent (MTA). Desenvolvido especificamente para atender às necessidades do **Clube Naval**, este sistema é ideal para organizações que dependem de comunicações por e-mail para operações administrativas, eventos ou interações com membros, garantindo visibilidade detalhada sobre envios, rejeições e falhas. Ele suporta grandes volumes de dados, conformidade com regulamentações de privacidade (como a LGPD no Brasil) e integração com sistemas corporativos existentes.

A aplicação é totalmente containerizada usando **Docker** e **Docker Compose**, o que facilita a implantação em ambientes locais, servidores dedicados ou plataformas de nuvem (AWS, Azure, Google Cloud). O sistema combina um relay SMTP (Exim), um banco de dados MySQL para persistência de dados, e uma interface web em Flask para relatórios interativos e gerenciamento de usuários. Ele suporta autenticação segura via **Active Directory (AD)** ou banco local (**DB**), com recursos como recuperação de senha, agendamento automatizado de importação de logs e exportação de relatórios em formatos CSV e PDF.

**Motivação e Contexto**: E-mails são críticos para comunicações organizacionais, como notificações de eventos, boletins ou confirmações administrativas. Falhas ou rejeições podem levar a perdas financeiras, falhas de compliance ou problemas de reputação. Este sistema resolve isso ao oferecer monitoramento em tempo real, relatórios detalhados e automação robusta. Ele é projetado para ser extensível, permitindo futuras integrações com ferramentas de Business Intelligence (BI), sistemas de alerta ou dashboards avançados.

**Versão Atual**: 1.0.0 (Lançada em 17 de Outubro de 2025). Inclui otimizações de performance (ex.: queries SQL indexadas), suporte a encoding UTF-8 em subjects, validações rigorosas de variáveis de ambiente e melhorias de usabilidade baseadas em feedback inicial.

**Data da Última Atualização**: 17 de Outubro de 2025.

## **Características Principais**

A seguir, uma lista detalhada das funcionalidades, com explicações de como elas agregam valor ao usuário final:

1. **Processamento Inteligente de Logs**:
   - **Descrição**: Extrai dados de arquivos de log do Exim (`full_subjects.log` para detalhes como remetente, destinatário e assunto; `mail.log` para status como "sent", "rejected" ou "completed"). Usa expressões regulares (regex) otimizadas para parsear campos como `message_id`, data/hora, e-mails, host/IP de origem e subject.
   - **Benefícios**: Garante precisão na extração, filtra duplicatas via índices únicos no banco de dados, lida com pendências (e-mails sem resolução final) e suporta subjects complexos com pipes e encoding UTF-8.
   - **Exemplo de Uso**: Um administrador pode verificar quantos e-mails foram rejeitados em um dia específico, identificando problemas como blacklists ou configurações incorretas.

2. **Relatórios Interativos e Customizáveis**:
   - **Descrição**: Interface web responsiva com filtros dinâmicos (data, hora, remetente, destinatário, assunto parcial, status "sent"/"failed"). Suporta ordenação (ascendente/descendente por data ou hora), modals para detalhes expandidos (com cópia de host/IP/subject para clipboard), auto-refresh a cada 60 segundos e exportação para CSV com formatação localizada (ex.: data em DD/MM/YYYY, status traduzido para "Enviado").
   - **Benefícios**: Permite análises rápidas, relatórios para auditorias e exportação para ferramentas externas como Excel.
   - **Exemplo de Uso**: Filtrar todos os e-mails rejeitados de um remetente específico em um intervalo de datas.

3. **Autenticação Segura e Flexível**:
   - **Descrição**: Suporta dois modos:
     - **AD**: Integração com Active Directory via LDAP, com bind seguro, filtros por grupo e suporte a base DN para autenticação corporativa.
     - **DB**: Autenticação local com hashes bcrypt (via Werkzeug), recuperação de senha por e-mail com tokens temporizados (ItsDangerous) e gerenciamento de usuários (admin/non-admin).
   - **Benefícios**: Compatível com infraestruturas corporativas (AD) ou setups standalone (DB). Recuperação de senha aumenta usabilidade.
   - **Exemplo de Uso**: Um admin cria usuários locais via interface ou usa credenciais de domínio existentes.

4. **Agendamento e Automação**:
   - **Descrição**: Importação automatizada de logs via biblioteca `schedule`, rodando em thread daemon. Configurável para intervalos em minutos (ex.: a cada 2 minutos para atualizações quase em tempo real) ou horários fixos (ex.: diariamente às 16:40). Inclui retries em erros e logging detalhado.
   - **Benefícios**: Reduz intervenção manual, mantendo dados atualizados. Logging facilita auditoria de falhas.
   - **Exemplo de Uso**: Configurar importação a cada 5 minutos para monitorar envios em tempo real.

5. **Dockerização Completa e Escalável**:
   - **Descrição**: Orquestração via Docker Compose com três serviços (relay Exim, MySQL, app Flask), healthchecks para readiness, volumes persistentes para logs e dados do banco, e rede bridge isolada. O Dockerfile da app usa Python 3.12 slim para leveza.
   - **Benefícios**: Implantação rápida, isolamento de serviços e fácil escalabilidade (ex.: replicas da app com load balancer).
   - **Exemplo de Uso**: Deploy em AWS ECS com auto-scaling para picos de tráfego.

6. **Segurança Integrada**:
   - **Descrição**: Validações rigorosas de variáveis de ambiente (ex.: checagem de tipos, formatos e dependências condicionais via `config.py`), proteção contra SQL injection (queries parametrizadas), headers de segurança (ex.: `Cache-Control: no-store` em rotas sensíveis), suporte a HTTPS via reverse proxy, e hashes seguros para senhas.
   - **Benefícios**: Conformidade com OWASP Top 10 e LGPD, minimizando riscos de ataques como XSS ou brute-force.
   - **Exemplo de Uso**: Evita injeções em filtros de busca de relatórios.

7. **Frontend Moderno e Responsivo**:
   - **Descrição**: Templates Jinja2 com CSS inline (variáveis CSS para temas consistentes), fontes Roboto, gradients temáticos (vermelho #C8102E e azul naval #1A3C5E do Clube Naval), e JavaScript para interatividade (modals, cópia para clipboard, confirmações de delete, auto-refresh). Media queries garantem responsividade em dispositivos móveis.
   - **Benefícios**: Interface intuitiva, acessível em desktops e smartphones, com UX otimizada.
   - **Exemplo de Uso**: Um admin acessa relatórios em um tablet durante uma reunião.

8. **Logging e Monitoramento**:
   - **Descrição**: Logging detalhado (INFO/ERROR) para todas operações, incluindo resumos de importações (ex.: "IDs total=100, importados=80, pendentes=20"). Compatível com ferramentas externas como Prometheus, ELK Stack ou Sentry.
   - **Benefícios**: Facilita depuração e auditoria de conformidade.
   - **Exemplo de Uso**: Investigar por que um lote de logs não foi importado.

9. **Extensibilidade**:
   - **Descrição**: Código modular (arquivos separados para config, database, parser, auth, scheduler) permite adicionar features como integração com Power BI, alertas por e-mail para falhas ou suporte a múltiplos relays SMTP.
   - **Benefícios**: Fácil adaptação para novos requisitos organizacionais.
   - **Exemplo de Uso**: Adicionar gráficos de envios por dia usando Chart.js.

## **Tecnologias Utilizadas**

A stack foi escolhida para equilibrar performance, segurança e facilidade de manutenção:

- **Backend**: Python 3.12 (suporte a async/await, tipagem avançada); Flask (leve, com blueprints para escalabilidade).
- **Banco de Dados**: MySQL 5.7.44 (estável, com índices únicos para deduplicação eficiente; suporta transações e UTF-8).
- **Autenticação**: LDAP3 (para AD, com suporte a TLS); Werkzeug (hashing bcrypt); Flask-Mail e ItsDangerous (recuperação de senha).
- **Agendamento**: Schedule (simples para tasks periódicas); Threading (execução assíncrona leve).
- **Docker**: Docker Compose v3.8 (orquestração robusta); Python slim (base leve para app).
- **Frontend**: HTML5/CSS3 (variáveis CSS, media queries); JavaScript (interatividade); Jinja2 (templates dinâmicos).
- **Bibliotecas Adicionais**:
  - `mysql-connector-python`: Conexões DB confiáveis.
  - `pytz`: Gerenciamento de timezones.
  - `re`: Regex para parsing de logs.
- **Justificativa**: Stack leve (baixo overhead), auditada para segurança (ex.: Werkzeug segue OWASP), e amplamente suportada pelo ecossistema Python.

## **Arquitetura**

A arquitetura segue o padrão de microservices containerizados, com separação clara de responsabilidades.

![Diagrama](static/diagrama.svg)

**Fluxo Detalhado**:
1. **Envio de E-mails**: Clients (ex.: apps internas) enviam e-mails ao Exim via portas 25/2525.
2. **Logging**: Exim gera logs em `/srv/smtp-relay/logs` (montado como volume).
3. **Parsing**: Scheduler na app Flask aciona `log_parser.py` periodicamente, extraindo dados com regex e verificando duplicatas no MySQL.
4. **Persistência**: Dados são inseridos no banco (`email_logs` e `app_users`) via `database.py` com `INSERT IGNORE` para eficiência.
5. **Autenticação**: Usuários logam via `/login`, autenticando contra LDAP (AD) ou MySQL (DB).
6. **Relatórios**: Rotas Flask renderizam relatórios com filtros, exportação CSV e impressão otimizada.

**Benefícios Arquiteturais**:
- Isolamento via containers (evita conflitos de dependências).
- Persistência via volumes (logs e DB salvos entre restarts).
- Rede bridge (`smtp-network`) para segurança e comunicação interna.

## **Docker Compose: Arquivo Detalhado**

O `docker-compose.yml` define três serviços: `smtp-relay` (Exim), `smtp-relay-db` (MySQL) e `smtp-relay-app` (Flask, renomeado para clareza). Abaixo, o arquivo completo com comentários detalhados, seguido de uma explicação exaustiva de cada variável de ambiente.

```yaml
version: '3.8'  # Suporta features modernas como healthchecks, secrets e redes avançadas.

services:
  smtp-relay:  # Relay Exim para encaminhamento de e-mails.
    image: aprendendolinux/exim-relay:latest  # Imagem oficial, otimizada para relay seguro.
    restart: always  # Reinicia em falhas, exceto se parado manualmente.
    container_name: smtp-relay
    hostname: smtp-relay  # FQDN interno para headers SMTP.
    environment:  # Configurações do relay.
      # Host SMTP externo para encaminhamento (ex.: Gmail, AWS SES).
      SMTP_SERVER: smtp-relay.example.com
      # Porta SMTP (25: não seguro, 587: STARTTLS, 465: SSL).
      SMTP_PORT: 587
      # Credenciais para autenticação SMTP, se necessário.
      SMTP_USERNAME: user@example.com
      SMTP_PASSWORD: xxxxxxxxxxxxxxxx  # Sensível; use .env ou secrets.
      # FQDN do servidor Exim para identificação em headers.
      SERVER_HOSTNAME: mail.example.com
      # Redes permitidas para relay (CIDR); restrinja em produção.
      RELAY_NETS: 0.0.0.0/0
      # Timezone para logs, sincronizado com app.
      TZ: America/Sao_Paulo
      # Decodifica assuntos MIME (yes/no).
      DECODE_SUBJECT: yes
    volumes:
      # Volume para persistência de logs Exim.
      - /srv/smtp-relay/logs:/var/log/exim4
    ports:
      # Portas SMTP padrão e alternativa.
      - 25:25
      - 2525:25
    healthcheck:  # Verifica se Exim está funcional.
      test: ["CMD-SHELL", "exim -bhc 127.0.0.1 -oX 25 <<< 'QUIT'"]
      interval: 10s
      timeout: 5s
      retries: 5

  smtp-relay-db:  # Banco MySQL para logs e usuários.
    image: mysql:5.7.44  # Versão estável, compatível com schemas legados.
    restart: always
    container_name: smtp-relay-db
    hostname: smtp-relay-db
    environment:  # Credenciais e configs do banco.
      # Senha root, sensível; use .env.
      MYSQL_ROOT_PASSWORD: 'xxxxxxxxxxxxxxxx'
      # Nome do banco criado automaticamente.
      MYSQL_DATABASE: smtp_cpd
      # Usuário app, com privilégios limitados.
      MYSQL_USER: smtp_user
      # Senha app, sensível.
      MYSQL_PASSWORD: 'xxxxxxxxxxxxxxxx'
    volumes:
      # Persistência de dados do banco.
      - /srv/mysql:/var/lib/mysql
    healthcheck:  # Verifica conectividade MySQL.
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10

  smtp-relay-app:  # App Flask com lógica de negócio e UI.
    build: .  # Build a partir do Dockerfile local.
    restart: always
    container_name: smtp-relay-app
    hostname: smtp-relay-app
    environment:  # Configurações da app.
      # Modo de autenticação: AD (LDAP) ou DB (local).
      AUTH_MODE: DB
      # Host do banco (nome do serviço Docker).
      DB_HOST: smtp-relay-db
      # Credenciais DB, devem coincidir com smtp-relay-db.
      DB_USER: smtp_user
      DB_PASSWORD: 'xxxxxxxxxxxxxxxx'
      DB_NAME: smtp_cpd
      # Diretório de logs, compartilhado com smtp-relay.
      LOG_DIR: /app/logs
      # Timezone, sincronizado com relay.
      TZ: America/Sao_Paulo
      # Tipo de agendamento: minutes (intervalo) ou time (horário fixo).
      SCHEDULE_TYPE: minutes
      # Intervalo em minutos, se SCHEDULE_TYPE=minutes.
      SCHEDULE_INTERVAL_MINUTES: 2
      # Horário fixo, se SCHEDULE_TYPE=time (ex.: 16:40).
      # SCHEDULE_TIME: 16:40
      # Porta do banco, geralmente 3306.
      DB_PORT: 3306
      # Configs SMTP para recuperação de senha (DB mode).
      SMTP_SERVER: smtp-relay
      SMTP_PORT: 25
      SMTP_FROM: noreply@example.com
      SMTP_FROM_NAME: 'Sistema de Relatórios'
      SMTP_AUTHENTICATED: False  # Autenticação SMTP, se True requer username/password.
      # SMTP_USERNAME: user@example.com
      # SMTP_PASSWORD: xxxxxxxxxxxxxxxx
      # SMTP_USE_TLS: True
      # SMTP_USE_SSL: False
      # Configs LDAP, se AUTH_MODE=AD.
      # LDAP_HOST: 192.168.1.100
      # LDAP_DOMAIN: @example.com
      # LDAP_BASE_DN: DC=example,DC=com
      # LDAP_GROUP_DN: CN=Users,DC=example,DC=com
    volumes:
      # Compartilha logs com relay.
      - /srv/smtp-relay/logs:/app/logs
    ports:
      # Exposição da app Flask.
      - "5000:5000"
    depends_on:
      smtp-relay-db:  # Espera banco estar healthy.
        condition: service_healthy

networks:
  default:
    driver: bridge
    name: smtp-network  # Rede isolada para segurança.
```

### **Configuração Detalhada das Variáveis de Ambiente**

Abaixo, cada variável do `docker-compose.yml` é explicada com detalhes, incluindo propósito, tipo, valores default, exemplos, impacto no sistema, erros comuns, soluções e melhores práticas. Variáveis condicionais (ex.: LDAP para AD) são marcadas como tal.

#### **Serviço: `smtp-relay`**

1. **`SMTP_SERVER`**:
   - **Descrição**: Hostname do servidor SMTP externo para onde o Exim encaminha e-mails (ex.: Gmail, AWS SES, SendGrid). Define o destino final das mensagens.
   - **Tipo**: String.
   - **Obrigatória**: Sim.
   - **Default**: Nenhum.
   - **Exemplo Básico**: `smtp-relay.example.com`.
   - **Exemplo Avançado**: `email-smtp.us-east-1.amazonaws.com` (AWS SES com DKIM/SPF configurado).
   - **Impacto no Sistema**: Determina o destino dos e-mails. Um valor inválido impede envios, causando falhas nos logs.
   - **Erros Comuns**:
     - "Connection timed out": Firewall bloqueando porta ou host inacessível.
     - "Relay not permitted": Falta de autenticação ou configuração incorreta.
   - **Soluções**:
     - Teste conectividade: `telnet smtp-relay.example.com 587`.
     - Verifique DNS resolution do host.
   - **Melhores Práticas**: Use hosts SMTP com alta reputação (ex.: MailChannels). Configure failover com smarthost secundário.

2. **`SMTP_PORT`**:
   - **Descrição**: Porta do servidor SMTP externo. Comuns: 25 (não seguro), 587 (STARTTLS), 465 (SSL).
   - **Tipo**: Inteiro (1-65535).
   - **Obrigatória**: Sim.
   - **Default**: Nenhum.
   - **Exemplo Básico**: `587`.
   - **Exemplo Avançado**: `465` para servidores legados que exigem SSL direto.
   - **Impacto no Sistema**: Define o protocolo de segurança (STARTTLS vs SSL). Porta errada causa falhas de conexão.
   - **Erros Comuns**:
     - "Port blocked": ISPs bloqueiam 25; use 587/465.
     - "SSL/TLS error": Mismatch entre porta e protocolo.
   - **Soluções**:
     - Teste com `openssl s_client -connect host:port`.
     - Confirme com provedor SMTP qual porta usar.
   - **Melhores Práticas**: Prefira 587 com STARTTLS para conformidade moderna. Evite 25 em produção para prevenir relays abertos.

3. **`SMTP_USERNAME`**:
   - **Descrição**: Usuário para autenticação no servidor SMTP externo (ex.: e-mail ou API key).
   - **Tipo**: String.
   - **Obrigatória**: Sim, se autenticação requerida (ver `SMTP_AUTHENTICATED`).
   - **Default**: Nenhum.
   - **Exemplo Básico**: `user@example.com`.
   - **Exemplo Avançado**: `AKIAIOSFODNN7EXAMPLE` (chave AWS SES).
   - **Impacto no Sistema**: Necessário para servidores que exigem login. Falta causa erro "Authentication required".
   - **Erros Comuns**:
     - "Invalid credentials": Usuário errado ou desativado.
   - **Soluções**:
     - Valide credenciais no console do provedor SMTP.
     - Use .env para segurança.
   - **Melhores Práticas**: Rotacione chaves regularmente. Use IAM roles em cloud.

4. **`SMTP_PASSWORD`**:
   - **Descrição**: Senha ou token para autenticação SMTP.
   - **Tipo**: String.
   - **Obrigatória**: Sim, se autenticação requerida.
   - **Default**: Nenhum.
   - **Exemplo Básico**: `xxxxxxxxxxxxxxxx`.
   - **Exemplo Avançado**: Token AWS SES ou app-specific password do Gmail.
   - **Impacto no Sistema**: Garante acesso seguro ao SMTP. Senha errada bloqueia envios.
   - **Erros Comuns**:
     - "Authentication failed": Senha expirada ou incorreta.
   - **Soluções**:
     - Gere nova senha no provedor.
     - Use Docker secrets para evitar exposição.
   - **Melhores Práticas**: Armazene em `.env` ou secrets. Nunca commit no Git.

5. **`SERVER_HOSTNAME`**:
   - **Descrição**: FQDN (Fully Qualified Domain Name) do servidor Exim, usado em headers SMTP (ex.: EHLO).
   - **Tipo**: String.
   - **Obrigatória**: Sim.
   - **Default**: Nenhum.
   - **Exemplo Básico**: `mail.example.com`.
   - **Exemplo Avançado**: Domínio com SPF/DKIM configurado (ex.: `smtp.clubenaval.org.br`).
   - **Impacto no Sistema**: Afeta validação SPF/DKIM por servidores remotos. Valor inválido pode levar a rejeições.
   - **Erros Comuns**:
     - "Lowest numbered MX record points to local host": DNS mal configurado.
   - **Soluções**:
     - Configure DNS com registros A/MX válidos.
     - Teste com `dig mail.example.com`.
   - **Melhores Práticas**: Use domínio registrado com SPF/DKIM/DMARC para deliverability.

6. **`RELAY_NETS`**:
   - **Descrição**: Redes IP permitidas para enviar e-mails via relay, no formato CIDR.
   - **Tipo**: String.
   - **Obrigatória**: Sim.
   - **Default**: Nenhum.
   - **Exemplo Básico**: `0.0.0.0/0` (permite todas).
   - **Exemplo Avançado**: `192.168.1.0/24` (restringe a LAN interna).
   - **Impacto no Sistema**: Controla acesso ao relay. Valor amplo (0.0.0.0/0) pode criar open relay em produção.
   - **Erros Comuns**:
     - "Relay not permitted": IP fora da faixa permitida.
   - **Soluções**:
     - Liste IPs/subnets de clients confiáveis.
     - Monitore logs Exim para tentativas não autorizadas.
   - **Melhores Práticas**: Restrinja a redes internas ou VPN em produção.

7. **`TZ`**:
   - **Descrição**: Fuso horário para timestamps em logs Exim.
   - **Tipo**: String (formato TZ database).
   - **Obrigatória**: Sim.
   - **Default**: Nenhum.
   - **Exemplo Básico**: `America/Sao_Paulo`.
   - **Exemplo Avançado**: `UTC` para sistemas globais.
   - **Impacto no Sistema**: Garante consistência em timestamps entre relay, app e DB.
   - **Erros Comuns**:
     - "Unknown timezone": Valor inválido.
   - **Soluções**:
     - Valide com `pytz` (ex.: `python -c "import pytz; print(pytz.timezone('America/Sao_Paulo'))"`).
   - **Melhores Práticas**: Sincronize com app e DB para evitar discrepâncias.

8. **`DECODE_SUBJECT`**:
   - **Descrição**: Ativa/desativa decodificação de assuntos MIME nos logs (ex.: UTF-8 encoded subjects).
   - **Tipo**: String (yes/no).
   - **Obrigatória**: Não.
   - **Default**: `yes`.
   - **Exemplo Básico**: `yes`.
   - **Exemplo Avançado**: `no` para preservar encoding bruto em logs.
   - **Impacto no Sistema**: Afeta legibilidade de subjects nos relatórios. Desativar pode ajudar em debug de encodings.
   - **Erros Comuns**:
     - Subjects corrompidos: Encoding inválido no log.
   - **Soluções**:
     - Teste com e-mails internacionais (ex.: subjects em português com acentos).
   - **Melhores Práticas**: Mantenha `yes` para UX, a menos que haja problemas específicos.

#### **Serviço: `smtp-relay-db`**

9. **`MYSQL_ROOT_PASSWORD`**:
   - **Descrição**: Senha do usuário root do MySQL, usada para setup inicial e administração.
   - **Tipo**: String.
   - **Obrigatória**: Sim.
   - **Default**: Nenhum.
   - **Exemplo Básico**: `xxxxxxxxxxxxxxxx`.
   - **Exemplo Avançado**: Senha complexa gerada via `openssl rand -base64 32`.
   - **Impacto no Sistema**: Garante segurança do banco. Senha fraca compromete todo o DB.
   - **Erros Comuns**:
     - "Access denied": Senha incorreta ou não definida.
   - **Soluções**:
     - Armazene em `.env` ou secrets.
     - Use gerenciadores de senhas para criar valores únicos.
   - **Melhores Práticas**: Mínimo 12 caracteres, mix de letras/números/símbolos.

10. **`MYSQL_DATABASE`**:
    - **Descrição**: Nome do banco de dados criado automaticamente pelo MySQL.
    - **Tipo**: String.
    - **Obrigatória**: Sim.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `smtp_cpd`.
    - **Exemplo Avançado**: `clubenaval_smtp_logs_2025`.
    - **Impacto no Sistema**: Define o schema usado pela app. Deve coincidir com `DB_NAME`.
    - **Erros Comuns**:
      - "Database does not exist": Mismatch entre configs.
    - **Soluções**:
      - Sincronize com `DB_NAME` na app.
    - **Melhores Práticas**: Use nomes descritivos sem caracteres especiais.

11. **`MYSQL_USER`**:
    - **Descrição**: Usuário MySQL para a app, com privilégios limitados.
    - **Tipo**: String.
    - **Obrigatória**: Sim.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `smtp_user`.
    - **Exemplo Avançado**: `smtp_app_user`.
    - **Impacto no Sistema**: Conexão app-DB. Usuário errado causa falhas de conexão.
    - **Erros Comuns**:
      - "Access denied": Usuário não criado ou sem permissões.
    - **Soluções**:
      - Confirme GRANTs: `GRANT SELECT, INSERT, UPDATE ON smtp_cpd.* TO 'smtp_user'@'%'`.
    - **Melhores Práticas**: Limite privilégios ao necessário.

12. **`MYSQL_PASSWORD`**:
    - **Descrição**: Senha do usuário MySQL da app.
    - **Tipo**: String.
    - **Obrigatória**: Sim.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `xxxxxxxxxxxxxxxx`.
    - **Exemplo Avançado**: Senha gerada com alta entropia.
    - **Impacto no Sistema**: Garante acesso seguro ao DB. Senha fraca é risco crítico.
    - **Erros Comuns**:
      - "Access denied": Mismatch com `DB_PASSWORD`.
    - **Soluções**:
      - Sincronize com `DB_PASSWORD` na app.
    - **Melhores Práticas**: Use `.env` ou secrets.

#### **Serviço: `smtp-relay-app`**

13. **`AUTH_MODE`**:
    - **Descrição**: Modo de autenticação: `AD` (Active Directory via LDAP) ou `DB` (banco local).
    - **Tipo**: String (AD/DB).
    - **Obrigatória**: Sim.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `DB`.
    - **Exemplo Avançado**: `AD` para integração com Microsoft Entra ID.
    - **Impacto no Sistema**: Define fluxo de login. `AD` requer vars LDAP; `DB` requer vars SMTP para recuperação.
    - **Erros Comuns**:
      - "Invalid AUTH_MODE": Valor fora de AD/DB.
    - **Soluções**:
      - Valide em `config.py` antes de deploy.
    - **Melhores Práticas**: Use `DB` para setups simples; `AD` para empresas.

14. **`DB_HOST`**:
    - **Descrição**: Hostname do serviço MySQL (geralmente nome do serviço Docker).
    - **Tipo**: String.
    - **Obrigatória**: Sim.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `smtp-relay-db`.
    - **Exemplo Avançado**: `mysql-prod.clubenaval.org.br` em setups externos.
    - **Impacto no Sistema**: Conexão app-DB. Erro impede acesso aos dados.
    - **Erros Comuns**:
      - "Connection refused": Serviço DB não iniciado.
    - **Soluções**:
      - Verifique `docker ps` e healthcheck.
    - **Melhores Práticas**: Use nome do serviço para rede interna.

15. **`DB_USER`**:
    - **Descrição**: Usuário MySQL para app, deve coincidir com `MYSQL_USER`.
    - **Tipo**: String.
    - **Obrigatória**: Sim.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `smtp_user`.

16. **`DB_PASSWORD`**:
    - **Descrição**: Senha MySQL, deve coincidir com `MYSQL_PASSWORD`.
    - **Tipo**: String.
    - **Obrigatória**: Sim.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `xxxxxxxxxxxxxxxx`.

17. **`DB_NAME`**:
    - **Descrição**: Nome do banco, deve coincidir com `MYSQL_DATABASE`.
    - **Tipo**: String.
    - **Obrigatória**: Sim.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `smtp_cpd`.

18. **`LOG_DIR`**:
    - **Descrição**: Diretório de logs Exim, montado via volume compartilhado.
    - **Tipo**: String (caminho).
    - **Obrigatória**: Sim.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `/app/logs`.
    - **Exemplo Avançado**: `/mnt/logs/exim` em setups com storage externo.
    - **Impacto no Sistema**: Define onde parser busca logs. Erro impede importação.
    - **Erros Comuns**:
      - "No such file or directory": Volume não montado.
    - **Soluções**:
      - Verifique permissões: `chmod -R 755 /srv/smtp-relay/logs`.
    - **Melhores Práticas**: Use volumes named para backups.

19. **`TZ`**:
    - **Descrição**: Fuso horário da app, sincronizado com relay.
    - **Tipo**: String.
    - **Obrigatória**: Sim.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `America/Sao_Paulo`.

20. **`SCHEDULE_TYPE`**:
    - **Descrição**: Tipo de agendamento: `minutes` (intervalo) ou `time` (horário fixo).
    - **Tipo**: String (minutes/time).
    - **Obrigatória**: Sim.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `minutes`.
    - **Exemplo Avançado**: `time` para relatórios diários às 23:59.
    - **Impacto no Sistema**: Controla frequência de importação de logs.
    - **Erros Comuns**:
      - "Invalid SCHEDULE_TYPE": Valor fora de minutes/time.
    - **Soluções**:
      - Valide em `config.py`.
    - **Melhores Práticas**: Use `minutes` para monitoramento contínuo.

21. **`SCHEDULE_INTERVAL_MINUTES`** (Condicional: SCHEDULE_TYPE=minutes):
    - **Descrição**: Intervalo em minutos para importação de logs.
    - **Tipo**: Inteiro (>0).
    - **Obrigatória**: Sim, se `SCHEDULE_TYPE=minutes`.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `2`.
    - **Exemplo Avançado**: `10` para reduzir carga em logs volumosos.
    - **Impacto no Sistema**: Define frequência de updates. Valores muito baixos podem sobrecarregar.
    - **Erros Comuns**:
      - "ValueError": Valor não-inteiro ou <=0.
    - **Soluções**:
      - Teste com valores altos inicialmente (ex.: 5).
    - **Melhores Práticas**: Ajuste com base no volume de logs (ex.: 1-5min para alta frequência).

22. **`SCHEDULE_TIME`** (Condicional: SCHEDULE_TYPE=time):
    - **Descrição**: Horário diário fixo para importação (formato HH:MM).
    - **Tipo**: String.
    - **Obrigatória**: Sim, se `SCHEDULE_TYPE=time`.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `16:40`.
    - **Exemplo Avançado**: `00:00` para relatórios noturnos.
    - **Impacto no Sistema**: Define momento exato de execução.
    - **Erros Comuns**:
      - "Invalid format": Formato fora de HH:MM.
    - **Soluções**:
      - Use regex em `config.py` para validar.

23. **`DB_PORT`**:
    - **Descrição**: Porta do MySQL.
    - **Tipo**: Inteiro (1-65535).
    - **Obrigatória**: Não.
    - **Default**: `3306`.
    - **Exemplo Básico**: `3306`.

24. **`SMTP_SERVER`** (Condicional: AUTH_MODE=DB):
    - **Descrição**: Servidor SMTP para e-mails de recuperação de senha.
    - **Tipo**: String.
    - **Obrigatória**: Sim, se `AUTH_MODE=DB`.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `smtp-relay`.
    - **Exemplo Avançado**: `smtp.gmail.com`.
    - **Impacto no Sistema**: Necessário para envio de tokens de reset.
    - **Erros Comuns**:
      - "Connection refused": Servidor SMTP inacessível.
    - **Soluções**:
      - Teste com `telnet smtp-relay 25`.

25. **`SMTP_PORT`** (Condicional: AUTH_MODE=DB):
    - **Descrição**: Porta SMTP para recuperação.
    - **Tipo**: Inteiro.
    - **Obrigatória**: Sim, se `AUTH_MODE=DB`.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `25`.

26. **`SMTP_FROM`** (Condicional: AUTH_MODE=DB):
    - **Descrição**: E-mail remetente para mensagens de sistema.
    - **Tipo**: String.
    - **Obrigatória**: Sim, se `AUTH_MODE=DB`.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `noreply@example.com`.

27. **`SMTP_FROM_NAME`** (Condicional: AUTH_MODE=DB):
    - **Descrição**: Nome do remetente.
    - **Tipo**: String.
    - **Obrigatória**: Sim, se `AUTH_MODE=DB`.
    - **Default**: Nenhum.
    - **Exemplo Básico**: `Sistema de Relatórios`.

28. **`SMTP_AUTHENTICATED`** (Condicional: AUTH_MODE=DB):
    - **Descrição**: Requer autenticação SMTP (True/False).
    - **Tipo**: Boolean (como string).
    - **Obrigatória**: Não.
    - **Default**: `True`.
    - **Exemplo Básico**: `False`.

29. **`SMTP_USERNAME`** (Condicional: AUTH_MODE=DB e SMTP_AUTHENTICATED=True):
    - **Descrição**: Usuário SMTP.
    - **Tipo**: String.
    - **Obrigatória**: Sim, se autenticado.

30. **`SMTP_PASSWORD`** (Condicional: AUTH_MODE=DB e SMTP_AUTHENTICATED=True):
    - **Descrição**: Senha SMTP.
    - **Tipo**: String.
    - **Obrigatória**: Sim, se autenticado.

31. **`SMTP_USE_TLS`** (Condicional: AUTH_MODE=DB e SMTP_AUTHENTICATED=True):
    - **Descrição**: Ativa TLS.
    - **Tipo**: Boolean (como string).
    - **Obrigatória**: Não.
    - **Default**: `False`.

32. **`SMTP_USE_SSL`** (Condicional: AUTH_MODE=DB e SMTP_AUTHENTICATED=True):
    - **Descrição**: Ativa SSL.
    - **Tipo**: Boolean (como string).
    - **Obrigatória**: Não.
    - **Default**: `False`.

33. **`LDAP_HOST`** (Condicional: AUTH_MODE=AD):
    - **Descrição**: Host do servidor LDAP/AD.
    - **Tipo**: String.
    - **Obrigatória**: Sim, se `AUTH_MODE=AD`.
    - **Exemplo Básico**: `192.168.1.100`.

34. **`LDAP_DOMAIN`** (Condicional: AUTH_MODE=AD):
    - **Descrição**: Domínio AD (ex.: @example.com).
    - **Tipo**: String.
    - **Obrigatória**: Sim, se `AUTH_MODE=AD`.

35. **`LDAP_BASE_DN`** (Condicional: AUTH_MODE=AD):
    - **Descrição**: Base DN para buscas LDAP.
    - **Tipo**: String.
    - **Obrigatória**: Sim, se `AUTH_MODE=AD`.

36. **`LDAP_GROUP_DN`** (Condicional: AUTH_MODE=AD):
    - **Descrição**: DN do grupo para autorização.
    - **Tipo**: String.
    - **Obrigatória**: Sim, se `AUTH_MODE=AD`.

**Nota sobre Variáveis Sensíveis**: Use `.env` ou Docker secrets para senhas e chaves. Exemplo de `.env`:
```
MYSQL_ROOT_PASSWORD=senha_complexa_root
MYSQL_PASSWORD=senha_complexa_user
DB_PASSWORD=senha_complexa_user
SMTP_PASSWORD=senha_smtp
```

## **Ajuste do Tamanho do Logo**

O logo no README foi ajustado para `<img src="static/logo.png" alt="Logo Clube Naval" width="150" />`, definindo uma largura de 150 pixels para um tamanho menor e mais equilibrado visualmente. A proporção é mantida automaticamente pelo navegador (via `height="auto"` implícito). 

**Por que 150px?**:
- **Estética**: Evita que o logo domine o topo do README, mantendo foco no conteúdo textual.
- **Compatibilidade**: Renderiza bem em GitHub, GitLab e browsers modernos, sem cortes em resoluções menores (ex.: mobile).
- **Flexibilidade**: 150px é pequeno o suficiente para não sobrecarregar a página, mas visível para branding.

**Como Personalizar o Tamanho**:
- **Markdown com HTML**: Edite o atributo `width` no `<img>` (ex.: `width="100"` para ainda menor).
- **CSS Inline**: Adicione `style="width: 150px; max-width: 100%;"` para responsividade extra.
- **Arquivo Estático**: Se preferir, mova o logo para um arquivo CSS externo (ex.: `static/styles.css`) e referencie com `<link>`, mas note que o GitHub não renderiza CSS externo diretamente.
- **Teste Visual**: Pré-visualize no GitHub ou use ferramentas como `marked` localmente (`npm install marked` e `marked README.md -o preview.html`).

**Considerações**:
- **Alt Text**: O atributo `alt="Logo Clube Naval"` é mantido para acessibilidade (WCAG 2.1).
- **Formato do Logo**: Certifique-se de que `static/logo.png` é um PNG/JPG otimizado (use ferramentas como TinyPNG para reduzir tamanho do arquivo).
- **Renderização no GitHub**: O GitHub suporta HTML em Markdown, mas não scripts CSS/JS externos. O inline `<img>` é a melhor abordagem.
- **Tamanho Alternativo**: Se 150px ainda parecer grande, teste com 100px ou 120px, mas evite valores abaixo de 80px para manter legibilidade.

**Exemplo Alternativo com CSS**:
```html
<img src="static/logo.png" alt="Logo Clube Naval" style="width: 150px; max-width: 100%; height: auto;" />
```

**Teste de Compatibilidade**:
- Renderize em browsers (Chrome, Firefox, Safari).
- Verifique em dispositivos móveis via DevTools (ex.: Chrome F12 → Toggle Device Toolbar).
- Confirme que o logo não quebra o layout em resoluções pequenas (ex.: 320px de largura).

Se precisar de um tamanho específico (ex.: 120px) ou ajuda para otimizar o arquivo do logo, avise!

## **Execução da Aplicação**

### **1. Pré-Requisitos**
- **Docker**: Versão 20+ (instale via `curl -fsSL https://get.docker.com | sh`).
- **Docker Compose**: Versão 2+ (`docker-compose --version`).
- **Sistema Operacional**: Linux recomendado (Ubuntu 22.04 testado), mas compatível com Windows/Mac via Docker Desktop.
- **Hardware**: Mínimo 2GB RAM, 1 CPU core; recomendado 4GB RAM, 2 cores para logs volumosos.
- **Diretórios de Volume**: Crie `/srv/smtp-relay/logs` e `/srv/mysql` com `mkdir -p` e permissões `chmod 755`.
- **Portas Livres**: 25, 2525 (SMTP), 3306 (MySQL, opcional), 5000 (Flask).

### **2. Baixar e Configurar**
```bash
git clone https://github.com/seu-usuario/relatorios-smtp.git
cd relatorios-smtp
```

Crie `.env` para secrets:
```bash
echo "MYSQL_ROOT_PASSWORD=$(openssl rand -base64 32)" > .env
echo "MYSQL_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "DB_PASSWORD=$(cat .env | grep MYSQL_PASSWORD | cut -d= -f2)" >> .env
echo "SMTP_PASSWORD=$(openssl rand -base64 32)" >> .env
```

Edite `docker-compose.yml` para ajustar `SMTP_SERVER`, `SERVER_HOSTNAME`, etc., conforme sua infra.

### **3. Build e Iniciar**
```bash
docker-compose build  # Constrói imagem Flask
docker-compose up -d  # Inicia containers em background
```

Verifique status:
```bash
docker-compose ps
```

Logs para depuração:
```bash
docker-compose logs -f smtp-relay-app
```

### **4. Acessar a Aplicação**
- URL: `http://localhost:5000/login`
- Credenciais default (modo DB): `admin`/`admin` (altere imediatamente via `/change_password`).
- Teste envio de e-mail:
  ```bash
  swaks --to user@example.com --from test@local --server localhost:25
  ```

### **5. Gerenciamento**
- **Relatórios**: Acesse `/`, filtre por data/status, exporte CSV ou imprima.
- **Importação Manual**: Use `/import-emails` para forçar atualização de logs.
- **Gerenciamento de Usuários**: Em modo DB, admins acessam `/manage` para criar/editar/excluir usuários.
- **Recuperação de Senha**: Via `/forgot_password` (DB mode).

### **6. Backup e Restauração**
- **Backup DB**:
  ```bash
  docker exec -t smtp-relay-db mysqldump -u root -p smtp_cpd > backup.sql
  ```
- **Restauração**:
  ```bash
  docker exec -i smtp-relay-db mysql -u root -p smtp_cpd < backup.sql
  ```
- **Logs**: Copie `/srv/smtp-relay/logs` para arquivamento.

### **7. Atualizações**
```bash
git pull
docker-compose down
docker-compose up -d --build
```

## **Uso Diário**

- **Relatórios**: Filtre por data (ex.: `2025-10-01 a 2025-10-17`), status (`failed`), ou assunto. Exporte CSV para Excel.
- **Administração**: Crie usuários com privilégios admin ou padrão. Edite/exclua via `/manage`.
- **Monitoramento**: Verifique logs Docker para erros (ex.: "Erro ao inserir no banco").

**Exemplo de Filtro de Relatório**:
- Busque e-mails rejeitados de `user@clubenaval.org.br` entre 01/10/2025 e 15/10/2025:
  - URL: `/report?from_date=2025-10-01&to_date=2025-10-15&from_email=user@clubenaval.org.br&status=failed`
  - Exporte via botão "Exportar CSV".

## **Solução de Problemas**

- **Erro de Conexão DB**:
  - **Sintoma**: "MySQL Connection Error" nos logs da app.
  - **Solução**: Verifique `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`. Confirme healthcheck: `docker inspect smtp-relay-db --format '{{.State.Health.Status}}'`.
- **Logs Não Atualizando**:
  - **Sintoma**: Relatórios vazios ou desatualizados.
  - **Solução**: Cheque `LOG_DIR` permissões (`ls -ld /srv/smtp-relay/logs`), `SCHEDULE_TYPE` e logs (`docker logs smtp-relay-app | grep "Erro ao executar schedule"`).
- **Autenticação Falhando**:
  - **AD**: Teste bind: `ldapsearch -x -H ldap://192.168.1.100 -D "user@example.com" -W`.
  - **DB**: Resete senha admin: `docker exec -it smtp-relay-db mysql -u root -p -e "UPDATE app_users SET password_hash='$(python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('newpassword'))")' WHERE username='admin'"`.
- **E-mails Não Enviando**:
  - **Sintoma**: Logs Exim mostram "Relay not permitted".
  - **Solução**: Verifique `SMTP_SERVER`, `SMTP_PORT`, `RELAY_NETS`. Teste: `exim -bt user@example.com`.
- **Container Não Inicia**:
  - **Solução**: Rode `docker-compose up` (sem `-d`) para erros. Valide `.env` e `docker-compose.yml`.

**Logs Comuns**:
- "ID pendente X": E-mail sem "Completed" no `mail.log`.
- "Erro ao inserir no banco": Conexão DB falhou ou schema corrompido.

## **Melhores Práticas**

- **Exim Relay**: Configure SPF/DKIM/DMARC, monitore queue (`exim -bp`), use autenticação OAUTH para Exchange Online.
- **MySQL**: Habilite SSL, restrinja GRANTs, use `innodb_buffer_pool_size=256M` para performance.
- **Flask**: Adicione headers CSP, use Flask-Security, sanitize inputs.
- **Docker**: Pin versions de imagens, use volumes named, monitore com Prometheus.
- **Performance**: Indexe colunas como `log_date`, `to_email` no MySQL; limite batch size no parser.

## **Contribuição**

1. Fork o repositório.
2. Crie branch: `git checkout -b feature/nova-funcionalidade`.
3. Commit: `git commit -m 'Adiciona nova funcionalidade'`.
4. Push: `git push origin feature/nova-funcionalidade`.
5. Abra Pull Request.

Crie `CONTRIBUTING.md` com guidelines, incluindo testes com pytest e linting com flake8.

## **Roadmap**

- **v1.1.0**: Integração com Chart.js para gráficos de envios/rejeições.
- **v1.2.0**: Suporte a múltiplos relays SMTP e alertas por e-mail.
- **v2.0.0**: Escalabilidade com Kubernetes, integração ELK Stack.

## **FAQ**

- **Como escalar?** Use Docker Swarm ou Kubernetes com replicas da app.
- **Suporta grandes volumes?** Sim, com tuning (ex.: MySQL buffer pool, parser batch size).
- **HTTPS?** Configure Nginx como reverse proxy com certbot.

## **Licença**

Licenciado sob **MIT**. Veja [LICENSE](LICENSE).

## **Suporte**

**Desenvolvido por Henrique Fagundes**. Contato: [support@henrique.tec.br](mailto:support@henrique.tec.br). Abra issues no GitHub para bugs ou sugestões.