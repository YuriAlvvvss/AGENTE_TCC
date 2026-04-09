/**
 * Interface do chat ROSITA: eventos, status e streaming no DOM.
 */
class RositaApp {
  constructor() {
    this.chatContainer = document.getElementById("chat-container");
    this.userInput = document.getElementById("user-input");
    this.sendBtn = document.getElementById("send-btn");
    this.clearBtn = document.getElementById("clear-btn");
    this.statusEl = document.getElementById("status");

    this.adicionarMensagem(
      "Olá! Sou a ROSITA, assistente da PEI Rosa Bonfiglioli. Como posso ajudar?",
      "assistant"
    );
    this.inicializarEventos();
    this.verificarStatus();
  }

  /** Registra cliques e tecla Enter no campo de texto. */
  inicializarEventos() {
    this.sendBtn.addEventListener("click", () => this.enviarMensagem());
    this.clearBtn.addEventListener("click", () => this.limparChat());
    this.userInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.enviarMensagem();
      }
    });
  }

  /** Consulta /api/status e atualiza o indicador visual. */
  async verificarStatus() {
    try {
      await window.rositaApi.verificarConexao();
      const ok = window.rositaApi.isConnected;
      this.atualizarIndicadorStatus(ok);
    } catch {
      this.atualizarIndicadorStatus(false);
    }
  }

  /**
   * Atualiza cor do indicador (verde = online, vermelho = offline).
   * @param {boolean} conectado
   */
  atualizarIndicadorStatus(conectado) {
    if (!this.statusEl) return;
    this.statusEl.classList.remove("status--online", "status--offline");
    this.statusEl.classList.add(conectado ? "status--online" : "status--offline");
    this.statusEl.textContent = conectado ? "Online" : "Offline";
    this.statusEl.setAttribute("aria-label", conectado ? "Servidor conectado" : "Servidor desconectado");
  }

  /** Envia texto do input para a API e atualiza o painel com streaming. */
  async enviarMensagem() {
    const texto = (this.userInput.value || "").trim();
    if (!texto) {
      alert("Digite uma mensagem antes de enviar.");
      return;
    }
    if (texto.length > 1000) {
      alert("Mensagem muito longa (máximo 1000 caracteres).");
      return;
    }

    this.userInput.disabled = true;
    this.sendBtn.disabled = true;

    this.adicionarMensagem(texto, "user");
    this.userInput.value = "";

    const respostaDiv = this.criarContainerResposta();
    const conteudoDiv = respostaDiv.querySelector(".message-content");

    try {
      await window.rositaApi.enviarMensagem(texto, (chunk) => {
        conteudoDiv.textContent += chunk;
        this.scrollParaBaixo();
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      conteudoDiv.textContent = `🤖 Erro: ${msg}`;
      console.error(err);
    } finally {
      this.userInput.disabled = false;
      this.sendBtn.disabled = false;
      this.userInput.focus();
      this.scrollParaBaixo();
    }
  }

  /**
   * Insere uma bolha de mensagem no chat.
   * @param {string} conteudo
   * @param {'user'|'assistant'} tipo
   */
  adicionarMensagem(conteudo, tipo = "user") {
    const wrap = document.createElement("div");
    wrap.className = `message ${tipo}`;
    const inner = document.createElement("div");
    inner.className = "message-content";
    inner.textContent = conteudo;
    wrap.appendChild(inner);
    this.chatContainer.appendChild(wrap);
    this.scrollParaBaixo();
  }

  /** Cria linha da ROSITA com prefixo inicial para streaming. */
  criarContainerResposta() {
    const messageDiv = document.createElement("div");
    messageDiv.className = "message assistant";
    const inner = document.createElement("div");
    inner.className = "message-content";
    inner.textContent = "🤖 ";
    messageDiv.appendChild(inner);
    this.chatContainer.appendChild(messageDiv);
    this.scrollParaBaixo();
    return messageDiv;
  }

  /** Limpa histórico no servidor e reinicia o painel com mensagem de boas-vindas. */
  async limparChat() {
    if (!window.confirm("Limpar toda a conversa?")) return;
    try {
      await window.rositaApi.limparHistorico();
      this.chatContainer.innerHTML = "";
      this.adicionarMensagem(
        "Olá! Sou a ROSITA, assistente da PEI Rosa Bonfiglioli. Como posso ajudar?",
        "assistant"
      );
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      alert(`Não foi possível limpar: ${msg}`);
    }
  }

  scrollParaBaixo() {
    this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  new RositaApp();
});
