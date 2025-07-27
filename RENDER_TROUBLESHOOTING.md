# 🔧 Troubleshooting - Render Deploy

## ❌ Problema: Serviço não responde

Se o serviço não está respondendo na Render, siga estes passos:

## 🔍 Passo 1: Verificar Configurações na Render

### 1. Acesse o Render Dashboard
- Vá para [render.com](https://render.com)
- Faça login e acesse seu projeto `futbin-scraper`

### 2. Verifique as Configurações
Na seção **Settings** do seu serviço, confirme:

**✅ Start Command deve ser:**
```
python app.py
```

**❌ NÃO deve ser:**
```
python run_scraper.py
```

### 3. Verifique Build Command
```
pip install -r requirements.txt
```

### 4. Verifique Environment
```
Python 3
```

## 🔍 Passo 2: Verificar Variáveis de Ambiente

Na seção **Environment Variables**, confirme que estão configuradas:

```env
TELEGRAM_BOT_TOKEN=8450381764:AAHS7rOLqUZjdoMgypzKaots282jf9CQlfw
MYSQL_HOST=srv1577.hstgr.io
MYSQL_USER=u559058762_claudinez
MYSQL_PASSWORD=Cms332211
MYSQL_DATABASE=u559058762_futbin
```

## 🔍 Passo 3: Verificar Logs

1. Vá para a aba **Logs**
2. Procure por erros recentes
3. Procure por: `🚀 Scraper iniciado em background`

### Logs Esperados (Sucesso):
```
🚀 Iniciando Futbin Scraper...
🚀 Scraper iniciado em background
🌐 Servidor iniciado na porta 5000
```

### Logs de Erro Comuns:
```
ModuleNotFoundError: No module named 'flask'
```
→ **Solução**: Verificar se `Flask>=2.3.0` está no `requirements.txt`

```
ImportError: No module named 'futbin_mass_scraper'
```
→ **Solução**: Verificar se todos os arquivos estão no repositório

## 🔍 Passo 4: Forçar Novo Deploy

### Opção 1: Manual Deploy
1. No Render Dashboard
2. Clique em **"Manual Deploy"**
3. Selecione **"Deploy latest commit"**

### Opção 2: Commit Vazio
```bash
git commit --allow-empty -m "Forçar deploy"
git push origin main
```

## 🔍 Passo 5: Testar Localmente

Execute localmente para verificar se funciona:

```bash
python app.py
```

Deve mostrar:
```
🚀 Iniciando Futbin Scraper...
🚀 Scraper iniciado em background
🌐 Servidor iniciado na porta 5000
```

## 🔍 Passo 6: Verificar Arquivos

Confirme que estes arquivos estão no repositório:
- ✅ `app.py`
- ✅ `futbin_mass_scraper.py`
- ✅ `telegram_bot.py`
- ✅ `requirements.txt`
- ✅ `render.yaml`

## 🚀 Solução Rápida

Se nada funcionar, tente:

1. **Deletar o serviço na Render**
2. **Criar um novo serviço**
3. **Conectar o mesmo repositório**
4. **Configurar Start Command como `python app.py`**
5. **Adicionar variáveis de ambiente**
6. **Fazer deploy**

## 📞 Suporte

Se ainda não funcionar:
1. Verifique os logs completos na Render
2. Teste localmente primeiro
3. Confirme que todos os arquivos estão no GitHub

---

**🎯 Lembre-se: O Start Command DEVE ser `python app.py` para funcionar em background!** 