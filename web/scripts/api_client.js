class RositaApiClient {
  constructor(baseUrl = window.ROSITA_API_BASE_URL || "") {
    this.baseUrlCandidates = this.buildBaseUrlCandidates(baseUrl);
    this.baseUrl = this.baseUrlCandidates[0] || "";
    this.isConnected = false;
  }

  buildBaseUrlCandidates(explicitBaseUrl = "") {
    const candidates = [];
    const pushCandidate = (value) => {
      const normalized = (value || "").replace(/\/$/, "");
      if (!candidates.includes(normalized)) {
        candidates.push(normalized);
      }
    };

    pushCandidate(explicitBaseUrl);
    pushCandidate("");

    if (typeof window !== "undefined" && window.location) {
      const { protocol, hostname } = window.location;
      if (hostname && (protocol === "http:" || protocol === "https:")) {
        pushCandidate(`${protocol}//${hostname}:18500`);
      }
    }

    return candidates.length ? candidates : [""];
  }

  shouldRetryWithNextBase(response) {
    return [404, 502, 503, 504].includes(response?.status || 0);
  }

  async request(path, options = {}) {
    let lastError = null;
    const lastCandidate = this.baseUrlCandidates[this.baseUrlCandidates.length - 1];
    const requestOptions = {
      credentials: "include",
      ...options,
      headers: {
        ...(options.headers || {}),
      },
    };

    for (const candidate of this.baseUrlCandidates) {
      const url = `${candidate}${path}`;
      try {
        const response = await fetch(url, requestOptions);
        if (!response.ok && this.shouldRetryWithNextBase(response) && candidate !== lastCandidate) {
          lastError = new Error(`Erro HTTP ${response.status}`);
          continue;
        }

        this.baseUrlCandidates = [candidate, ...this.baseUrlCandidates.filter((item) => item !== candidate)];
        this.baseUrl = candidate;
        return response;
      } catch (error) {
        lastError = error;
        if (candidate === lastCandidate) {
          break;
        }
      }
    }

    throw lastError || new Error("Não foi possível conectar ao backend ROSITA.");
  }

  async obterStatus() {
    const res = await this.request("/api/status");
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `Erro HTTP ${res.status}`);
    }
    this.isConnected = true;
    return res.json();
  }

  async obterSessao() {
    const res = await this.request("/api/auth/session");
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `Erro HTTP ${res.status}`);
    }
    return res.json();
  }

  async login(username, password) {
    const res = await this.request("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      let erro = `Erro HTTP ${res.status}`;
      try {
        const payload = await res.json();
        erro = payload.erro || erro;
      } catch (_) {
        const text = await res.text();
        if (text) erro = text;
      }
      throw new Error(erro);
    }
    return res.json();
  }

  async logout() {
    const res = await this.request("/api/auth/logout", { method: "POST" });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `Erro HTTP ${res.status}`);
    }
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
    const response = await this.request(path, options);

    if (!response.ok) {
      const text = await response.text();
      let errorMessage = text || `Erro HTTP ${response.status}`;
      try {
        const payload = JSON.parse(text);
        errorMessage = payload.erro || errorMessage;
      } catch (_) {}
      throw new Error(errorMessage);
    }

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

  async enviarMensagem(mensagem, onChunk = null) {
    const result = await this.streamSse(
      "/api/chat",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensagem }),
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
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `Erro HTTP ${res.status}`);
    }
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
    if (!res.ok) {
      let erro = `Erro HTTP ${res.status}`;
      try {
        const payload = await res.json();
        erro = payload.erro || erro;
      } catch (_) {
        const text = await res.text();
        if (text) erro = text;
      }
      throw new Error(erro);
    }
    return res.json();
  }

  async descarregarModeloAtual() {
    const res = await this.request("/api/models/unload", {
      method: "POST",
    });
    if (!res.ok) {
      let erro = `Erro HTTP ${res.status}`;
      try {
        const payload = await res.json();
        erro = payload.erro || erro;
      } catch (_) {
        const text = await res.text();
        if (text) erro = text;
      }
      throw new Error(erro);
    }
    return res.json();
  }

  async excluirModelo(model) {
    const res = await this.request("/api/models/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model }),
    });
    if (!res.ok) {
      let erro = `Erro HTTP ${res.status}`;
      try {
        const payload = await res.json();
        erro = payload.erro || erro;
      } catch (_) {
        const text = await res.text();
        if (text) erro = text;
      }
      throw new Error(erro);
    }
    return res.json();
  }

  async listarArquivosConfiguracao() {
    const res = await this.request("/api/config/files");
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `Erro HTTP ${res.status}`);
    }
    return res.json();
  }

  async lerArquivoConfiguracao(filename) {
    const res = await this.request(`/api/config/files/${encodeURIComponent(filename)}`);
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `Erro HTTP ${res.status}`);
    }
    return res.json();
  }

  async salvarArquivoConfiguracao(filename, content) {
    const res = await this.request(`/api/config/files/${encodeURIComponent(filename)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
    if (!res.ok) {
      let erro = `Erro HTTP ${res.status}`;
      try {
        const payload = await res.json();
        erro = payload.erro || erro;
      } catch (_) {
        const text = await res.text();
        if (text) erro = text;
      }
      throw new Error(erro);
    }
    return res.json();
  }

  async limparHistorico() {
    const res = await this.request("/api/limpar", { method: "POST" });
    if (!res.ok) throw new Error(`Erro HTTP ${res.status}`);
    return res.json();
  }
}

window.rositaApi = new RositaApiClient();
