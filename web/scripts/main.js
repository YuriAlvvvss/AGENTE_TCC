class RositaApp {
  constructor() {
    this.authView = document.getElementById("auth-view");
    this.appShell = document.getElementById("app-shell");
    this.loginForm = document.getElementById("login-form");
    this.loginUsername = document.getElementById("login-username");
    this.loginPassword = document.getElementById("login-password");
    this.authFeedbackEl = document.getElementById("auth-feedback");
    this.userNameEl = document.getElementById("user-name");
    this.userRoleEl = document.getElementById("user-role");
    this.userAvatarEl = document.getElementById("user-avatar");
    this.accessHintEl = document.getElementById("access-hint");
    this.logoutBtn = document.getElementById("logout-btn");
    this.themeToggleBtn = document.getElementById("theme-toggle-btn");
    this.chatContainer = document.getElementById("chat-container");
    this.modelSelectorWrap = document.querySelector(".assistant-model-selector") || document.querySelector(".model-selector");
    this.userInput = document.getElementById("user-input");
    this.sendBtn = document.getElementById("send-btn");
    this.micBtn = document.getElementById("mic-btn");
    this.clearBtn = document.getElementById("clear-btn");
    this.newChatBtn = document.getElementById("new-chat-btn");
    this.settingsBtn = document.getElementById("settings-btn");
    this.suggestionsEl = document.getElementById("assistant-suggestions");
    this.greetingLine1 = document.getElementById("greeting-line-1");
    this.historyCurrent = document.getElementById("history-current");
    this.historyEmpty = document.getElementById("history-empty");
    this.sidebarToggleBtn = document.getElementById("sidebar-toggle-btn");
    this.sidebarCloseBtn = document.getElementById("sidebar-close-btn");
    this.sidebarBackdrop = document.getElementById("sidebar-backdrop");
    this.headerUserAvatar = document.getElementById("header-user-avatar");
    this.navAdminShortcut = document.getElementById("nav-admin-shortcut");
    this.statusEl = document.getElementById("status") || document.getElementById("status-indicator");
    this.serverInfoEl = document.getElementById("server-info");
    this.systemHostEl = document.getElementById("system-host");
    this.systemCpuEl = document.getElementById("system-cpu");
    this.systemMemoryEl = document.getElementById("system-memory");
    this.systemDiskEl = document.getElementById("system-disk");
    this.systemGpuEl = document.getElementById("system-gpu");
    this.systemVramEl = document.getElementById("system-vram");
    this.modelSelect = document.getElementById("model-select");
    this.modelSelectAdmin = document.getElementById("model-select-admin");
    this.navItems = Array.from(document.querySelectorAll(".nav-item[data-section]"));
    this.sections = Array.from(document.querySelectorAll(".main-content > .section"));
    this.adminTabs = Array.from(document.querySelectorAll(".admin-tab"));
    this.adminPanels = Array.from(document.querySelectorAll(".admin-panel"));
    this.navAdmin = document.getElementById("nav-admin");
    this.charCountEl = document.getElementById("char-count");
    this.statusPillEl = document.getElementById("status-pill");
    this.providerPillEl = document.getElementById("provider-pill");
    this.summaryProviderEl = document.getElementById("summary-provider");
    this.summaryModelEl = document.getElementById("summary-model");
    this.summaryLastUpdateEl = document.getElementById("summary-last-update");
    this.quickActionsEl = document.getElementById("quick-actions"); // legado; substituído por assistant-suggestions
    this.reloadModelsBtn = document.getElementById("reload-models-btn");
    this.unloadModelBtn = document.getElementById("unload-model-btn");
    this.deleteModelBtn = document.getElementById("delete-model-btn");
    this.downloadInput = document.getElementById("model-download-input");
    this.downloadBtn = document.getElementById("download-model-btn");
    this.suggestedModelsEl = document.getElementById("suggested-models");
    this.downloadProgressWrap = document.getElementById("download-progress-wrap");
    this.downloadStatusEl = document.getElementById("download-status");
    this.downloadProgressBar = document.getElementById("download-progress-bar");
    this.loadingOverlay = document.getElementById("loading-overlay");
    this.loadingText = document.getElementById("loading-text");
    this.toastContainer = document.getElementById("toast-container");
    this.scrollBottomBtn = document.getElementById("scroll-bottom-btn");
    this.grudadoNoFim = true;
    this.configFileSelect = document.getElementById("config-file-select");
    this.reloadConfigBtn = document.getElementById("reload-config-btn");
    this.saveConfigBtn = document.getElementById("save-config-btn");
    this.configFileEditor = document.getElementById("config-file-editor");
    this.configFileStatusEl =
      document.getElementById("config-file-status") || document.getElementById("config-status");

    // Configuração do provedor de IA (aba "Provedor de IA").
    this.providerSelect = document.getElementById("provider-select");
    this.providerStatusLine = document.getElementById("provider-status-line");
    this.providerGroups = Array.from(document.querySelectorAll("[data-provider-group]"));
    this.ollamaHostInput = document.getElementById("ollama-host-input");
    this.openrouterKeyInput = document.getElementById("openrouter-key-input");
    this.openrouterKeyHint = document.getElementById("openrouter-key-hint");
    this.openrouterModelInput = document.getElementById("openrouter-model-input");
    this.gatewayUrlInput = document.getElementById("gateway-url-input");
    this.gatewayModelInput = document.getElementById("gateway-model-input");
    this.gatewayKeyInput = document.getElementById("gateway-key-input");
    this.gatewayKeyHint = document.getElementById("gateway-key-hint");
    this.saveProviderBtn = document.getElementById("save-provider-btn");
    this.reloadProviderBtn = document.getElementById("reload-provider-btn");
    this.providerConfigStatusEl = document.getElementById("provider-config-status");

    this.session = {
      authenticated: false,
      role: "guest",
      username: "",
      displayName: "Visitante",
    };
    this.isAwaitingResponse = false;
    this.isDownloadingModel = false;
    this.hasInstalledModels = false;
    this.hasActiveModel = false;
    this.hasShownEmptyModelsTip = false;
    this.modelRefreshTimer = null;
    this.selectedConfigFile = "";
    this.configFilesLoaded = false;
    this.providerConfigLoaded = false;
    this.statusTimer = null;
    this.currentAbort = null;

    // Ícones do botão de envio (avião) e do modo "parar" (quadrado).
    this.sendIconHtml = this.sendBtn ? this.sendBtn.innerHTML : "";
    this.stopIconHtml =
      '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>';

    // Quebras de linha simples viram <br> (mais natural num chat).
    if (window.marked?.setOptions) {
      window.marked.setOptions({ breaks: true });
    }

    this.sincronizarBotaoTema();
    this.bindEvents();
    this.updateControls();
    this.atualizarVisibilidadeProvedor();
    this.initialize();
  }

  bindEvents() {
    this.loginForm?.addEventListener("submit", (event) => {
      event.preventDefault();
      this.login();
    });
    this.logoutBtn?.addEventListener("click", () => this.logout());
    this.themeToggleBtn?.addEventListener("click", () => this.alternarTema());
    this.sendBtn?.addEventListener("click", () => {
      if (this.isAwaitingResponse) {
        this.abortarResposta();
      } else {
        this.enviarMensagem();
      }
    });
    this.clearBtn?.addEventListener("click", () => this.limparChat());
    this.newChatBtn?.addEventListener("click", () => this.limparChat());
    this.settingsBtn?.addEventListener("click", () => {
      if (this.isAdmin()) {
        this.switchSection("admin");
      } else {
        this.notificar("Configurações avançadas disponíveis apenas para administradores.", "info");
      }
    });
    this.sidebarToggleBtn?.addEventListener("click", () => this.abrirSidebarMobile());
    this.sidebarCloseBtn?.addEventListener("click", () => this.fecharSidebarMobile());
    this.sidebarBackdrop?.addEventListener("click", () => this.fecharSidebarMobile());
    this.navAdminShortcut?.addEventListener("click", () => this.switchSection("admin"));
    this.reloadModelsBtn?.addEventListener("click", () => this.carregarModelos());
    this.unloadModelBtn?.addEventListener("click", () => this.descarregarModeloAtual());
    this.deleteModelBtn?.addEventListener("click", () => this.excluirModeloSelecionado());
    this.downloadBtn?.addEventListener("click", () => this.baixarModelo());
    this.modelSelect?.addEventListener("change", () => this.selecionarModelo());
    this.modelSelectAdmin?.addEventListener("change", () => {
      if (this.modelSelect && this.modelSelectAdmin) {
        this.modelSelect.value = this.modelSelectAdmin.value;
      }
      this.selecionarModelo();
    });
    this.navItems.forEach((item) => {
      item.addEventListener("click", () => this.switchSection(item.dataset.section));
    });
    this.adminTabs.forEach((tab) => {
      tab.addEventListener("click", () => this.switchAdminTab(tab.dataset.tab));
    });
    this.userInput?.addEventListener("input", () => {
      this.atualizarContadorCaracteres();
      this.atualizarBotoesInput();
    });
    this.quickActionsEl?.addEventListener("click", (event) => {
      const button = event.target.closest(".quick-chip");
      if (!button || !this.userInput) return;
      this.userInput.value = button.textContent.trim();
      this.atualizarContadorCaracteres();
      this.ajustarAlturaInput();
      this.atualizarBotoesInput();
      this.userInput.focus();
    });
    // Cards de sugestão da tela inicial — preenchem e enviam a pergunta.
    this.suggestionsEl?.addEventListener("click", (event) => {
      const card = event.target.closest(".suggestion-card");
      if (!card || !this.userInput) return;
      const texto = (card.dataset.prompt || card.querySelector(".suggestion-card__title")?.textContent || "").trim();
      if (!texto) return;
      this.userInput.value = texto;
      this.atualizarContadorCaracteres();
      this.ajustarAlturaInput();
      this.atualizarBotoesInput();
      this.enviarMensagem();
    });
    this.configFileSelect?.addEventListener("change", () => this.carregarArquivoConfiguracao());
    this.reloadConfigBtn?.addEventListener("click", () => this.carregarArquivosConfiguracao());
    this.saveConfigBtn?.addEventListener("click", () => this.salvarArquivoConfiguracao());

    this.providerSelect?.addEventListener("change", () => this.atualizarVisibilidadeProvedor());
    this.saveProviderBtn?.addEventListener("click", () => this.salvarConfiguracaoProvedor());
    this.reloadProviderBtn?.addEventListener("click", () => this.carregarConfiguracaoProvedor());

    this.userInput?.addEventListener("keydown", (event) => {
      // Enter envia; Shift+Enter insere quebra de linha.
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        if (!this.isAwaitingResponse && this.hasActiveModel && this.session.authenticated) {
          this.enviarMensagem();
        }
      }
    });
    this.userInput?.addEventListener("input", () => this.ajustarAlturaInput());

    this.chatContainer?.addEventListener("scroll", () => {
      this.grudadoNoFim = this.estaNoFim();
      this.atualizarBotaoScroll();
    });
    this.scrollBottomBtn?.addEventListener("click", () => this.scrollParaFim());

    this.downloadInput?.addEventListener("keypress", (event) => {
      if (event.key === "Enter" && !this.isDownloadingModel && this.isAdmin()) {
        this.baixarModelo();
      }
    });
  }

  async initialize() {
    this.showLoading("Validando sessão...");
    try {
      const payload = await window.rositaApi.obterSessao();
      if (payload?.authenticated) {
        this.applySession(payload);
        await this.onAuthenticated();
      } else {
        this.showLogin("Faça login para continuar.");
      }
    } catch {
      this.showLogin("Não foi possível validar a sessão neste momento.");
    } finally {
      this.hideLoading();
    }
  }

  isAdmin() {
    return this.session.role === "admin";
  }

  setAuthFeedback(message, isError = false) {
    if (!this.authFeedbackEl) return;
    this.authFeedbackEl.textContent = message || "";
    this.authFeedbackEl.classList.toggle("is-error", Boolean(isError));

    // Em caso de erro, balança o card brevemente como feedback visual.
    if (isError) {
      const card = this.authView?.querySelector(".auth-card");
      if (card) {
        card.classList.remove("is-shaking");
        void card.offsetWidth; // força reflow para reiniciar a animação
        card.classList.add("is-shaking");
      }
    }
  }

  /** Controla saudação/cards vazios vs. área de mensagens do assistente. */
  setConversaAtiva(ativa) {
    document
      .getElementById("chat-section")
      ?.classList.toggle("has-conversation", Boolean(ativa));
    this.atualizarHistoricoSidebar();
  }

  /** Personaliza a saudação com o nome do usuário logado. */
  atualizarSaudacao() {
    if (!this.greetingLine1) return;
    const nome = this.session.displayName || this.session.username || "aluno";
    const primeiroNome = nome.split(/\s+/)[0] || "aluno";
    this.greetingLine1.textContent = `Olá, ${primeiroNome}.`;
  }

  /** Atualiza o bloco de histórico lateral conforme existem mensagens. */
  atualizarHistoricoSidebar() {
    const temMensagens = Boolean(this.chatContainer?.children.length);
    if (this.historyCurrent) {
      this.historyCurrent.hidden = !temMensagens;
    }
    if (this.historyEmpty) {
      this.historyEmpty.hidden = temMensagens;
    }
  }

  abrirSidebarMobile() {
    this.appShell?.classList.add("sidebar-open");
  }

  fecharSidebarMobile() {
    this.appShell?.classList.remove("sidebar-open");
  }

  /** Alterna ícone de microfone (vazio) e botão de envio (com texto). */
  atualizarBotoesInput() {
    const hasText = Boolean((this.userInput?.value || "").trim());
    if (this.micBtn) {
      this.micBtn.classList.toggle("hidden", hasText || this.isAwaitingResponse);
    }
    if (this.sendBtn && !this.isAwaitingResponse) {
      this.sendBtn.classList.toggle("hidden", !hasText);
    }
  }

  applySession(payload = {}) {
    const role = payload.role || "guest";
    const authenticated = Boolean(payload.authenticated && ["admin", "user"].includes(role));

    this.session = {
      authenticated,
      role,
      username: payload.username || "",
      displayName: payload.display_name || (role === "admin" ? "Administrador" : role === "user" ? "Usuário" : "Visitante"),
    };

    this.authView?.classList.toggle("hidden", authenticated);
    this.appShell?.classList.toggle("hidden", !authenticated);
    if (this.navAdmin) {
      this.navAdmin.disabled = !this.isAdmin();
      this.navAdmin.classList.toggle("is-disabled", !this.isAdmin());
    }
    if (!this.isAdmin() && this.navAdmin?.classList.contains("nav-item--active")) {
      this.switchSection("chat");
    }

    const roleLabel = this.isAdmin() ? "Administrador" : authenticated ? "Usuário" : "Visitante";
    if (this.userNameEl) {
      this.userNameEl.textContent = this.session.displayName || this.session.username || roleLabel;
    }
    if (this.userRoleEl) {
      this.userRoleEl.textContent = roleLabel;
    }
    if (this.userAvatarEl) {
      const initial = (this.session.username || roleLabel).charAt(0).toUpperCase();
      this.userAvatarEl.textContent = initial || "U";
    }
    if (this.headerUserAvatar) {
      this.headerUserAvatar.textContent = this.userAvatarEl?.textContent || "U";
    }
    if (this.navAdminShortcut) {
      this.navAdminShortcut.classList.toggle("hidden", !this.isAdmin());
    }

    this.atualizarSaudacao();

    if (this.accessHintEl) {
      this.accessHintEl.textContent = this.isAdmin()
        ? "Acesso total: chat, modelos, referências e hardware."
        : authenticated
          ? "Modo usuário: apenas bate-papo com o agente."
          : "Aguardando autenticação...";
    }

    this.updateControls();
  }

  showLogin(message) {
    this.stopStatusPolling();
    this.stopModelPolling();
    this.applySession({ authenticated: false, role: "guest", username: "" });
    this.setAuthFeedback(message || "Faça login para continuar.");
    if (this.statusEl) {
      this.statusEl.textContent = "Login necessário";
    }
    if (this.statusPillEl) {
      this.statusPillEl.classList.remove("status--online");
      this.statusPillEl.classList.add("status--offline");
    }
    if (this.serverInfoEl) {
      this.serverInfoEl.textContent = "Entre como administrador ou usuário para acessar a ROSITA.";
    }
    this.atualizarSistema({});
  }

  async login() {
    const username = (this.loginUsername?.value || "").trim();
    const password = this.loginPassword?.value || "";

    if (!username || !password) {
      this.setAuthFeedback("Informe usuário e senha.", true);
      return;
    }

    this.showLoading("Entrando...");
    try {
      const payload = await window.rositaApi.login(username, password);
      this.loginForm?.reset();
      this.chatContainer.innerHTML = "";
      this.grudadoNoFim = true;
      this.atualizarBotaoScroll();
      this.setAuthFeedback("Login realizado com sucesso.");
      this.applySession(payload);
      await this.onAuthenticated();
    } catch (err) {
      this.setAuthFeedback(err.message || "Falha ao entrar.", true);
    } finally {
      this.hideLoading();
    }
  }

  async logout() {
    this.showLoading("Encerrando sessão...");
    try {
      await window.rositaApi.logout();
    } catch (_) {
    } finally {
      this.chatContainer.innerHTML = "";
      this.grudadoNoFim = true;
      this.atualizarBotaoScroll();
      this.showLogin("Sessão encerrada com sucesso.");
      this.hideLoading();
    }
  }

  async onAuthenticated() {
    await this.verificarStatus();
    this.startStatusPolling();
    if (this.isAdmin()) {
      await this.carregarModelos();
      await this.carregarArquivosConfiguracao(true);
    }
    await this.carregarHistorico();
  }

  /** Carrega e renderiza o histórico persistido do usuário; senão, dá as boas-vindas. */
  async carregarHistorico() {
    let mensagens = [];
    try {
      const payload = await window.rositaApi.obterHistorico();
      mensagens = Array.isArray(payload?.historico) ? payload.historico : [];
    } catch (_) {
      // Falha ao carregar histórico não deve impedir o uso do chat.
    }

    if (!mensagens.length) {
      this.setConversaAtiva(false);
      this.appendWelcomeMessage();
      return;
    }

    this.setConversaAtiva(true);
    this.chatContainer.innerHTML = "";
    this.grudadoNoFim = true;
    for (const msg of mensagens) {
      const tipo = msg.role === "user" ? "user" : "assistant";
      if (tipo === "assistant") {
        const el = this.adicionarMensagem("", "assistant");
        this.renderMarkdown(el, msg.content || "");
      } else {
        this.adicionarMensagem(msg.content || "", "user");
      }
    }
    this.scrollParaFim();
    this.atualizarHistoricoSidebar();
  }

  appendWelcomeMessage() {
    if (!this.chatContainer || this.chatContainer.children.length > 0) return;

    // Admin sem modelo ativo: mostra aviso na área de mensagens com atalho.
    if (this.isAdmin() && !this.hasActiveModel) {
      this.setConversaAtiva(true);
      const content = this.adicionarMensagem(
        "Login de administrador ativo. Nenhum modelo está ativo no momento — ative um para liberar o chat da ROSITA.",
        "assistant"
      );
      const semModelos = !this.hasInstalledModels;
      const cta = document.createElement("button");
      cta.type = "button";
      cta.className = "btn-primary welcome-cta";
      cta.textContent = semModelos ? "Baixar um modelo para começar" : "Ativar um modelo";
      cta.addEventListener("click", () => {
        this.switchSection("admin");
        this.switchAdminTab(semModelos ? "download" : "model-mgmt");
      });
      content.appendChild(cta);
      return;
    }

    // Estado vazio: saudação + cards (sem mensagens no container).
    this.setConversaAtiva(false);
  }

  updateControls() {
    const loggedIn = this.session.authenticated;
    const admin = this.isAdmin();
    const chatDisabled = !loggedIn || this.isAwaitingResponse || this.isDownloadingModel || !this.hasActiveModel;
    const configDisabled = !admin || this.isAwaitingResponse || this.isDownloadingModel;

    if (this.userInput) {
      this.userInput.disabled = chatDisabled;
      this.userInput.placeholder = !loggedIn
        ? "Faça login para usar o chat"
        : this.hasActiveModel
          ? "Pergunte ao assistente da escola..."
          : admin
            ? "Ative um modelo em Administração para conversar"
            : "⏳ Preparando a ROSITA... o chat abre automaticamente";
    }
    if (this.sendBtn) {
      if (this.isAwaitingResponse) {
        // Durante a resposta o botão vira "parar" e fica clicável para abortar.
        this.sendBtn.classList.remove("hidden");
        this.sendBtn.disabled = false;
        this.sendBtn.classList.add("btn-send--stop");
        this.sendBtn.title = "Parar resposta";
        this.sendBtn.setAttribute("aria-label", "Parar resposta");
        if (this.sendBtn.innerHTML !== this.stopIconHtml) {
          this.sendBtn.innerHTML = this.stopIconHtml;
        }
      } else {
        this.sendBtn.disabled = chatDisabled;
        this.sendBtn.classList.remove("btn-send--stop");
        this.sendBtn.title = "Enviar mensagem (Enter)";
        this.sendBtn.setAttribute("aria-label", "Enviar mensagem");
        if (this.sendIconHtml && this.sendBtn.innerHTML !== this.sendIconHtml) {
          this.sendBtn.innerHTML = this.sendIconHtml;
        }
      }
    }
    if (this.modelSelectorWrap) {
      this.modelSelectorWrap.classList.toggle("hidden", !admin);
    }
    if (this.modelSelect) {
      this.modelSelect.disabled = !admin || this.isAwaitingResponse || this.isDownloadingModel || !this.hasInstalledModels;
    }
    if (this.reloadModelsBtn) {
      this.reloadModelsBtn.disabled = !admin || this.isAwaitingResponse || this.isDownloadingModel;
    }
    if (this.unloadModelBtn) {
      this.unloadModelBtn.disabled = !admin || this.isAwaitingResponse || this.isDownloadingModel || !this.hasActiveModel;
    }
    if (this.deleteModelBtn) {
      this.deleteModelBtn.disabled = !admin || this.isAwaitingResponse || this.isDownloadingModel || !this.hasInstalledModels || !this.modelSelect?.value;
    }
    if (this.clearBtn) {
      this.clearBtn.disabled = !loggedIn || this.isAwaitingResponse;
    }
    if (this.downloadInput) {
      this.downloadInput.disabled = !admin || this.isAwaitingResponse || this.isDownloadingModel;
    }
    if (this.downloadBtn) {
      this.downloadBtn.disabled = !admin || this.isAwaitingResponse || this.isDownloadingModel;
    }

    if (this.configFileSelect) {
      this.configFileSelect.disabled = configDisabled || !this.configFilesLoaded;
    }
    if (this.reloadConfigBtn) {
      this.reloadConfigBtn.disabled = configDisabled;
    }
    if (this.configFileEditor) {
      this.configFileEditor.disabled = configDisabled || !this.selectedConfigFile;
    }
    if (this.saveConfigBtn) {
      this.saveConfigBtn.disabled = configDisabled || !this.selectedConfigFile;
    }
    this.atualizarBotoesInput();
  }

  switchSection(sectionName) {
    if (!sectionName) return;
    if (sectionName === "admin" && !this.isAdmin()) return;

    this.fecharSidebarMobile();

    this.navItems.forEach((item) => {
      const active = item.dataset.section === sectionName;
      item.classList.toggle("nav-item--active", active);
    });

    this.sections.forEach((section) => {
      const active = section.id === `${sectionName}-section`;
      section.classList.toggle("section--active", active);
    });
  }

  switchAdminTab(tabName) {
    if (!this.isAdmin() || !tabName) return;

    this.adminTabs.forEach((tab) => {
      const active = tab.dataset.tab === tabName;
      tab.classList.toggle("admin-tab--active", active);
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });

    this.adminPanels.forEach((panel) => {
      const active = panel.id === `panel-${tabName}`;
      panel.classList.toggle("admin-panel--active", active);
      panel.classList.toggle("is-active", active);
    });

    if (tabName === "references" && !this.configFilesLoaded) {
      this.carregarArquivosConfiguracao();
    }
    if (tabName === "provider" && !this.providerConfigLoaded) {
      this.carregarConfiguracaoProvedor();
    }
  }

  atualizarContadorCaracteres() {
    if (!this.charCountEl || !this.userInput) return;
    const len = this.userInput.value.length;
    const max = this.userInput.maxLength || 1000;
    this.charCountEl.textContent = `${len}/${max}`;
  }

  /** Ajusta a altura do campo de texto ao conteúdo (auto-resize, com limite). */
  ajustarAlturaInput() {
    const el = this.userInput;
    if (!el || el.tagName !== "TEXTAREA") return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 140)}px`;
  }

  /** Copia um texto para a área de transferência, com feedback no botão. */
  async copiarTexto(texto, botao) {
    if (!texto) return;
    try {
      await navigator.clipboard.writeText(texto);
    } catch (e) {
      // Fallback para navegadores/contextos sem Clipboard API (ex.: http).
      const ta = document.createElement("textarea");
      ta.value = texto;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
      } catch (_) {}
      ta.remove();
    }
    if (botao) {
      const original = botao.textContent;
      botao.textContent = "Copiado!";
      botao.classList.add("is-copied");
      window.setTimeout(() => {
        botao.textContent = original;
        botao.classList.remove("is-copied");
      }, 1500);
    }
  }

  /** Alterna entre tema claro e escuro e persiste a escolha. */
  alternarTema() {
    const escuroAgora = document.documentElement.classList.toggle("theme-dark");
    try {
      localStorage.setItem("rosita-theme", escuroAgora ? "dark" : "light");
    } catch (e) {}
    this.sincronizarBotaoTema();
  }

  /** Atualiza o rótulo/título do botão conforme o tema atual. */
  sincronizarBotaoTema() {
    if (!this.themeToggleBtn) return;
    const escuro = document.documentElement.classList.contains("theme-dark");
    const rotulo = escuro ? "Mudar para tema claro" : "Mudar para tema escuro";
    this.themeToggleBtn.title = rotulo;
    this.themeToggleBtn.setAttribute("aria-label", rotulo);
  }

  /** True se o chat está rolado até (perto do) fim. */
  estaNoFim() {
    const el = this.chatContainer;
    if (!el) return true;
    return el.scrollHeight - el.scrollTop - el.clientHeight < 40;
  }

  /** Rola o chat até o fim e esconde o botão de "novas mensagens". */
  scrollParaFim() {
    const el = this.chatContainer;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
    this.grudadoNoFim = true;
    this.atualizarBotaoScroll();
  }

  /** Mostra o botão flutuante apenas quando o usuário não está no fim. */
  atualizarBotaoScroll() {
    if (!this.scrollBottomBtn) return;
    this.scrollBottomBtn.classList.toggle("hidden", this.grudadoNoFim);
  }

  startStatusPolling() {
    if (this.statusTimer) return;
    this.statusTimer = window.setInterval(() => this.verificarStatus(), 5000);
  }

  stopStatusPolling() {
    if (!this.statusTimer) return;
    window.clearInterval(this.statusTimer);
    this.statusTimer = null;
  }

  formatPercent(value) {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? `${numeric.toFixed(1)}%` : "--";
  }

  atualizarSistema(system = {}) {
    const cpu = system.cpu || {};
    const memory = system.memoria || {};
    const disk = system.disco || {};
    const gpu = system.gpu || {};

    if (this.systemHostEl) {
      this.systemHostEl.textContent = `${system.hostname || "Host"} • ${system.plataforma || "Sistema"}`;
    }

    if (this.systemCpuEl) {
      this.systemCpuEl.textContent = `${this.formatPercent(cpu.uso_percentual)} • ${cpu.nucleos_logicos || 0} núcleos lógicos`;
    }

    if (this.systemMemoryEl) {
      this.systemMemoryEl.textContent = `${memory.usada || "--"} / ${memory.total || "--"} • ${this.formatPercent(memory.percentual)}`;
    }

    if (this.systemDiskEl) {
      this.systemDiskEl.textContent = `${disk.usado || "--"} / ${disk.total || "--"} • ${this.formatPercent(disk.percentual)}`;
    }

    if (this.systemGpuEl) {
      const gpuUsage = gpu.uso_percentual == null ? "sem telemetria" : this.formatPercent(gpu.uso_percentual);
      this.systemGpuEl.textContent = gpu.disponivel
        ? `${gpu.nome || "GPU"} • ${gpuUsage}`
        : (gpu.mensagem || "GPU não detectada");
    }

    if (this.systemVramEl) {
      const vramPercent = gpu.memoria_percentual == null ? "--" : this.formatPercent(gpu.memoria_percentual);
      this.systemVramEl.textContent = gpu.disponivel
        ? `${gpu.memoria_usada || "--"} / ${gpu.memoria_total || "--"} • ${vramPercent}`
        : "indisponível";
    }
  }

  async verificarStatus() {
    try {
      const payload = await window.rositaApi.obterStatus();

      // Sessão expirou no servidor enquanto a interface ainda estava aberta:
      // volta para a tela de login em vez de deixar o app num estado quebrado.
      if (this.session.authenticated && !payload.authenticated) {
        this.showLogin("Sua sessão expirou. Faça login novamente.");
        return;
      }

      this.hasActiveModel = Boolean(payload.modelo_atual);

      const modelStatus = document.getElementById("model-status");
      if (modelStatus) {
        modelStatus.textContent = payload.modelo_atual || "Nenhum modelo";
      }

      if (payload.authenticated && payload.role && payload.role !== this.session.role) {
        this.applySession({ ...this.session, ...payload });
      }

      if (this.statusEl) {
        this.statusEl.textContent = this.hasActiveModel ? "Online" : "Online • sem modelo ativo";
      }
      if (this.statusPillEl) {
        this.statusPillEl.classList.remove("status--offline");
        this.statusPillEl.classList.add("status--online");
      }

      const providerLabel = payload.provedor_ia || payload.servidor_ia || "--";
      if (this.providerPillEl) {
        this.providerPillEl.textContent = `Provedor: ${providerLabel}`;
      }
      if (this.summaryProviderEl) {
        this.summaryProviderEl.textContent = providerLabel;
      }
      if (this.summaryModelEl) {
        this.summaryModelEl.textContent = payload.modelo_atual || "Nenhum ativo";
      }
      if (this.summaryLastUpdateEl) {
        this.summaryLastUpdateEl.textContent = new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit",
        });
      }

      if (payload.role === "admin") {
        const docs = payload.documentos_contexto || [];
        const contexto = docs.length
          ? `Contexto carregado: ${docs.length} documento(s)`
          : "Contexto documental não encontrado";
        const gpu = payload.sistema?.gpu || {};
        const gpuResumo = gpu.disponivel
          ? `${gpu.nome || "GPU"}${gpu.uso_percentual == null ? "" : ` • ${this.formatPercent(gpu.uso_percentual)}`}`
          : (gpu.nome || "CPU");

        if (this.serverInfoEl) {
          this.serverInfoEl.textContent = payload.modelo_atual
            ? `Administrador • Servidor: ${payload.servidor_ia} • Modelo ativo: ${payload.modelo_atual} • GPU: ${gpuResumo} • ${contexto}`
            : `Administrador • Servidor: ${payload.servidor_ia} • Selecione um modelo para começar • ${contexto}`;
        }
        this.atualizarSistema(payload.sistema || {});
      } else if (payload.role === "user") {
        if (this.serverInfoEl) {
          this.serverInfoEl.textContent = payload.modelo_atual
            ? `Usuário • Chat liberado com o modelo ${payload.modelo_atual}.`
            : "Usuário • O chat ficará disponível quando um administrador ativar um modelo.";
        }
        this.atualizarSistema({});
      } else {
        if (this.serverInfoEl) {
          this.serverInfoEl.textContent = "Entre com suas credenciais para acessar o sistema.";
        }
        this.atualizarSistema({});
      }

      // Reavalia os controles a cada ciclo: assim o chat é liberado
      // automaticamente quando um modelo fica ativo (e bloqueado se sair).
      this.updateControls();
    } catch {
      if (this.statusEl) {
        this.statusEl.textContent = "Offline";
      }
      if (this.statusPillEl) {
        this.statusPillEl.classList.remove("status--online");
        this.statusPillEl.classList.add("status--offline");
      }
      if (this.serverInfoEl) {
        this.serverInfoEl.textContent = "Não foi possível conectar ao backend.";
      }
      this.atualizarSistema({});
    } finally {
      this.updateControls();
    }
  }

  adicionarMensagem(texto, tipo) {
    const wrap = document.createElement("div");
    wrap.className = `message ${tipo}`;

    const body = document.createElement("div");
    body.className = "message-body";

    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = texto;

    const meta = document.createElement("div");
    meta.className = "message-meta";
    const hora = document.createElement("span");
    hora.textContent = new Date().toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    });
    meta.appendChild(hora);

    // Botão de copiar apenas nas respostas da assistente.
    if (tipo === "assistant") {
      const copiar = document.createElement("button");
      copiar.type = "button";
      copiar.className = "copy-btn";
      copiar.title = "Copiar resposta";
      copiar.setAttribute("aria-label", "Copiar resposta");
      copiar.textContent = "Copiar";
      copiar.addEventListener("click", () => this.copiarTexto(content.textContent || "", copiar));
      meta.appendChild(copiar);
    }

    body.appendChild(content);
    body.appendChild(meta);
    wrap.appendChild(body);
    this.chatContainer.appendChild(wrap);
    // Assim que o usuário envia algo, escondemos os chips de boas-vindas.
    if (tipo === "user") {
      this.setConversaAtiva(true);
    }
    // Mensagem do próprio usuário sempre rola; demais só se já estava no fim.
    if (tipo === "user" || this.grudadoNoFim) {
      this.scrollParaFim();
    } else {
      this.atualizarBotaoScroll();
    }
    return content;
  }

  /**
   * Renderiza texto em Markdown dentro de um elemento, sanitizando o HTML.
   * Faz fallback para texto puro se as bibliotecas não estiverem carregadas.
   */
  renderMarkdown(el, texto) {
    if (!el) return;
    if (window.marked?.parse && window.DOMPurify?.sanitize) {
      el.innerHTML = window.DOMPurify.sanitize(window.marked.parse(texto || ""));
      el.classList.add("markdown-body");
    } else {
      el.textContent = texto || "";
    }
  }

  /**
   * Exibe uma notificação flutuante (toast) para mensagens de sistema/admin,
   * mantendo-as separadas da conversa do chat.
   * @param {string} mensagem
   * @param {"info"|"success"|"error"} tipo
   * @param {number} duracao  Tempo até sumir automaticamente (ms). 0 = fixo.
   */
  notificar(mensagem, tipo = "info", duracao = 4500) {
    if (!this.toastContainer || !mensagem) return;

    const toast = document.createElement("div");
    toast.className = `toast toast--${tipo}`;
    toast.setAttribute("role", tipo === "error" ? "alert" : "status");

    const texto = document.createElement("div");
    texto.className = "toast-message";
    texto.textContent = mensagem;

    const fechar = document.createElement("button");
    fechar.type = "button";
    fechar.className = "toast-close";
    fechar.setAttribute("aria-label", "Fechar notificação");
    fechar.textContent = "×";

    const remover = () => {
      if (!toast.isConnected) return;
      toast.classList.add("is-leaving");
      toast.addEventListener("animationend", () => toast.remove(), { once: true });
    };

    fechar.addEventListener("click", remover);
    toast.appendChild(texto);
    toast.appendChild(fechar);
    this.toastContainer.appendChild(toast);

    if (duracao > 0) {
      window.setTimeout(remover, duracao);
    }
  }

  ensureLoadingOverlay() {
    this.loadingOverlay = document.getElementById("loading-overlay");
    this.loadingText = document.getElementById("loading-text");
    if (this.loadingOverlay) return;

    const overlay = document.createElement("div");
    overlay.id = "loading-overlay";
    overlay.className = "loading-overlay";
    overlay.setAttribute("aria-live", "polite");
    overlay.setAttribute("aria-busy", "true");
    overlay.innerHTML =
      '<div class="loading-card"><div class="spinner" aria-hidden="true"></div><p id="loading-text">Carregando...</p></div>';
    document.body.appendChild(overlay);
    this.loadingOverlay = overlay;
    this.loadingText = document.getElementById("loading-text");
  }

  showLoading(text) {
    this.ensureLoadingOverlay();
    const message = text || "Carregando...";
    if (this.loadingText) {
      this.loadingText.textContent = message;
    }
    this.loadingOverlay?.classList.remove("hidden");
  }

  hideLoading() {
    this.ensureLoadingOverlay();
    this.loadingOverlay?.classList.add("hidden");
  }

  renderSuggestedModels(models) {
    if (!this.suggestedModelsEl) return;
    this.suggestedModelsEl.innerHTML = "";
    for (const item of models || []) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "suggested-chip";
      button.title = `${item.description || ""} ${item.size || ""}`.trim();
      button.textContent = `${item.label || item.name} ${item.size ? `• ${item.size}` : ""}`;
      button.addEventListener("click", () => {
        if (!this.downloadInput) return;
        this.downloadInput.value = item.name;
        this.downloadInput.focus();
      });
      this.suggestedModelsEl.appendChild(button);
    }
  }

  setDownloadProgress(percentual, status) {
    if (!this.downloadProgressWrap || !this.downloadProgressBar || !this.downloadStatusEl) return;
    this.downloadProgressWrap.classList.remove("hidden");
    this.downloadProgressBar.style.width = `${Math.max(0, Math.min(100, percentual || 0))}%`;
    this.downloadStatusEl.textContent = status || "Preparando download...";
  }

  startModelPolling() {
    if (this.modelRefreshTimer) return;
    this.modelRefreshTimer = window.setInterval(() => {
      if (this.isDownloadingModel) {
        this.carregarModelos(true);
      }
    }, 3000);
  }

  stopModelPolling() {
    if (!this.modelRefreshTimer) return;
    window.clearInterval(this.modelRefreshTimer);
    this.modelRefreshTimer = null;
  }

  hideDownloadProgress() {
    if (!this.downloadProgressWrap || !this.downloadProgressBar || !this.downloadStatusEl) return;
    this.downloadProgressWrap.classList.add("hidden");
    this.downloadProgressBar.style.width = "0%";
    this.downloadStatusEl.textContent = "Preparando download...";
  }

  setConfigStatus(message) {
    if (this.configFileStatusEl) {
      this.configFileStatusEl.textContent = message;
    }
  }

  async carregarArquivosConfiguracao(silent = false) {
    if (!this.isAdmin()) return;

    try {
      if (!silent) {
        this.setConfigStatus("Carregando referências disponíveis...");
      }

      const payload = await window.rositaApi.listarArquivosConfiguracao();
      const files = payload.files || [];
      this.configFilesLoaded = files.length > 0;
      this.configFileSelect.innerHTML = "";

      if (!files.length) {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = "Nenhum arquivo de referência";
        option.selected = true;
        this.configFileSelect.appendChild(option);
        this.selectedConfigFile = "";
        this.configFileEditor.value = "";
        this.setConfigStatus("Nenhuma referência editável foi encontrada na pasta de dados.");
        this.updateControls();
        return;
      }

      for (const file of files) {
        const option = document.createElement("option");
        option.value = file;
        option.textContent = file;
        this.configFileSelect.appendChild(option);
      }

      const targetFile = files.includes(this.selectedConfigFile) ? this.selectedConfigFile : files[0];
      this.configFileSelect.value = targetFile;
      await this.carregarArquivoConfiguracao(targetFile);
    } catch (err) {
      this.setConfigStatus(`Erro ao carregar referências: ${err.message || String(err)}`);
    } finally {
      this.updateControls();
    }
  }

  async carregarArquivoConfiguracao(filename = null) {
    if (!this.isAdmin()) return;

    const selected = filename || this.configFileSelect?.value || "";
    if (!selected) {
      this.selectedConfigFile = "";
      this.configFileEditor.value = "";
      this.setConfigStatus("Selecione um arquivo para visualizar ou editar.");
      this.updateControls();
      return;
    }

    try {
      this.setConfigStatus(`Carregando ${selected}...`);
      const payload = await window.rositaApi.lerArquivoConfiguracao(selected);
      this.selectedConfigFile = payload.filename;
      this.configFileEditor.value = payload.content || "";
      this.setConfigStatus(`Editando ${payload.filename}. As alterações impactam o contexto da ROSITA.`);
    } catch (err) {
      this.setConfigStatus(`Erro ao abrir referência: ${err.message || String(err)}`);
    } finally {
      this.updateControls();
    }
  }

  async salvarArquivoConfiguracao() {
    if (!this.isAdmin() || !this.selectedConfigFile) return;

    if (
      !window.confirm(
        `Salvar e sobrescrever "${this.selectedConfigFile}"?\n\n` +
          "Isto altera o conhecimento usado pela ROSITA nas respostas. " +
          "Uma cópia de segurança (.bak) do conteúdo anterior será criada no servidor."
      )
    ) {
      return;
    }

    try {
      this.setConfigStatus(`Salvando ${this.selectedConfigFile}...`);
      await window.rositaApi.salvarArquivoConfiguracao(this.selectedConfigFile, this.configFileEditor.value || "");
      this.setConfigStatus(`Referência ${this.selectedConfigFile} salva com sucesso.`);
      await this.verificarStatus();
    } catch (err) {
      this.setConfigStatus(`Erro ao salvar referência: ${err.message || String(err)}`);
    }
  }

  setProviderStatus(message, isError = false) {
    if (!this.providerConfigStatusEl) return;
    this.providerConfigStatusEl.textContent = message || "";
    this.providerConfigStatusEl.classList.toggle("is-error", Boolean(isError));
  }

  atualizarVisibilidadeProvedor() {
    const ativo = this.providerSelect?.value || "ollama";
    this.providerGroups.forEach((group) => {
      const isActive = group.dataset.providerGroup === ativo;
      group.classList.toggle("provider-group--active", isActive);
    });
  }

  preencherProvedorStatusLine(provedores = []) {
    if (!this.providerStatusLine) return;
    if (!Array.isArray(provedores) || !provedores.length) {
      this.providerStatusLine.textContent = "";
      return;
    }
    const partes = provedores.map((p) => {
      const ativo = p.active ? " (ativo)" : "";
      return `${p.label}: ${p.status}${ativo}`;
    });
    this.providerStatusLine.textContent = partes.join(" • ");
  }

  async carregarConfiguracaoProvedor() {
    if (!this.isAdmin()) return;

    this.setProviderStatus("Carregando configuração...");
    try {
      const config = await window.rositaApi.obterCredenciais();

      if (this.providerSelect && config.ai_provider) {
        this.providerSelect.value = config.ai_provider;
      }
      if (this.ollamaHostInput) this.ollamaHostInput.value = config.ollama_host || "";
      if (this.openrouterModelInput) this.openrouterModelInput.value = config.openrouter_model || "";
      if (this.gatewayUrlInput) this.gatewayUrlInput.value = config.gateway_url || "";
      if (this.gatewayModelInput) this.gatewayModelInput.value = config.gateway_model || "";

      // As API keys nunca voltam do servidor; mostramos apenas se já estão configuradas.
      if (this.gatewayKeyInput) {
        this.gatewayKeyInput.value = "";
        this.gatewayKeyInput.placeholder = config.gateway_api_key_set
          ? "•••••••• (configurada — deixe em branco para manter)"
          : "Bearer token, se o gateway exigir";
      }
      if (this.gatewayKeyHint) {
        this.gatewayKeyHint.textContent = config.gateway_api_key_set
          ? "Uma chave já está salva. Preencha apenas para substituí-la."
          : "Enviada como Authorization: Bearer. Deixe em branco se o gateway for aberto.";
      }
      if (this.openrouterKeyInput) {
        this.openrouterKeyInput.value = "";
        this.openrouterKeyInput.placeholder = config.openrouter_api_key_set
          ? "•••••••• (configurada — deixe em branco para manter)"
          : "sk-or-...";
      }
      if (this.openrouterKeyHint) {
        this.openrouterKeyHint.textContent = config.openrouter_api_key_set
          ? "Uma chave já está salva. Preencha apenas se quiser substituí-la."
          : "A chave é gravada apenas no servidor e nunca é devolvida ao navegador.";
      }

      this.atualizarVisibilidadeProvedor();
      this.preencherProvedorStatusLine(config.provedores);
      this.providerConfigLoaded = true;
      this.setProviderStatus("Configuração carregada.");
    } catch (err) {
      this.setProviderStatus(`Erro ao carregar configuração: ${err.message || String(err)}`, true);
    }
  }

  async salvarConfiguracaoProvedor() {
    if (!this.isAdmin()) return;

    const provedor = this.providerSelect?.value || "ollama";
    const payload = {
      ai_provider: provedor,
      ollama_host: (this.ollamaHostInput?.value || "").trim(),
      openrouter_model: (this.openrouterModelInput?.value || "").trim(),
      gateway_url: (this.gatewayUrlInput?.value || "").trim(),
      gateway_model: (this.gatewayModelInput?.value || "").trim(),
    };

    // Só envia as API keys se o usuário digitou algo (evita apagar a existente).
    const apiKey = (this.openrouterKeyInput?.value || "").trim();
    if (apiKey) payload.openrouter_api_key = apiKey;
    const gatewayKey = (this.gatewayKeyInput?.value || "").trim();
    if (gatewayKey) payload.gateway_api_key = gatewayKey;

    // Validação básica no cliente para feedback imediato.
    if (provedor === "openrouter") {
      const semChaveSalva = (this.openrouterKeyInput?.placeholder || "").startsWith("sk-or-");
      if (!apiKey && semChaveSalva) {
        this.setProviderStatus("Informe a API Key do Open Router para usar esse provedor.", true);
        return;
      }
      if (!payload.openrouter_model) {
        this.setProviderStatus("Informe o modelo do Open Router (ex: openai/gpt-4o-mini).", true);
        return;
      }
    }
    if (provedor === "gateway") {
      if (!payload.gateway_url) {
        this.setProviderStatus("Informe a URL base do gateway.", true);
        return;
      }
      if (!payload.gateway_model) {
        this.setProviderStatus("Informe o modelo do gateway.", true);
        return;
      }
    }

    if (this.saveProviderBtn) this.saveProviderBtn.disabled = true;
    this.showLoading("Aplicando configuração do provedor...");
    try {
      const resposta = await window.rositaApi.salvarCredenciais(payload);
      this.preencherProvedorStatusLine(resposta.provedores);
      this.setProviderStatus(resposta.aviso
        ? `${resposta.mensagem} Aviso: ${resposta.aviso}`
        : (resposta.mensagem || "Configuração salva."));
      this.notificar(`Provedor de IA atualizado para "${provedor}".`, "success");
      // Recarrega modelos e status para refletir o novo provedor/modelo.
      this.providerConfigLoaded = false;
      await this.carregarConfiguracaoProvedor();
      await this.carregarModelos(true);
      await this.verificarStatus();
    } catch (err) {
      this.setProviderStatus(`Erro ao salvar: ${err.message || String(err)}`, true);
    } finally {
      if (this.saveProviderBtn) this.saveProviderBtn.disabled = false;
      this.hideLoading();
    }
  }

  async carregarModelos(silent = false) {
    if (!this.isAdmin()) return;

    if (!silent) {
      this.showLoading("Buscando modelos instalados no Ollama...");
    }
    try {
      const payload = await window.rositaApi.listarModelos();
      const models = payload.models || [];
      const current = payload.current_model || "";

      this.renderSuggestedModels(payload.recommended_models || []);
      const selects = [this.modelSelect, this.modelSelectAdmin].filter(Boolean);
      selects.forEach((select) => {
        select.innerHTML = "";
      });
      this.hasInstalledModels = models.length > 0;
      this.hasActiveModel = Boolean(current);

      const fillSelect = (select) => {
        if (!models.length) {
          const option = document.createElement("option");
          option.value = "";
          option.textContent = "Nenhum modelo instalado";
          option.selected = true;
          select.appendChild(option);
          return;
        }

        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = current ? "Modelo ativo" : "Selecione um modelo instalado";
        placeholder.selected = !current;
        select.appendChild(placeholder);

        for (const model of models) {
          const option = document.createElement("option");
          option.value = model;
          option.textContent = model;
          if (model === current) option.selected = true;
          select.appendChild(option);
        }
      };

      selects.forEach(fillSelect);

      const modelDisplay = document.querySelector("#current-model-display .model-name");
      if (modelDisplay) {
        modelDisplay.textContent = current || "Nenhum modelo selecionado";
      }

      const modelStatus = document.getElementById("model-status");
      if (modelStatus) {
        modelStatus.textContent = current || "Nenhum modelo";
      }

      if (!models.length && !this.hasShownEmptyModelsTip) {
        this.notificar(
          "Nenhum modelo está instalado ainda. Escolha uma sugestão ou informe um nome de modelo para começar.",
          "info",
          7000
        );
        this.hasShownEmptyModelsTip = true;
      }

      if (payload.downloading) {
        this.isDownloadingModel = true;
        this.setDownloadProgress(
          payload.download_percent || 0,
          `${payload.download_model || "Modelo"} • ${payload.download_status || "Baixando..."}`
        );
        this.startModelPolling();
      } else {
        this.isDownloadingModel = false;
        this.stopModelPolling();
        this.hideDownloadProgress();
      }

      this.updateControls();
      await this.verificarStatus();
    } catch (err) {
      this.notificar(`Erro ao carregar modelos: ${err.message || String(err)}`, "error");
    } finally {
      if (!silent) {
        this.hideLoading();
      }
    }
  }

  async selecionarModelo() {
    if (!this.isAdmin()) return;

    const model = this.modelSelect.value;
    if (!model) return;

    this.showLoading(`Trocando modelo para ${model}...`);
    this.isAwaitingResponse = true;
    this.updateControls();
    try {
      await window.rositaApi.selecionarModelo(model);
      this.hasActiveModel = true;
      this.notificar(`Modelo ativo alterado para: ${model}`, "success");
      await this.verificarStatus();
    } catch (err) {
      this.notificar(`Erro ao trocar modelo: ${err.message || String(err)}`, "error");
      await this.carregarModelos();
    } finally {
      this.isAwaitingResponse = false;
      this.updateControls();
      this.hideLoading();
    }
  }

  async descarregarModeloAtual() {
    if (!this.isAdmin()) return;

    const model = (this.modelSelect.value || "").trim();
    if (!model || !this.hasActiveModel) return;

    if (!window.confirm(`Descarregar o modelo ativo ${model}?`)) {
      return;
    }

    this.showLoading(`Descarregando ${model}...`);
    this.isAwaitingResponse = true;
    this.updateControls();
    try {
      await window.rositaApi.descarregarModeloAtual();
      this.hasActiveModel = false;
      this.notificar(`Modelo descarregado da memória: ${model}.`, "success");
      await this.carregarModelos();
    } catch (err) {
      this.notificar(`Erro ao descarregar modelo: ${err.message || String(err)}`, "error");
    } finally {
      this.isAwaitingResponse = false;
      this.updateControls();
      this.hideLoading();
    }
  }

  async excluirModeloSelecionado() {
    if (!this.isAdmin()) return;

    const model = (this.modelSelect.value || "").trim();
    if (!model) return;

    if (!window.confirm(`Excluir o modelo ${model}? Essa ação remove os arquivos baixados do Ollama.`)) {
      return;
    }

    this.showLoading(`Excluindo ${model}...`);
    this.isAwaitingResponse = true;
    this.updateControls();
    try {
      const payload = await window.rositaApi.excluirModelo(model);
      this.hasActiveModel = Boolean(payload.current_model);
      this.notificar(`Modelo removido com sucesso: ${model}.`, "success");
      await this.carregarModelos();
    } catch (err) {
      this.notificar(`Erro ao excluir modelo: ${err.message || String(err)}`, "error");
    } finally {
      this.isAwaitingResponse = false;
      this.updateControls();
      this.hideLoading();
    }
  }

  async baixarModelo() {
    if (!this.isAdmin()) return;

    const model = (this.downloadInput.value || "").trim();
    if (!model || this.isDownloadingModel) return;

    this.isDownloadingModel = true;
    this.updateControls();
    this.setDownloadProgress(0, `Iniciando download de ${model}...`);
    this.notificar(
      `Baixando o modelo ${model}. Isso pode levar alguns minutos na primeira vez.`,
      "info",
      6000
    );

    try {
      await window.rositaApi.baixarModelo(model, (evento) => {
        if (!evento || typeof evento !== "object") return;
        const percentual = Number(evento.percentual || 0);
        const status = evento.status || "Baixando...";
        this.setDownloadProgress(percentual, `${model} • ${status}${percentual ? ` (${percentual}%)` : ""}`);
      });

      this.setDownloadProgress(100, `Modelo ${model} baixado com sucesso.`);
      this.notificar(
        `Modelo instalado com sucesso: ${model}. Agora selecione esse modelo na lista para ativá-lo.`,
        "success",
        6000
      );
      await this.carregarModelos();
    } catch (err) {
      const errorMessage = err.message || String(err);
      this.notificar(`Erro ao baixar modelo: ${errorMessage}`, "error");
      this.setDownloadProgress(0, `Falha ao baixar ${model}: ${errorMessage}`);
    } finally {
      this.isDownloadingModel = false;
      this.stopModelPolling();
      this.updateControls();
    }
  }

  async enviarMensagem() {
    const texto = (this.userInput.value || "").trim();
    if (!this.session.authenticated || !texto || this.isAwaitingResponse || !this.hasActiveModel) return;

    this.isAwaitingResponse = true;
    this.updateControls();

    this.adicionarMensagem(texto, "user");
    this.userInput.value = "";
    this.atualizarContadorCaracteres();
    this.ajustarAlturaInput();
    const content = this.adicionarMensagem("", "assistant");
    // Mostra o indicador "digitando" enquanto o primeiro chunk não chega.
    content.innerHTML =
      '<span class="typing-indicator"><span></span><span></span><span></span></span>';

    this.currentAbort = new AbortController();
    let resposta = "";
    let primeiroChunk = true;
    try {
      await window.rositaApi.enviarMensagem(
        texto,
        (chunk) => {
          if (primeiroChunk) {
            // Remove o indicador ao receber o início da resposta.
            content.textContent = "";
            primeiroChunk = false;
          }
          resposta += chunk;
          // Durante o streaming mostra texto puro (mais fluido); o Markdown
          // é renderizado ao final, quando a resposta está completa.
          content.textContent = resposta;
          // Acompanha o fim só se o usuário não rolou para cima para reler.
          if (this.grudadoNoFim) {
            this.scrollParaFim();
          } else {
            this.atualizarBotaoScroll();
          }
        },
        this.currentAbort.signal
      );
      this.renderMarkdown(content, resposta);
    } catch (err) {
      if (err?.name === "AbortError") {
        const aviso = "⏹ Resposta interrompida.";
        this.renderMarkdown(content, resposta ? `${resposta}\n\n${aviso}` : aviso);
      } else {
        content.textContent = `Erro: ${err.message || String(err)}`;
      }
    } finally {
      this.currentAbort = null;
      this.isAwaitingResponse = false;
      this.updateControls();
    }
  }

  abortarResposta() {
    if (this.currentAbort) {
      this.currentAbort.abort();
    }
  }

  async limparChat() {
    if (!this.session.authenticated) return;

    try {
      await window.rositaApi.limparHistorico();
      this.chatContainer.innerHTML = "";
      this.grudadoNoFim = true;
      this.atualizarBotaoScroll();
      this.setConversaAtiva(false);
      this.appendWelcomeMessage();
    } catch (err) {
      this.notificar(`Erro ao limpar histórico: ${err.message || String(err)}`, "error");
    }
  }
}

document.addEventListener("DOMContentLoaded", () => new RositaApp());
