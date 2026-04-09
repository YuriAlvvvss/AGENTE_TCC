class RositaApp {
  constructor() {
    this.chatContainer = document.getElementById("chat-container");
    this.userInput = document.getElementById("user-input");
    this.sendBtn = document.getElementById("send-btn");
    this.clearBtn = document.getElementById("clear-btn");
    this.statusEl = document.getElementById("status");
    this.modelSelect = document.getElementById("model-select");
    this.reloadModelsBtn = document.getElementById("reload-models-btn");
    this.loadingOverlay = document.getElementById("loading-overlay");
    this.loadingText = document.getElementById("loading-text");
    this.tokenStatsEl = document.getElementById("token-stats");
    this.isAwaitingResponse = false;
    this.currentTokens = [];

    this.bindEvents();
    this.verificarStatus();
    this.carregarModelos();
    this.adicionarMensagem("Ola! Sou a ROSITA. Como posso ajudar?", "assistant");
  }

  bindEvents() {
    this.sendBtn.addEventListener("click", () => this.enviarMensagem());
    this.clearBtn.addEventListener("click", () => this.limparChat());
    this.reloadModelsBtn.addEventListener("click", () => this.carregarModelos());
    this.modelSelect.addEventListener("change", () => this.selecionarModelo());
    this.userInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !this.isAwaitingResponse) this.enviarMensagem();
    });
  }

  async verificarStatus() {
    const ok = await window.rositaApi.verificarConexao();
    this.statusEl.textContent = ok ? "Online" : "Offline";
    this.statusEl.className = ok ? "status status--online" : "status status--offline";
  }

  adicionarMensagem(texto, tipo) {
    const wrap = document.createElement("div");
    wrap.className = `message ${tipo}`;
    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = texto;
    wrap.appendChild(content);
    this.chatContainer.appendChild(wrap);
    this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    return content;
  }

  tokenizeChunk(chunk) {
    // Tokenizacao simples para visualizacao em tempo real no frontend.
    return (chunk.match(/\S+/g) || []);
  }

  atualizarTokenStats() {
    const total = this.currentTokens.length;
    const ultimos = this.currentTokens.slice(-12).join(" | ");
    this.tokenStatsEl.textContent = `Tokens: ${total}${ultimos ? ` | ${ultimos}` : ""}`;
  }

  setInputLock(locked) {
    this.isAwaitingResponse = locked;
    this.userInput.disabled = locked;
    this.sendBtn.disabled = locked;
    this.modelSelect.disabled = locked;
    this.reloadModelsBtn.disabled = locked;
    this.clearBtn.disabled = locked;
  }

  showLoading(text) {
    this.loadingText.textContent = text || "Carregando...";
    this.loadingOverlay.classList.remove("hidden");
  }

  hideLoading() {
    this.loadingOverlay.classList.add("hidden");
  }

  async carregarModelos() {
    this.showLoading("Buscando modelos instalados no Ollama...");
    try {
      const payload = await window.rositaApi.listarModelos();
      const models = payload.models || [];
      const current = payload.current_model || "";

      this.modelSelect.innerHTML = "";
      for (const model of models) {
        const option = document.createElement("option");
        option.value = model;
        option.textContent = model;
        if (model === current) option.selected = true;
        this.modelSelect.appendChild(option);
      }
    } catch (err) {
      this.adicionarMensagem(`Erro ao carregar modelos: ${err.message || String(err)}`, "assistant");
    } finally {
      this.hideLoading();
    }
  }

  async selecionarModelo() {
    const model = this.modelSelect.value;
    if (!model) return;

    this.showLoading(`Trocando modelo para ${model}...`);
    this.setInputLock(true);
    try {
      await window.rositaApi.selecionarModelo(model);
      this.adicionarMensagem(`Modelo ativo alterado para: ${model}`, "assistant");
    } catch (err) {
      this.adicionarMensagem(`Erro ao trocar modelo: ${err.message || String(err)}`, "assistant");
      await this.carregarModelos();
    } finally {
      this.setInputLock(false);
      this.hideLoading();
    }
  }

  async enviarMensagem() {
    const texto = (this.userInput.value || "").trim();
    if (!texto || this.isAwaitingResponse) return;

    this.currentTokens = [];
    this.atualizarTokenStats();
    this.setInputLock(true);

    this.adicionarMensagem(texto, "user");
    this.userInput.value = "";
    const content = this.adicionarMensagem("ROSITA: ", "assistant");

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
      this.setInputLock(false);
    }
  }

  async limparChat() {
    await window.rositaApi.limparHistorico();
    this.chatContainer.innerHTML = "";
    this.adicionarMensagem("Historico limpo. Como posso ajudar?", "assistant");
  }
}

document.addEventListener("DOMContentLoaded", () => new RositaApp());
