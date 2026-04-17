class RositaApp {
  constructor() {
    this.authView = document.getElementById("auth-view");
    this.appShell = document.getElementById("app-shell");
    this.loginForm = document.getElementById("login-form");
    this.loginUsername = document.getElementById("login-username");
    this.loginPassword = document.getElementById("login-password");
    this.authFeedbackEl = document.getElementById("auth-feedback");
    this.userBadge = document.getElementById("user-badge");
    this.accessHintEl = document.getElementById("access-hint");
    this.logoutBtn = document.getElementById("logout-btn");
    this.adminTelemetry = document.getElementById("admin-telemetry");
    this.adminSettings = document.getElementById("admin-settings");

    this.chatContainer = document.getElementById("chat-container");
    this.userInput = document.getElementById("user-input");
    this.sendBtn = document.getElementById("send-btn");
    this.clearBtn = document.getElementById("clear-btn");
    this.statusEl = document.getElementById("status");
    this.serverInfoEl = document.getElementById("server-info");
    this.systemHostEl = document.getElementById("system-host");
    this.systemCpuEl = document.getElementById("system-cpu");
    this.systemMemoryEl = document.getElementById("system-memory");
    this.systemDiskEl = document.getElementById("system-disk");
    this.systemGpuEl = document.getElementById("system-gpu");
    this.systemVramEl = document.getElementById("system-vram");
    this.modelSelect = document.getElementById("model-select");
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
    this.configFileStatusEl = document.getElementById("config-file-status");
    this.settingsTabs = Array.from(document.querySelectorAll(".settings-tab"));
    this.settingsPanels = Array.from(document.querySelectorAll(".settings-panel"));

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
    this.statusTimer = null;

    this.bindEvents();
    this.updateControls();
    this.initialize();
  }

  bindEvents() {
    this.loginForm?.addEventListener("submit", (event) => {
      event.preventDefault();
      this.login();
    });
    this.logoutBtn?.addEventListener("click", () => this.logout());
    this.sendBtn?.addEventListener("click", () => this.enviarMensagem());
    this.clearBtn?.addEventListener("click", () => this.limparChat());
    this.reloadModelsBtn?.addEventListener("click", () => this.carregarModelos());
    this.unloadModelBtn?.addEventListener("click", () => this.descarregarModeloAtual());
    this.deleteModelBtn?.addEventListener("click", () => this.excluirModeloSelecionado());
    this.downloadBtn?.addEventListener("click", () => this.baixarModelo());
    this.modelSelect?.addEventListener("change", () => this.selecionarModelo());
    this.settingsTabs.forEach((tab) => {
      tab.addEventListener("click", () => this.switchSettingsTab(tab.dataset.tab));
    });
    this.configFileSelect?.addEventListener("change", () => this.carregarArquivoConfiguracao());
    this.reloadConfigBtn?.addEventListener("click", () => this.carregarArquivosConfiguracao());
    this.saveConfigBtn?.addEventListener("click", () => this.salvarArquivoConfiguracao());

    this.userInput?.addEventListener("keypress", (event) => {
      if (event.key === "Enter" && !this.isAwaitingResponse && this.hasActiveModel && this.session.authenticated) {
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
    this.adminTelemetry?.classList.toggle("hidden", !this.isAdmin());
    this.adminSettings?.classList.toggle("hidden", !this.isAdmin());

    if (this.userBadge) {
      const roleLabel = this.isAdmin() ? "Administrador" : authenticated ? "Usuário" : "Visitante";
      const username = this.session.username ? ` • ${this.session.username}` : "";
      this.userBadge.textContent = `${roleLabel}${username}`;
    }

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
    this.statusEl.textContent = "Login necessário";
    this.statusEl.className = "status status--offline";
    this.serverInfoEl.textContent = "Entre como administrador ou usuário para acessar a ROSITA.";
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
      this.currentTokens = [];
      this.atualizarTokenStats();
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
      this.currentTokens = [];
      this.atualizarTokenStats();
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
    this.appendWelcomeMessage();
  }

  appendWelcomeMessage() {
    if (!this.chatContainer || this.chatContainer.children.length > 0) return;
    const message = this.isAdmin()
      ? "Login de administrador ativo. Você pode conversar com a ROSITA e gerenciar as configurações do sistema."
      : "Login de usuário ativo. Este perfil possui acesso somente ao bate-papo com a ROSITA.";
    this.adicionarMensagem(message, "assistant");
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
          ? "Digite sua pergunta..."
          : "Aguarde um modelo ativo para conversar";
    }
    if (this.sendBtn) {
      this.sendBtn.disabled = chatDisabled;
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
  }

  switchSettingsTab(tabName) {
    if (!this.isAdmin()) return;

    this.settingsTabs.forEach((tab) => {
      const active = tab.dataset.tab === tabName;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });

    this.settingsPanels.forEach((panel) => {
      panel.classList.toggle("is-active", panel.id === `panel-${tabName}`);
    });

    if (tabName === "references" && !this.configFilesLoaded) {
      this.carregarArquivosConfiguracao();
    }
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

      if (payload.authenticated && payload.role && payload.role !== this.session.role) {
        this.applySession({ ...this.session, ...payload });
      }

      this.statusEl.textContent = this.hasActiveModel ? "Online" : "Online • sem modelo ativo";
      this.statusEl.className = "status status--online";

      if (payload.role === "admin") {
        const docs = payload.documentos_contexto || [];
        const contexto = docs.length
          ? `Contexto carregado: ${docs.length} documento(s)`
          : "Contexto documental não encontrado";
        const gpu = payload.sistema?.gpu || {};
        const gpuResumo = gpu.disponivel
          ? `${gpu.nome || "GPU"}${gpu.uso_percentual == null ? "" : ` • ${this.formatPercent(gpu.uso_percentual)}`}`
          : (gpu.nome || "CPU");

        this.serverInfoEl.textContent = payload.modelo_atual
          ? `Administrador • Servidor: ${payload.servidor_ia} • Modelo ativo: ${payload.modelo_atual} • GPU: ${gpuResumo} • ${contexto}`
          : `Administrador • Servidor: ${payload.servidor_ia} • Selecione um modelo para começar • ${contexto}`;
        this.atualizarSistema(payload.sistema || {});
      } else if (payload.role === "user") {
        this.serverInfoEl.textContent = payload.modelo_atual
          ? `Usuário • Chat liberado com o modelo ${payload.modelo_atual}.`
          : "Usuário • O chat ficará disponível quando um administrador ativar um modelo.";
        this.atualizarSistema({});
      } else {
        this.serverInfoEl.textContent = "Entre com suas credenciais para acessar o sistema.";
        this.atualizarSistema({});
      }
    } catch {
      this.statusEl.textContent = "Offline";
      this.statusEl.className = "status status--offline";
      this.serverInfoEl.textContent = "Não foi possível conectar ao backend.";
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
    this.tokenStatsEl.textContent = `Tokens: ${total}${ultimos ? ` | ${ultimos}` : ""}`;
  }

  showLoading(text) {
    this.loadingText.textContent = text || "Carregando...";
    this.loadingOverlay.classList.remove("hidden");
  }

  hideLoading() {
    this.loadingOverlay.classList.add("hidden");
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
      this.modelSelect.innerHTML = "";
      this.hasInstalledModels = models.length > 0;
      this.hasActiveModel = Boolean(current);

      if (!models.length) {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = "Nenhum modelo instalado";
        option.selected = true;
        this.modelSelect.appendChild(option);

        if (!this.hasShownEmptyModelsTip) {
          this.adicionarMensagem(
            "Nenhum modelo está instalado ainda. Escolha uma sugestão acima ou informe um nome de modelo para começar.",
            "assistant"
          );
          this.hasShownEmptyModelsTip = true;
        }
      } else {
        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = current ? "Modelo ativo" : "Selecione um modelo instalado";
        placeholder.selected = !current;
        this.modelSelect.appendChild(placeholder);

        for (const model of models) {
          const option = document.createElement("option");
          option.value = model;
          option.textContent = model;
          if (model === current) option.selected = true;
          this.modelSelect.appendChild(option);
        }
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
    if (!this.session.authenticated || !texto || this.isAwaitingResponse || !this.hasActiveModel) return;

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
    if (!this.session.authenticated) return;

    try {
      await window.rositaApi.limparHistorico();
      this.chatContainer.innerHTML = "";
      this.appendWelcomeMessage();
    } catch (err) {
      this.adicionarMensagem(`Erro ao limpar histórico: ${err.message || String(err)}`, "assistant");
    }
  }
}

document.addEventListener("DOMContentLoaded", () => new RositaApp());
