class RositaApp {
  constructor() {
    this.chatContainer = document.getElementById("chat-container");
    this.userInput = document.getElementById("user-input");
    this.sendBtn = document.getElementById("send-btn");
    this.clearBtn = document.getElementById("clear-btn");
    this.statusEl = document.getElementById("status");
    this.serverInfoEl = document.getElementById("server-info");
    this.settingsBtn = document.getElementById("settings-btn");
    this.configModal = document.getElementById("config-modal");
    this.closeSettingsBtn = document.getElementById("close-settings-btn");
    this.configFileSelect = document.getElementById("config-file-select");
    this.reloadConfigBtn = document.getElementById("reload-config-btn");
    this.configEditor = document.getElementById("config-editor");
    this.configStatusEl = document.getElementById("config-status");
    this.saveConfigBtn = document.getElementById("save-config-btn");
    this.modelSelect = document.getElementById("model-select");
    this.reloadModelsBtn = document.getElementById("reload-models-btn");
    this.downloadInput = document.getElementById("model-download-input");
    this.downloadBtn = document.getElementById("download-model-btn");
    this.suggestedModelsEl = document.getElementById("suggested-models");
    this.downloadProgressWrap = document.getElementById("download-progress-wrap");
    this.downloadStatusEl = document.getElementById("download-status");
    this.downloadProgressBar = document.getElementById("download-progress-bar");
    this.loadingOverlay = document.getElementById("loading-overlay");
    this.loadingText = document.getElementById("loading-text");
    this.tokenStatsEl = document.getElementById("token-stats");

    this.isAwaitingResponse = false;
    this.isDownloadingModel = false;
    this.hasInstalledModels = false;
    this.hasActiveModel = false;
    this.currentTokens = [];
    this.hasShownEmptyModelsTip = false;
    this.modelRefreshTimer = null;
    this.currentConfigFile = "";

    this.bindEvents();
    this.updateControls();
    this.verificarStatus();
    this.carregarModelos();
    this.adicionarMensagem("Olá! Sou a ROSITA. Como posso ajudar?", "assistant");
  }

