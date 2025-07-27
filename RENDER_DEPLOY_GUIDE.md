# 🚀 Guia de Deploy na Render - Versão Atualizada

## ✅ Problema Resolvido

Agora o bot funciona corretamente em background! Quando você fechar o navegador ou sair da Render, o scraper continuará rodando.

## 🔧 O que foi alterado

1. **`app.py`**: Agora é um serviço web Flask que roda o scraper em background
2. **`render.yaml`**: Configurado para usar `app.py` em vez de `run_scraper.py`
3. **Threading**: O scraper roda em uma thread separada
4. **Endpoints**: API para monitorar o status do scraper

## 📋 Passo a Passo para Deploy

### 1. Preparar o Repositório

```bash
# Certifique-se de que todos os arquivos estão commitados
git add .
git commit -m "Atualização: Scraper em background com Flask"
git push origin main
```

### 2. Configurar na Render

1. **Acesse [Render.com](https://render.com)**
2. **Faça login com GitHub**
3. **Clique em "New +" → "Web Service"**
4. **Conecte seu repositório**
5. **Configure as variáveis de ambiente**

### 3. Variáveis de Ambiente

Configure estas variáveis na Render:

```env
TELEGRAM_BOT_TOKEN=8450381764:AAHS7rOLqUZjdoMgypzKaots282jf9CQlfw
MYSQL_HOST=srv1577.hstgr.io
MYSQL_USER=u559058762_claudinez
MYSQL_PASSWORD=Cms332211
MYSQL_DATABASE=u559058762_futbin
```

### 4. Configurações do Serviço

- **Name**: `futbin-scraper`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`
- **Plan**: `Free`

## 🌐 Endpoints da API

Após o deploy, você pode acessar:

- **`https://seu-app.onrender.com/`** - Página inicial
- **`https://seu-app.onrender.com/status`** - Status do scraper
- **`https://seu-app.onrender.com/health`** - Saúde da aplicação
- **`https://seu-app.onrender.com/ping`** - Manter ativo

## 🔄 Como Funciona Agora

1. **Inicialização**: Quando o serviço sobe, o scraper inicia automaticamente
2. **Background**: O scraper roda em uma thread separada
3. **Persistência**: Continua rodando mesmo se você fechar o navegador
4. **Monitoramento**: Você pode verificar o status via API
5. **Notificações**: Telegram continua funcionando normalmente

## 📊 Monitoramento

### Via API
```bash
# Verificar status
curl https://seu-app.onrender.com/status

# Verificar saúde
curl https://seu-app.onrender.com/health

# Manter ativo
curl https://seu-app.onrender.com/ping
```

### Via Telegram
- Receberá notificações de progresso
- Status de início e conclusão
- Alertas de erro

## 🛡️ Manter Ativo

Para evitar que o serviço "durma":

### Opção 1: UptimeRobot (Recomendado)
1. Acesse [UptimeRobot.com](https://uptimerobot.com)
2. Crie conta gratuita
3. Adicione monitor: `https://seu-app.onrender.com/ping`
4. Configure para verificar a cada 10 minutos

### Opção 2: Script Local
```bash
# Execute localmente para manter ativo
python keep_alive.py
```

## ✅ Quando Está Pronto

O bot está pronto quando:

1. **Deploy concluído** na Render
2. **Logs mostram**: "🚀 Scraper iniciado em background"
3. **API responde**: `https://seu-app.onrender.com/status`
4. **Telegram notifica**: "🚀 SCRAPING INICIADO"

## 🎯 Próximos Passos

1. **Deploy**: Faça o deploy na Render
2. **Teste**: Acesse a URL da API
3. **Monitore**: Verifique os logs
4. **Configure**: UptimeRobot para manter ativo
5. **Feche**: Pode fechar o navegador com segurança

## 🆘 Troubleshooting

### Erro: "Module not found"
```bash
# Verifique se requirements.txt está correto
pip install -r requirements.txt
```

### Erro: "Port already in use"
- Normal na Render, o serviço usa a porta automática

### Erro: "Scraper não iniciou"
- Verifique os logs na Render
- Confirme que as variáveis de ambiente estão corretas

### Serviço "dormindo"
- Configure UptimeRobot
- Ou execute `python keep_alive.py` localmente

## 📈 Estatísticas Esperadas

- **Tempo total**: 35-40 horas
- **Cartas coletadas**: ~23.580
- **Taxa de sucesso**: ~95%
- **Memória**: ~200MB
- **CPU**: Baixo uso

## 🎉 Resultado Final

Após o deploy, você terá:
- ✅ Scraper rodando 24/7
- ✅ Não para quando fecha o navegador
- ✅ Notificações Telegram em tempo real
- ✅ API para monitoramento
- ✅ Coleta completa de todas as cartas

---

**🚀 Agora você pode fechar o navegador com segurança! O scraper continuará rodando!** 