# 🚀 Guia de Deploy - Futbin Scraper

## 📋 Pré-requisitos

- ✅ Conta no GitHub
- ✅ Conta no Railway (gratuita)
- ✅ Bot do Telegram configurado

## 🔧 Passo a Passo

### 1. Preparar o Repositório

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/futbin-scraper.git
cd futbin-scraper

# Adicione todos os arquivos
git add .

# Commit inicial
git commit -m "Initial commit: Futbin Scraper completo"

# Push para GitHub
git push origin main
```

### 2. Configurar Railway

1. **Acesse [Railway.app](https://railway.app)**
2. **Faça login com GitHub**
3. **Clique em "New Project"**
4. **Selecione "Deploy from GitHub repo"**
5. **Escolha seu repositório**
6. **Clique em "Deploy Now"**

### 3. Configurar Variáveis de Ambiente

No Railway, vá em **Variables** e adicione:

```env
TELEGRAM_BOT_TOKEN=8450381764:AAHS7rOLqUZjdoMgypzKaots282jf9CQlfw
MYSQL_HOST=srv1577.hstgr.io
MYSQL_USER=u559058762_claudinez
MYSQL_PASSWORD=Cms332211
MYSQL_DATABASE=u559058762_futbin
```

### 4. Configurar Telegram

1. **Abra o Telegram**
2. **Procure por @BotFather**
3. **Envie /start**
4. **Envie /newbot**
5. **Siga as instruções**
6. **Copie o token gerado**
7. **Atualize no Railway**

### 5. Testar o Deploy

1. **Aguarde o deploy terminar**
2. **Vá em "Deployments"**
3. **Clique no deploy mais recente**
4. **Verifique os logs**
5. **Confirme que está funcionando**

## 📊 Monitoramento

### Logs do Railway
- **Acesse**: Railway Dashboard → Seu Projeto → Deployments
- **Clique**: No deploy mais recente
- **Verifique**: Logs em tempo real

### Notificações Telegram
- **Progresso**: A cada 50 cartas
- **Seções**: Conclusão de cada seção
- **Erros**: Notificação imediata
- **Conclusão**: Relatório final

## 🔧 Troubleshooting

### Erro: "Module not found"
```bash
# Verifique se requirements.txt está correto
pip install -r requirements.txt
```

### Erro: "Database connection failed"
```bash
# Verifique as variáveis de ambiente
echo $MYSQL_HOST
echo $MYSQL_USER
echo $MYSQL_PASSWORD
```

### Erro: "Telegram token invalid"
```bash
# Regenere o token no @BotFather
# Atualize no Railway
```

## 📈 Estatísticas Esperadas

- **Tempo total**: 35-40 horas
- **Cartas coletadas**: ~23.580
- **Taxa de sucesso**: ~95%
- **Memória**: ~200MB
- **CPU**: Baixo uso

## 🎯 Próximos Passos

1. **Monitore os logs** nas primeiras horas
2. **Verifique as notificações** do Telegram
3. **Confirme** que as cartas estão sendo salvas
4. **Ajuste** configurações se necessário

## 🆘 Suporte

- **Issues**: GitHub Issues
- **Railway**: Railway Discord
- **Telegram**: @seu_usuario

---

**🚀 Deploy concluído! O scraper está rodando 24/7 no Railway!** 