  bindEvents() {
    this.sendBtn.addEventListener("click", () => this.enviarMensagem());
    this.clearBtn.addEventListener("click", () => this.limparChat());
    this.reloadModelsBtn.addEventListener("click", () => this.carregarModelos());
    this.downloadBtn.addEventListener("click", () => this.baixarModelo());
    this.settingsBtn.addEventListener("click", () => this.abrirConfiguracoes());
    this.closeSettingsBtn.addEventListener("click", () => this.fecharConfiguracoes());
    this.reloadConfigBtn.addEventListener("click", () => this.carregarArquivosConfiguracao());
    this.configFileSelect.addEventListener("change", () => this.carregarConteudoArquivoConfiguracao());
    this.saveConfigBtn.addEventListener("click", () => this.salvarConfiguracoes());
    this.modelSelect.addEventListener("change", () => this.selecionarModelo());

    this.userInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !this.isAwaitingResponse && this.hasActiveModel) {
        this.enviarMensagem();
      }
    });

    this.downloadInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !this.isDownloadingModel) {
        this.baixarModelo();
      }
    });
  }

  updateControls() {
    const chatDisabled = this.isAwaitingResponse || this.isDownloadingModel || !this.hasActiveModel;
    this.userInput.disabled = chatDisabled;
    this.sendBtn.disabled = chatDisabled;
    this.modelSelect.disabled = this.isAwaitingResponse || this.isDownloadingModel || !this.hasInstalledModels;
    this.reloadModelsBtn.disabled = this.isAwaitingResponse || this.isDownloadingModel;
    this.clearBtn.disabled = this.isAwaitingResponse;
    this.downloadInput.disabled = this.isAwaitingResponse || this.isDownloadingModel;
    this.downloadBtn.disabled = this.isAwaitingResponse || this.isDownloadingModel;
    this.settingsBtn.disabled = false;
  }

  async verificarStatus() {
    try {
      const payload = await window.rositaApi.obterStatus();
      const docs = payload.documentos_contexto || [];
      const contexto = docs.length
        ? `Contexto carregado: ${docs.length} documento(s)`
        : "Contexto documental não encontrado";

      this.statusEl.textContent = payload.modelo_atual ? "Online" : "Online • sem modelo ativo";
      this.statusEl.className = "status status--online";
      this.serverInfoEl.textContent = payload.modelo_atual
        ? `Servidor de IA: ${payload.servidor_ia} • Modelo ativo: ${payload.modelo_atual} • ${contexto}`
        : `Servidor de IA: ${payload.servidor_ia} • Selecione um modelo para começar • ${contexto}`;
    } catch {
      this.statusEl.textContent = "Offline";
      this.statusEl.className = "status status--offline";
      this.serverInfoEl.textContent = "Não foi possível conectar ao backend.";
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
    this.suggestedModelsEl.innerHTML = "";
    for (const item of models || []) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "suggested-chip";
      button.title = `${item.description || ""} ${item.size || ""}`.trim();
      button.textContent = `${item.label || item.name} ${item.size ? `• ${item.size}` : ""}`;
      button.addEventListener("click", () => {
        this.downloadInput.value = item.name;
        this.downloadInput.focus();
      });
      this.suggestedModelsEl.appendChild(button);
    }
  }

  setDownloadProgress(percentual, status) {
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
    this.downloadProgressWrap.classList.add("hidden");
    this.downloadProgressBar.style.width = "0%";
    this.downloadStatusEl.textContent = "Preparando download...";
  }

  async carregarModelos(silent = false) {
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

  async baixarModelo() {
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
      this.adicionarMensagem(`Erro ao baixar modelo: ${err.message || String(err)}`, "assistant");
      this.setDownloadProgress(0, `Falha ao baixar ${model}`);
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

  async abrirConfiguracoes() {
    this.configModal.classList.remove("hidden");
    await this.carregarArquivosConfiguracao();
  }

  fecharConfiguracoes() {
    this.configModal.classList.add("hidden");
  }

  async carregarArquivosConfiguracao() {
    this.configStatusEl.textContent = "Carregando arquivos editáveis...";
    try {
      const payload = await window.rositaApi.listarArquivosConfiguracao();
      const files = payload.files || [];
      this.configFileSelect.innerHTML = "";

      if (!files.length) {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = "Nenhum arquivo editável disponível";
        this.configFileSelect.appendChild(option);
        this.configEditor.value = "";
        this.currentConfigFile = "";
        this.configStatusEl.textContent = "Nenhum arquivo de configuração disponível.";
        return;
      }

      for (const file of files) {
        const option = document.createElement("option");
        option.value = file;
        option.textContent = file;
        this.configFileSelect.appendChild(option);
      }

      this.currentConfigFile = this.configFileSelect.value;
      await this.carregarConteudoArquivoConfiguracao();
    } catch (err) {
      this.configStatusEl.textContent = `Erro ao listar arquivos: ${err.message || String(err)}`;
    }
  }

  async carregarConteudoArquivoConfiguracao() {
    const filename = this.configFileSelect.value;
    this.currentConfigFile = filename;
    if (!filename) {
      this.configEditor.value = "";
      return;
    }

    this.configStatusEl.textContent = `Carregando ${filename}...`;
    try {
      const payload = await window.rositaApi.lerArquivoConfiguracao(filename);
      this.configEditor.value = payload.content || "";
      this.configStatusEl.textContent = `${filename} carregado para edição.`;
    } catch (err) {
      this.configStatusEl.textContent = `Erro ao abrir arquivo: ${err.message || String(err)}`;
    }
  }

  async salvarConfiguracoes() {
    const filename = this.currentConfigFile || this.configFileSelect.value;
    if (!filename) return;

    this.configStatusEl.textContent = `Salvando ${filename}...`;
    this.saveConfigBtn.disabled = true;
    try {
      await window.rositaApi.salvarArquivoConfiguracao(filename, this.configEditor.value);
      this.configStatusEl.textContent = `${filename} salvo com sucesso. O contexto da IA foi atualizado.`;
      this.adicionarMensagem(`As configurações do arquivo ${filename} foram salvas com sucesso.`, "assistant");
      await this.verificarStatus();
    } catch (err) {
      this.configStatusEl.textContent = `Erro ao salvar arquivo: ${err.message || String(err)}`;
    } finally {
      this.saveConfigBtn.disabled = false;
    }
  }

  async limparChat() {
    try {
      await window.rositaApi.limparHistorico();
      this.chatContainer.innerHTML = "";
      this.adicionarMensagem("Histórico limpo. Como posso ajudar?", "assistant");
    } catch (err) {
      this.adicionarMensagem(`Erro ao limpar histórico: ${err.message || String(err)}`, "assistant");
    }
  }
}

document.addEventListener("DOMContentLoaded", () => new RositaApp());
