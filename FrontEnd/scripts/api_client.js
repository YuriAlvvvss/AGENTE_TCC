/**
 * Cliente HTTP para a API ROSITA (SSE em /api/chat).
 */

/**
 * Interpreta o payload após o prefixo "data: " (JSON ou texto especial).
 * @param {string} raw
 * @returns {string|number|boolean|null}
 */
function parsePayload(raw) {
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

class RositaApiClient {
  /**
   * @param {string} baseUrl - URL base do backend (ex.: http://localhost:5000)
   */
  constructor(baseUrl = "http://localhost:5000") {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    /** @type {boolean} */
    this.isConnected = false;
  }

  /**
   * Verifica disponibilidade do backend via GET /api/status.
   * @returns {Promise<boolean>} true se online
   */
  async verificarConexao() {
    try {
      const res = await fetch(`${this.baseUrl}/api/status`, { method: "GET" });
      this.isConnected = res.ok;
      return this.isConnected;
    } catch (e) {
      this.isConnected = false;
      return false;
    }
  }

  /**
   * Envia mensagem e consome stream SSE; opcionalmente notifica cada chunk.
   * @param {string} mensagem - Texto do usuário
   * @param {(chunk: string) => void} [onChunk] - Callback por fragmento de texto
   * @returns {Promise<string>} Texto completo da resposta
   */
  async enviarMensagem(mensagem, onChunk = null) {
    if (!this.isConnected) {
      await this.verificarConexao();
    }
    if (!this.isConnected) {
      throw new Error(
        "Sem conexão com o servidor ROSITA. Verifique se o backend está em execução."
      );
    }

    const texto = typeof mensagem === "string" ? mensagem.trim() : "";
    if (!texto) {
      throw new Error("Digite uma mensagem válida.");
    }
    if (texto.length > 1000) {
      throw new Error("Mensagem muito longa (máximo 1000 caracteres).");
    }

    let respostaCompleta = "";

    try {
      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensagem: texto }),
      });

      if (!response.ok) {
        let detalhe = response.statusText;
        try {
          const errJson = await response.json();
          if (errJson && errJson.erro) detalhe = errJson.erro;
        } catch (_) {
          /* ignora parse de erro */
        }
        throw new Error(detalhe || `Erro HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const linhas = buffer.split("\n");
        buffer = linhas.pop() || "";

        for (const linha of linhas) {
          if (!linha.startsWith("data: ")) continue;
          const raw = linha.slice(6).trim();
          const conteudo = parsePayload(raw);

          if (conteudo === "[FIM]") {
            return respostaCompleta;
          }
          if (typeof conteudo === "string" && conteudo.startsWith("[ERRO]")) {
            throw new Error(conteudo.replace(/^\[ERRO\]\s*/, ""));
          }
          if (typeof conteudo === "string" && conteudo.length) {
            respostaCompleta += conteudo;
            if (typeof onChunk === "function") onChunk(conteudo);
          }
        }
      }

      if (buffer.startsWith("data: ")) {
        const raw = buffer.slice(6).trim();
        const conteudo = parsePayload(raw);
        if (conteudo === "[FIM]") return respostaCompleta;
        if (typeof conteudo === "string" && conteudo.startsWith("[ERRO]")) {
          throw new Error(conteudo.replace(/^\[ERRO\]\s*/, ""));
        }
        if (typeof conteudo === "string" && conteudo.length) {
          respostaCompleta += conteudo;
          if (typeof onChunk === "function") onChunk(conteudo);
        }
      }

      return respostaCompleta;
    } catch (e) {
      throw e instanceof Error ? e : new Error(String(e));
    }
  }

  /**
   * GET /api/historico
   * @returns {Promise<object>}
   */
  async obterHistorico() {
    const res = await fetch(`${this.baseUrl}/api/historico`);
    if (!res.ok) {
      const t = await res.text();
      throw new Error(t || `Erro HTTP ${res.status}`);
    }
    return res.json();
  }

  /**
   * POST /api/limpar
   * @returns {Promise<object>}
   */
  async limparHistorico() {
    const res = await fetch(`${this.baseUrl}/api/limpar`, { method: "POST" });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(t || `Erro HTTP ${res.status}`);
    }
    return res.json();
  }

  /**
   * GET /api/status
   * @returns {Promise<object>}
   */
  async obterStatus() {
    const res = await fetch(`${this.baseUrl}/api/status`);
    if (!res.ok) throw new Error(`Status HTTP ${res.status}`);
    return res.json();
  }
}

/** Instância global usada pela interface */
window.rositaApi = new RositaApiClient();
