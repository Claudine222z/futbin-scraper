# 🏆 Futbin Scraper - Coleta Completa

Sistema automatizado para coleta de todas as cartas do Futbin EA FC 25.

## 🚀 Funcionalidades

- ✅ **Coleta completa**: 786 páginas (23.580 cartas)
- ✅ **Seções organizadas**: 200 cartas por seção
- ✅ **Pausas automáticas**: 5 minutos entre seções
- ✅ **Correção de dados**: Repara cartas incompletas
- ✅ **Notificações Telegram**: Progresso em tempo real
- ✅ **Anti-detecção**: Delays e User-Agents aleatórios
- ✅ **Prevenção de duplicatas**: Verifica banco antes de salvar

## 📊 Configurações

- **Total de páginas**: 786
- **Cartas por página**: 30
- **Total estimado**: 23.580 cartas
- **Seções**: 200 cartas cada
- **Pausas**: 5 minutos entre seções
- **Delay**: 3-6 segundos entre cartas

## 🛠️ Tecnologias

- **Python 3.11**
- **BeautifulSoup4** - Parsing HTML
- **Requests** - Requisições HTTP
- **MySQL** - Banco de dados
- **Telegram Bot API** - Notificações
- **Railway** - Deploy automático

## 📁 Estrutura do Projeto

```
scraper/
├── futbin_mass_scraper.py    # Scraper principal
├── telegram_bot.py           # Notificações Telegram
├── simple_futbin_scraper.py  # Lógica de extração
├── app.py                    # API Flask
├── run_scraper.py           # Script de execução
├── requirements.txt         # Dependências
├── railway.json            # Config Railway
├── Procfile                # Deploy Railway
└── README.md               # Documentação
```

## 🔧 Instalação Local

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/futbin-scraper.git
cd futbin-scraper
```

2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente**
```bash
# Crie um arquivo .env
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
```

4. **Execute o scraper**
```bash
python run_scraper.py
```

## 🚀 Deploy na Render (Versão Atualizada)

**✅ PROBLEMA RESOLVIDO**: Agora o bot funciona em background! Quando você fechar o navegador, o scraper continuará rodando.

### 📋 Passo a Passo

1. **Fork este repositório**
2. **Acesse [Render.com](https://render.com)**
3. **Faça login com GitHub**
4. **Clique em "New +" → "Web Service"**
5. **Conecte seu repositório**
6. **Configure as variáveis de ambiente**
7. **Deploy automático!**

### ⚙️ Configuração na Render

**Nome**: `futbin-scraper`  
**Environment**: `Python 3`  
**Build Command**: `pip install -r requirements.txt`  
**Start Command**: `python app.py` *(ATUALIZADO)*  
**Plan**: `Free`

### 🔄 Como Funciona Agora

- ✅ **Background**: Scraper roda em thread separada
- ✅ **Persistência**: Continua rodando mesmo fechando navegador
- ✅ **API**: Endpoints para monitoramento
- ✅ **Telegram**: Notificações em tempo real

### 🔧 Variáveis de Ambiente

Configure estas variáveis na Render:

```env
TELEGRAM_BOT_TOKEN=8450381764:AAHS7rOLqUZjdoMgypzKaots282jf9CQlfw
MYSQL_HOST=srv1577.hstgr.io
MYSQL_USER=u559058762_claudinez
MYSQL_PASSWORD=Cms332211
MYSQL_DATABASE=u559058762_futbin
```

### 🌐 Endpoints da API

Após o deploy, você pode acessar:

- **`https://seu-app.onrender.com/`** - Página inicial
- **`https://seu-app.onrender.com/status`** - Status do scraper
- **`https://seu-app.onrender.com/health`** - Saúde da aplicação
- **`https://seu-app.onrender.com/ping`** - Manter ativo

### 🛡️ Manter Ativo

Para evitar que o serviço "durma":

1. **UptimeRobot** (Recomendado):
   - Acesse [UptimeRobot.com](https://uptimerobot.com)
   - Configure monitor: `https://seu-app.onrender.com/ping`
   - Verificar a cada 10 minutos

2. **Script Local**:
   ```bash
   python keep_alive.py
   ```



## ✅ Quando o Bot Está Pronto

O bot está pronto quando:

1. **Deploy concluído** na Render
2. **Logs mostram**: "🚀 Scraper iniciado em background"
3. **API responde**: `https://seu-app.onrender.com/status`
4. **Telegram notifica**: "🚀 SCRAPING INICIADO"

**🎉 Depois disso, você pode fechar o navegador com segurança!**

## 📱 Configuração Telegram

1. **Crie um bot** via @BotFather
2. **Obtenha o token**
3. **Configure na Render** como variável de ambiente
4. **Receba notificações** em tempo real

## 📊 Monitoramento

- **Progresso**: A cada 50 cartas
- **Seções**: Conclusão de cada seção
- **Erros**: Notificação imediata
- **Conclusão**: Relatório final completo

## 🔒 Segurança

- **Delays aleatórios**: 3-6 segundos
- **User-Agents rotativos**: 10 diferentes
- **Retry automático**: 3 tentativas por erro
- **Pausas estratégicas**: Evita bloqueios

## 📈 Estatísticas

- **Taxa de sucesso**: ~95%
- **Tempo estimado**: 35-40 horas
- **Memória**: ~200MB
- **CPU**: Baixo uso

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 Suporte

- **Issues**: GitHub Issues
- **Telegram**: @seu_usuario
- **Email**: seu@email.com

---

**Desenvolvido com ❤️ para a comunidade FIFA/EA FC** 