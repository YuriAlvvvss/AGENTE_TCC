class RositaApiClient {
  constructor(baseUrl = (window && window.ROSITA_API_BASE_URL) || "") {
    // Use explicit configured base URL only. Avoid guessing ports automatically.
    this.baseUrl = (baseUrl || "").replace(/\/$/, "");
    this.isConnected = false;
  }

  shouldRetryWithNextBase(response) {
    return [404, 502, 503, 504].includes(response?.status || 0);
  }

  async request(path, options = {}) {
    const requestOptions = {
      credentials: "include",
      ...options,
      headers: {
        ...(options.headers || {}),
      },
    };

    // Allow callers to opt-out of the default timeout (for streaming endpoints)
    const allowTimeout = requestOptions.stream !== true;

    // If caller provided an AbortSignal, use it. Otherwise create one with timeout.
    let abortController = null;
    if (requestOptions.signal) {
      // Use provided signal; do not create timeout.
      abortController = null;
    } else if (allowTimeout) {
      abortController = new AbortController();
      const timeoutMs = (window && window.ROSITA_FETCH_TIMEOUT_MS) || 15000;
      const id = setTimeout(() => abortController.abort(), timeoutMs);
      // ensure we clear the timeout when the fetch finishes
      requestOptions._timeoutId = id;
      requestOptions.signal = abortController.signal;
    }

    const url = `${this.baseUrl}${path}`;
    try {
      const response = await fetch(url, requestOptions);
      if (requestOptions._timeoutId) clearTimeout(requestOptions._timeoutId);
      return response;
    } catch (err) {
      if (err.name === "AbortError") throw new Error("Tempo de conexão esgotado (timeout)");
      throw err;
    }
  }

  async obterStatus() {
    const res = await this.request("/api/status");
    if (!res.ok) throw new Error(await this._parseErro(res));
    this.isConnected = true;
    return res.json();
  }

  async obterSessao() {
    const res = await this.request("/api/auth/session");
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }

  async login(username, password) {
    const res = await this.request("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }

  async logout() {
    const res = await this.request("/api/auth/logout", { method: "POST" });
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }

  async verificarConexao() {
    try {
      await this.obterStatus();
      return true;
    } catch {
      this.isConnected = false;
      return false;
    }
  }

  async streamSse(path, options = {}, onEvent = null) {
    // Streaming endpoints shouldn't be subject to short timeouts; mark stream:true
    const opts = { ...(options || {}), stream: true };
    const response = await this.request(path, opts);
    if (!response.ok) throw new Error(await this._parseErro(response));

    if (!response.body) {
      const fallbackText = await response.text();
      return { text: fallbackText, events: [] };
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let text = "";
    let buffer = "";
    const events = [];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const linhas = buffer.split("\n");
      buffer = linhas.pop() || "";

      for (const linha of linhas) {
        if (!linha.startsWith("data: ")) continue;
        const payload = linha.slice(6).trim();

        if (payload === "[FIM]") {
          return { text, events };
        }

        if (payload.startsWith("[ERRO]")) {
          throw new Error(payload.replace("[ERRO]", "").trim());
        }

        let conteudo = payload;
        try {
          conteudo = JSON.parse(payload);
        } catch (_) {}

        events.push(conteudo);
        if (typeof conteudo === "string") text += conteudo;
        if (typeof onEvent === "function") onEvent(conteudo);
      }
    }

    return { text, events };
  }

  async enviarMensagem(mensagem, onChunk = null, signal = null) {
    const result = await this.streamSse(
      "/api/chat",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensagem }),
        signal,
      },
      (conteudo) => {
        if (typeof conteudo === "string" && typeof onChunk === "function") {
          onChunk(conteudo);
        }
      }
    );

    return result.text;
  }

  async listarModelos() {
    const res = await this.request("/api/models");
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }

  async baixarModelo(model, onProgress = null) {
    return this.streamSse(
      "/api/models/download",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model }),
      },
      (evento) => {
        if (typeof onProgress === "function") onProgress(evento);
      }
    );
  }

  async selecionarModelo(model) {
    const res = await this.request("/api/models/select", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model }),
    });
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }

  async descarregarModeloAtual() {
    const res = await this.request("/api/models/unload", {
      method: "POST",
    });
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }

  async excluirModelo(model) {
    const res = await this.request("/api/models/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model }),
    });
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }

  async listarArquivosConfiguracao() {
    const res = await this.request("/api/config/files");
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }

  async lerArquivoConfiguracao(filename) {
    const res = await this.request(`/api/config/files/${encodeURIComponent(filename)}`);
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }

  async salvarArquivoConfiguracao(filename, content) {
    const res = await this.request(`/api/config/files/${encodeURIComponent(filename)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }

  async limparHistorico() {
    const res = await this.request("/api/limpar", { method: "POST" });
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }

  async obterHistorico() {
    const res = await this.request("/api/historico");
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }

  async _parseErro(res) {
    let erro = `Erro HTTP ${res.status}`;
    try {
      const payload = await res.json();
      erro = payload.erro || erro;
    } catch (_) {
      const text = await res.text();
      if (text) erro = text;
    }
    return erro;
  }

  async obterProvedores() {
    const res = await this.request("/api/provedores");
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }

  async trocarProvedor(provedor) {
    const res = await this.request("/api/provedores/trocar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provedor }),
    });
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }

  async obterCredenciais() {
    const res = await this.request("/api/credenciais");
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }

  async salvarCredenciais(config) {
    const res = await this.request("/api/credenciais", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config || {}),
    });
    if (!res.ok) throw new Error(await this._parseErro(res));
    return res.json();
  }
}

window.rositaApi = new RositaApiClient();
