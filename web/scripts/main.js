class RositaApp {
  constructor() {
    this.authView = document.getElementById("admin-login-modal");
    this.adminLoginBackdrop = document.getElementById("admin-login-backdrop");
    this.adminLoginBtn = document.getElementById("admin-login-btn");
    this.adminLoginCancel = document.getElementById("admin-login-cancel");
    this.appShell = document.getElementById("app-shell");
    this.sidebarToggle = document.getElementById("sidebar-toggle");
    this.sidebarCollapsedKey = "sidebarCollapsed";
    this.loginForm = document.getElementById("login-form");
    this.loginUsername = document.getElementById("login-username");
    this.loginPassword = document.getElementById("login-password");
    this.authFeedbackEl = document.getElementById("auth-feedback");
    this.userNameEl = document.getElementById("user-name");
    this.userRoleEl = document.getElementById("user-role");
    this.userAvatarEl = document.getElementById("user-avatar");
    this.accessHintEl = document.getElementById("access-hint");
    this.logoutBtn = document.getElementById("logout-btn");
    this.chatContainer = document.getElementById("chat-container");
    this.chatEmptyState = document.getElementById("chat-empty-state");
    this.chatSection = document.getElementById("chat-section");
    this.modelSelectorWrap = document.querySelector(".model-selector");
    this.userInput = document.getElementById("user-input");
    this.sendBtn = document.getElementById("send-btn");
    this.clearBtn = document.getElementById("clear-btn");
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
    this.navStatus = document.getElementById("nav-status");
    this.sideSummaryCard = document.getElementById("side-summary-card");
    this.charCountEl = document.getElementById("char-count");
    this.statusPillEl = document.getElementById("status-pill");
    this.providerPillEl = document.getElementById("provider-pill");
    this.summaryProviderEl = document.getElementById("summary-provider");
    this.summaryModelEl = document.getElementById("summary-model");
    this.summaryLastUpdateEl = document.getElementById("summary-last-update");
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
    this.tokenStatsEl = document.getElementById("token-stats");
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
    this.currentTokens = [];
    this.hasShownEmptyModelsTip = false;
    this.modelRefreshTimer = null;
    this.selectedConfigFile = "";
    this.configFilesLoaded = false;
    this.providerConfigLoaded = false;
    this.statusTimer = null;

    this.bindEvents();
    this.initializeSidebar();
    this.atualizarContadorCaracteres();
    this.updateControls();
    this.atualizarVisibilidadeProvedor();
    this.initialize();
    // Pause status polling when the tab is not visible to save requests
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        this.stopStatusPolling();
      } else {
        // resume only if admin (status polling is useful for admin view)
        if (this.session && this.session.role === "admin") {
          this.startStatusPolling();
        }
      }
    });
  }

  bindEvents() {
    this.loginForm?.addEventListener("submit", (event) => {
      event.preventDefault();
      this.login();
    });
    this.adminLoginBtn?.addEventListener("click", () => this.showAdminLoginModal());
    this.adminLoginCancel?.addEventListener("click", () => this.hideAdminLoginModal());
    this.adminLoginBackdrop?.addEventListener("click", () => this.hideAdminLoginModal());
    this.logoutBtn?.addEventListener("click", () => this.logout());
    this.sidebarToggle?.addEventListener("click", () => this.toggleSidebar());
    this.sendBtn?.addEventListener("click", () => this.enviarMensagem());
    this.clearBtn?.addEventListener("click", () => this.limparChat());
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
    this.userInput?.addEventListener("input", () => this.atualizarContadorCaracteres());
    this.configFileSelect?.addEventListener("change", () => this.carregarArquivoConfiguracao());
    this.reloadConfigBtn?.addEventListener("click", () => this.carregarArquivosConfiguracao());
    this.saveConfigBtn?.addEventListener("click", () => this.salvarArquivoConfiguracao());

    this.providerSelect?.addEventListener("change", () => this.atualizarVisibilidadeProvedor());
    this.saveProviderBtn?.addEventListener("click", () => this.salvarConfiguracaoProvedor());
    this.reloadProviderBtn?.addEventListener("click", () => this.carregarConfiguracaoProvedor());

    this.userInput?.addEventListener("keypress", (event) => {
      if (event.key === "Enter" && !this.isAwaitingResponse && this.hasActiveModel) {
        this.enviarMensagem();
      }
    });

    this.downloadInput?.addEventListener("keypress", (event) => {
      if (event.key === "Enter" && !this.isDownloadingModel && this.isAdmin()) {
        this.baixarModelo();
      }
    });
  }

  async initialize() {
    this.applySession({ authenticated: false, role: "guest" });
    this.showLoading("Carregando...");
    try {
      const payload = await window.rositaApi.obterSessao();
      if (payload?.authenticated && payload.role === "admin") {
        this.applySession(payload);
        await this.onAppReady(true);
      } else {
        if (payload?.authenticated && payload.role !== "admin") {
          await window.rositaApi.logout().catch(() => {});
        }
        await this.onAppReady(false);
      }
    } catch {
      await this.onAppReady(false);
    } finally {
      this.hideLoading();
    }
  }

  isGuest() {
    return !this.isAdmin();
  }

  initializeSidebar() {
    let stored = null;
    try {
      stored = window.localStorage.getItem(this.sidebarCollapsedKey);
    } catch (error) {
      console.warn("Não foi possível ler a preferência da sidebar.", error);
    }
    if (stored === "true") {
      this.setSidebarCollapsed(true);
    }
  }

  setSidebarCollapsed(isCollapsed) {
    this.appShell?.classList.toggle("sidebar-collapsed", Boolean(isCollapsed));
    if (this.sidebarToggle) {
      this.sidebarToggle.setAttribute("aria-expanded", String(!isCollapsed));
      const label = isCollapsed ? "Expandir barra lateral" : "Recolher barra lateral";
      this.sidebarToggle.setAttribute("aria-label", label);
      this.sidebarToggle.title = label;
    }
    try {
      window.localStorage.setItem(this.sidebarCollapsedKey, String(Boolean(isCollapsed)));
    } catch (error) {
      console.warn("Não foi possível salvar a preferência da sidebar.", error);
    }
  }

  toggleSidebar() {
    const isCollapsed = Boolean(this.appShell?.classList.contains("sidebar-collapsed"));
    this.setSidebarCollapsed(!isCollapsed);
  }

  showAdminLoginModal() {
    this.authView?.classList.remove("hidden");
    this.setAuthFeedback("");
    this.loginUsername?.focus();
  }

  hideAdminLoginModal() {
    this.authView?.classList.add("hidden");
    this.loginForm?.reset();
    this.setAuthFeedback("");
  }

  isAdmin() {
    return this.session.role === "admin";
  }

  setAuthFeedback(message, isError = false) {
    if (!this.authFeedbackEl) return;
    this.authFeedbackEl.textContent = message || "";
    this.authFeedbackEl.classList.toggle("is-error", Boolean(isError));
  }

  applySession(payload = {}) {
    const role = payload.role === "admin" ? "admin" : "guest";
    const authenticated = role === "admin";

    this.session = {
      authenticated,
      role,
      username: authenticated ? payload.username || "" : "",
      displayName: authenticated ? payload.display_name || "Administrador" : "Visitante",
    };

    this.navStatus?.classList.toggle("hidden", !this.isAdmin());
    this.sideSummaryCard?.classList.toggle("hidden", !this.isAdmin());
    this.adminLoginBtn?.classList.toggle("hidden", this.isAdmin());
    this.logoutBtn?.classList.toggle("hidden", !this.isAdmin());

    if (!this.isAdmin() && (this.navAdmin?.classList.contains("nav-item--active") || this.navStatus?.classList.contains("nav-item--active"))) {
      this.switchSection("chat", { force: true });
    }

    const roleLabel = this.isAdmin() ? "Administrador" : "Visitante";
    if (this.userNameEl) {
      this.userNameEl.textContent = this.session.displayName || roleLabel;
    }
    if (this.userRoleEl) {
      this.userRoleEl.textContent = roleLabel;
    }
    if (this.userAvatarEl) {
      const initial = (this.session.username || roleLabel).charAt(0).toUpperCase();
      this.userAvatarEl.textContent = initial || "V";
    }

    if (this.accessHintEl) {
      this.accessHintEl.textContent = this.isAdmin()
        ? "Acesso total: modelos, referências e hardware."
        : "Chat liberado. Entre como administrador para configurar o sistema.";
    }

    this.updateControls();
  }

  async onAppReady(isAdminSession = false) {
    await this.verificarStatus();
    this.startStatusPolling();
    if (isAdminSession) {
      await this.carregarModelos();
      await this.carregarArquivosConfiguracao(true);
    }
    this.appendWelcomeMessage();
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
      this.setAuthFeedback("Login realizado com sucesso.");
      this.hideAdminLoginModal();
      this.applySession(payload);
      await this.onAppReady(true);
      this.switchSection("admin", { force: true });
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
      // Ensure we stop any background polling on logout
      try {
        this.stopStatusPolling();
      } catch (_) {}
      this.hideAdminLoginModal();
      this.applySession({ authenticated: false, role: "guest" });
      this.switchSection("chat", { force: true });
      await this.verificarStatus();
      this.hideLoading();
    }
  }

  appendWelcomeMessage() {
    this.updateChatEmptyState();
  }

  updateChatEmptyState() {
    const isEmpty = !this.chatContainer || this.chatContainer.children.length === 0;
    this.chatSection?.classList.toggle("chat-empty", isEmpty);
    this.chatSection?.classList.toggle("chat-active", !isEmpty);
    this.chatContainer?.classList.toggle("chat-container--has-messages", !isEmpty);
  }

  updateControls() {
    const admin = this.isAdmin();
    const chatDisabled = this.isAwaitingResponse || this.isDownloadingModel || !this.hasActiveModel;
    const configDisabled = !admin || this.isAwaitingResponse || this.isDownloadingModel;

    if (this.userInput) {
      this.userInput.disabled = chatDisabled;
      this.userInput.placeholder = this.hasActiveModel
        ? "Pergunte ao assistente da escola..."
        : "Aguarde um modelo ativo para conversar";
    }
    if (this.sendBtn) {
      this.sendBtn.disabled = chatDisabled;
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
      this.clearBtn.disabled = this.isAwaitingResponse;
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
  }

  switchSection(sectionName, options = {}) {
    if (!sectionName) return;
    if (!options.force && (sectionName === "admin" || sectionName === "status") && !this.isAdmin()) {
      this.showAdminLoginModal();
      return;
    }

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
      this.hasActiveModel = Boolean(payload.modelo_atual);

      const modelStatus = document.getElementById("model-status");
      if (modelStatus) {
        modelStatus.textContent = payload.modelo_atual || "Nenhum modelo";
      }

      if (payload.authenticated && payload.role && payload.role !== this.session.role) {
        this.applySession({ ...this.session, ...payload });
      }

      if (this.statusEl) {
        this.statusEl.textContent = this.hasActiveModel ? "Online" : "Online • sem modelo";
      }
      if (this.statusPillEl) {
        this.statusPillEl.classList.remove("status--offline");
        this.statusPillEl.classList.add("status--online");
      }
      const statusIndicator = document.getElementById("status-indicator");
      if (statusIndicator) {
        statusIndicator.classList.remove("status-indicator--loading");
        statusIndicator.style.background = "var(--color-online)";
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
      } else {
        if (this.serverInfoEl) {
          this.serverInfoEl.textContent = payload.modelo_atual
            ? `Assistente disponível com o modelo ${payload.modelo_atual}.`
            : "O chat ficará disponível quando um administrador ativar um modelo.";
        }
        this.atualizarSistema({});
      }
    } catch {
      if (this.statusEl) {
        this.statusEl.textContent = "Offline";
      }
      if (this.statusPillEl) {
        this.statusPillEl.classList.remove("status--online");
        this.statusPillEl.classList.add("status--offline");
      }
      const statusIndicator = document.getElementById("status-indicator");
      if (statusIndicator) {
        statusIndicator.classList.remove("status-indicator--loading");
        statusIndicator.style.background = "var(--color-danger)";
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
    meta.textContent = new Date().toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    });

    body.appendChild(content);
    body.appendChild(meta);
    wrap.appendChild(body);
    this.chatContainer.appendChild(wrap);
    this.updateChatEmptyState();
    this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    return content;
  }

  tokenizeChunk(chunk) {
    return chunk.match(/\S+/g) || [];
  }

  atualizarTokenStats() {
    if (!this.tokenStatsEl) return;
    const total = this.currentTokens.length;
    const ultimos = this.currentTokens.slice(-12).join(" | ");
    if (this.tokenStatsEl) {
      this.tokenStatsEl.textContent = `Tokens: ${total}${ultimos ? ` | ${ultimos}` : ""}`;
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
      this.adicionarMensagem(
        `Provedor de IA atualizado para "${provedor}".`,
        "assistant"
      );
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
        this.adicionarMensagem(
          "Nenhum modelo está instalado ainda. Escolha uma sugestão acima ou informe um nome de modelo para começar.",
          "assistant"
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
      this.adicionarMensagem(`Erro ao carregar modelos: ${err.message || String(err)}`, "assistant");
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
      this.adicionarMensagem(`Modelo ativo alterado para: ${model}`, "assistant");
      await this.verificarStatus();
    } catch (err) {
      this.adicionarMensagem(`Erro ao trocar modelo: ${err.message || String(err)}`, "assistant");
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
      this.adicionarMensagem(`Modelo descarregado da memória: ${model}.`, "assistant");
      await this.carregarModelos();
    } catch (err) {
      this.adicionarMensagem(`Erro ao descarregar modelo: ${err.message || String(err)}`, "assistant");
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
      this.adicionarMensagem(`Modelo removido com sucesso: ${model}.`, "assistant");
      await this.carregarModelos();
    } catch (err) {
      this.adicionarMensagem(`Erro ao excluir modelo: ${err.message || String(err)}`, "assistant");
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
    this.adicionarMensagem(
      `Baixando o modelo ${model}. Isso pode levar alguns minutos na primeira vez.`,
      "assistant"
    );

    try {
      await window.rositaApi.baixarModelo(model, (evento) => {
        if (!evento || typeof evento !== "object") return;
        const percentual = Number(evento.percentual || 0);
        const status = evento.status || "Baixando...";
        this.setDownloadProgress(percentual, `${model} • ${status}${percentual ? ` (${percentual}%)` : ""}`);
      });

      this.setDownloadProgress(100, `Modelo ${model} baixado com sucesso.`);
      this.adicionarMensagem(
        `Modelo instalado com sucesso: ${model}. Agora selecione esse modelo na lista para ativá-lo.`,
        "assistant"
      );
      await this.carregarModelos();
    } catch (err) {
      const errorMessage = err.message || String(err);
      this.adicionarMensagem(`Erro ao baixar modelo: ${errorMessage}`, "assistant");
      this.setDownloadProgress(0, `Falha ao baixar ${model}: ${errorMessage}`);
    } finally {
      this.isDownloadingModel = false;
      this.stopModelPolling();
      this.updateControls();
    }
  }

  async enviarMensagem() {
    const texto = (this.userInput.value || "").trim();
    if (!texto || this.isAwaitingResponse || !this.hasActiveModel) return;

    this.currentTokens = [];
    this.atualizarTokenStats();
    this.isAwaitingResponse = true;
    this.updateControls();

    this.adicionarMensagem(texto, "user");
    this.userInput.value = "";
    const content = this.adicionarMensagem("", "assistant");

    try {
      await window.rositaApi.enviarMensagem(texto, (chunk) => {
        const novosTokens = this.tokenizeChunk(chunk);
        this.currentTokens.push(...novosTokens);
        this.atualizarTokenStats();
        content.textContent += chunk;
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
      });
    } catch (err) {
      content.textContent = `Erro: ${err.message || String(err)}`;
    } finally {
      this.isAwaitingResponse = false;
      this.updateControls();
    }
  }

  async limparChat() {
    try {
      await window.rositaApi.limparHistorico();
      this.chatContainer.innerHTML = "";
      this.updateChatEmptyState();
    } catch (err) {
      this.adicionarMensagem(`Erro ao limpar histórico: ${err.message || String(err)}`, "assistant");
    }
  }
}

document.addEventListener("DOMContentLoaded", () => new RositaApp());
