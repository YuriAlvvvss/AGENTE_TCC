"""Cliente CLI da ROSITA reutilizando o mesmo núcleo da API."""

from pathlib import Path
import sys

BACKEND_SRC = Path(__file__).resolve().parent / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from rosita.bootstrap import criar_agente
from rosita.settings import load_settings


def executar_cli() -> None:
    """Loop de conversa no terminal."""
    settings = load_settings()
    agent = criar_agente(settings)

    print("ROSITA - Assistente Escolar")
    print("=" * 40)
    print("Digite 'sair' para encerrar.")

    while True:
        pergunta = input("\nVoce: ").strip()
        if pergunta.lower() == "sair":
            print("Ate logo!")
            break

        print("\nRosita: ", end="", flush=True)
        try:
            for chunk in agent.processar_pergunta(pergunta):
                print(chunk, end="", flush=True)
            print("\n")
        except ValueError as exc:
            print(f"\nAviso: {exc}")
        except Exception as exc:
            print(f"\nErro: {exc}")


if __name__ == "__main__":
    executar_cli()
