# 🎨 ROSITA - Frontend Moderno

## 📋 O que foi criado?

Um **frontend completamente novo e moderno** para a ROSITA, com identidade visual roxa/branca elegante e profissional.

### Arquivos Novos:

1. **`web/index.html`** - Layout novo com:
   - Sidebar escura com navegação inteligente
   - Autenticação moderna (login/logout)
   - Chat como foco principal
   - Painel administrativo integrado
   - Dashboard de status do sistema
   - Design 100% responsivo

2. **`web/styles/main.css`** - Stylesheet completo:
   - Paleta roxa (#7c3aed) com detalhes brancos
   - Sidebar escuro (#0f172a)
   - Cards brancos com sombras elegantes
   - Animações suaves
   - Totalmente responsivo

3. **`web/scripts/main.js`** - Controlador JavaScript:
   - Navegação entre seções
   - Sistema de abas administrativas
   - Chat com streaming
   - Gerenciamento de modelos
   - Editor de configurações
   - Dashboard de monitoramento

---

## 🚀 Como Usar

### Iniciar o Sistema

```bash
# Windows
cd c:\AGENTE_TCC
start_system.bat

# Linux/Mac
cd /AGENTE_TCC
bash start_system.sh
```

### Acessar a Interface

1. Abra seu navegador
2. Acesse: `http://localhost:18080`
3. Faça login com sua conta de administrador ou usuário.

OBS: Não compartilhe credenciais reais no repositório. As credenciais de exemplo
fornecidas anteriormente foram removidas por motivos de segurança.

Para configurar as credenciais, defina as variáveis de ambiente no arquivo `.env`:

- `ROSITA_ADMIN_USERNAME` — nome do usuário admin (ex.: admin)
- `ROSITA_ADMIN_PASSWORD_HASH` — hash da senha do admin (use Werkzeug para gerar)
- `ROSITA_USER_USERNAME` — nome do usuário comum (ex.: usuario)
- `ROSITA_USER_PASSWORD_HASH` — hash da senha do usuário

Veja `.env.example` para o conjunto de variáveis suportadas e instruções de geração de hash.

---

## 🎯 Arquitetura da Interface

```
┌─────────────────────────────────────────────┐
│  ROSITA - Assistente Escolar Inteligente    │
├──────────────┬──────────────────────────────┤
│   SIDEBAR    │      MAIN CONTENT            │
│   (escuro)   │      (claro)                 │
│              │                              │
│  ℝ ROSITA    │  ┌──────────────────────┐   │
│  Assistente  │  │  CHAT / ADMIN / STATUS   │
│              │  │     (Seções)             │
│              │  │                          │
│  🔹 Chat     │  │  [Conteúdo Dinâmico]    │
│  🔹 Admin    │  │                          │
│  🔹 Status   │  │                          │
│              │  └──────────────────────┘   │
│              │                              │
│  ─────────   │                              │
│  👤 Usuario  │                              │
│     admin    │                              │
│  [Logout]    │                              │
└──────────────┴──────────────────────────────┘
```

---

## 🎨 Paleta de Cores

| Elemento | Cor | Código |
|----------|-----|--------|
| Primário (Roxo) | 🟣 | `#7c3aed` |
| Roxo Escuro | 🟣 | `#6d28d9` |
| Roxo Claro | 🟣 | `#a78bfa` |
| Roxo Suave | ✨ | `#ede9fe` |
| Sidebar | ⬛ | `#0f172a` |
| Fundo | ⬜ | `#f9fafb` |
| Texto Primário | ⬛ | `#111827` |
| Texto Secundário | ⬜ | `#6b7280` |
| Branco Puro | ⚪ | `#ffffff` |

---

## ✨ Recursos

### Chat
- ✅ Histórico de mensagens
- ✅ Streaming em tempo real (SSE)
- ✅ Seletor de modelos IA
- ✅ Contador de caracteres
- ✅ Limpar histórico
- ✅ Entrada de teclado (Enter para enviar)

### Administração
- ✅ **Modelo Ativo**: Selecionar, descarregar, excluir modelos
- ✅ **Referências**: Editar arquivos de configuração
- ✅ **Download**: Baixar novos modelos com progresso
- ✅ Acesso restrito (apenas admin)

### Status
- ✅ Indicador de conectividade
- ✅ Modelo ativo atual
- ✅ CPU, Memória, Disco, GPU
- ✅ Informações do servidor

### Autenticação
- ✅ Login/Logout
- ✅ Roles (admin, user, guest)
- ✅ Avatar personalizado
- ✅ Sessões persistentes

---

## 📱 Responsividade

| Dispositivo | Breakpoint | Comportamento |
|-----------|-----------|----------------|
| Desktop | >1024px | Sidebar visível + conteúdo pleno |
| Tablet | 768-1024px | Sidebar reduzido |
| Mobile | <768px | Sidebar oculta, conteúdo fullscreen |

---

## 🔧 Customização

### Cores
Edite as variáveis CSS em `web/styles/main.css`:

```css
:root {
  --color-primary: #7c3aed;        /* Roxo principal */
  --color-primary-dark: #6d28d9;   /* Roxo escuro */
  --color-sidebar: #0f172a;        /* Sidebar */
}
```

### Textos
As mensagens padrão estão em `web/scripts/main.js`:

```javascript
// Você pode localizar e modificar strings de texto conforme necessário
```

---

## 🧪 Testes Rápidos

1. **Login Admin**:
   - Usuário: <SEU_USUARIO_ADMIN>
   - Senha: <SUA_SENHA_ADMIN> (configure o hash em `.env`)
   - Acesso: Chat + Admin + Status

2. **Login Usuário**:
   - Usuário: <SEU_USUARIO_COMUM>
   - Senha: <SUA_SENHA_USUARIO> (configure o hash em `.env`)
   - Acesso: Chat apenas

3. **Funcionalidades para testar**:
   - ✅ Navegar entre Chat, Admin e Status (sidebar)
   - ✅ Enviar mensagens de chat
   - ✅ Abas do painel admin (Modelo, Referências, Download)
   - ✅ Ver status do sistema
   - ✅ Responsividade (redimensionar janela ou testar mobile)

---

## 📝 Compatibilidade

- ✅ Chrome/Chromium (recomendado)
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ✅ Mobile browsers

---

## 🐛 Troubleshooting

### Problema: Estilos não aparecem
**Solução**: Limpe o cache do navegador (Ctrl+Shift+Del) e recarregue a página.

### Problema: Sidebar não aparece em mobile
**Esperado**: Em telas <768px, o conteúdo ocupa tela inteira. A navegação fica com os botões do cabeçalho.

### Problema: Componentes ainda com estilo antigo
**Solução**: Verifique se `web/styles/main.css` foi corretamente aplicado.

---

## 📚 Estrutura de Arquivos

```
web/
├── index.html              # HTML principal (moderno)
├── styles/
│   └── main.css           # CSS principal (aplicado)
└── scripts/
    ├── main.js            # JS principal (aplicado)
    └── api_client.js      # Cliente API (mantido)
```

---

## 🎓 Notas de Desenvolvimento

- HTML semântico com ARIA labels
- CSS com variáveis CSS (fácil customização)
- JavaScript modular (class-based)
- Sem dependencies externas (vanilla JS)
- Performance otimizada
- Mobile-first approach

---

## ✅ Checklist de Validação

- ✅ Layout sidebar + main content
- ✅ Autenticação funcional
- ✅ Chat com streaming
- ✅ Admin panel com abas
- ✅ Dashboard de status
- ✅ Responsividade completa
- ✅ Paleta roxa/branca
- ✅ Animações suaves
- ✅ Sem templates genéricos
- ✅ Design profissional e elegante

---

**Criado com ❤️ para a ROSITA | v2.0 Modern Frontend**
