class RositaApiClient {
  constructor(baseUrl = "http://localhost:5000") {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.isConnected = false;
  }

  async verificarConexao() {
    try {
      const res = await fetch(`${this.baseUrl}/api/status`);
      this.isConnected = res.ok;
      return this.isConnected;
    } catch {
      this.isConnected = false;
      return false;
    }
  }

  async enviarMensagem(mensagem, onChunk = null) {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mensagem }),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Erro HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let respostaCompleta = "";
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const linhas = buffer.split("\n");
      buffer = linhas.pop() || "";

      for (const linha of linhas) {
        if (!linha.startsWith("data: ")) continue;
        const payload = linha.slice(6).trim();
        if (payload === "[FIM]") return respostaCompleta;
        if (payload.startsWith("[ERRO]")) throw new Error(payload.replace("[ERRO]", "").trim());
        let conteudo = payload;
        try {
          conteudo = JSON.parse(payload);
        } catch (_) {}
        if (typeof conteudo === "string") {
          respostaCompleta += conteudo;
          if (typeof onChunk === "function") onChunk(conteudo);
        }
      }
    }

    return respostaCompleta;
  }

  async listarModelos() {
    const res = await fetch(`${this.baseUrl}/api/models`);
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `Erro HTTP ${res.status}`);
    }
    return res.json();
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
