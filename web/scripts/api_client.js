class RositaApiClient {
  constructor(baseUrl = window.ROSITA_API_BASE_URL || "") {
    this.baseUrl = (baseUrl || "").replace(/\/$/, "");
    this.isConnected = false;
  }

  async obterStatus() {
    const res = await fetch(`${this.baseUrl}/api/status`);
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `Erro HTTP ${res.status}`);
    }
    this.isConnected = true;
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
    const response = await fetch(`${this.baseUrl}${path}`, options);

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Erro HTTP ${response.status}`);
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
    const res = await fetch(`${this.baseUrl}/api/models`);
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
    const res = await fetch(`${this.baseUrl}/api/models/select`, {
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

  async limparHistorico() {
    const res = await fetch(`${this.baseUrl}/api/limpar`, { method: "POST" });
    if (!res.ok) throw new Error(`Erro HTTP ${res.status}`);
    return res.json();
  }
}

window.rositaApi = new RositaApiClient();
