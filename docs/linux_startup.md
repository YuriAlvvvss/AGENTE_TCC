# Execução no Linux com Script Automático

Este guia descreve a inicialização da ROSITA no Linux usando o script de partida robusto do projeto.

## O que foi reforçado

O fluxo agora está mais estável para ambientes leves, inclusive MiniOS rodando no pendrive:

1. valida a estrutura mínima do projeto antes de iniciar;
2. verifica Python 3.8+ e tenta instalar os pacotes necessários pelo gerenciador do sistema;
3. cria ou reaproveita a pasta do ambiente virtual;
4. atualiza pip, setuptools e wheel com tentativas de repetição;
5. instala as dependências do backend;
6. garante que o Ollama esteja ativo;
7. verifica a disponibilidade do Ollama e deixa a escolha do modelo para o usuário;
8. inicia backend e frontend com checagem real de saúde;
9. grava logs persistentes na pasta de logs do projeto.

## Requisitos recomendados para MiniOS

- Linux com bash;
- acesso a sudo ou conta root para instalar dependências;
- internet na primeira execução;
- pelo menos 6 GB livres em disco para o modelo padrão;
- idealmente 8 GB de RAM para o modelo padrão.

> Em máquinas mais limitadas, prefira um modelo menor para maior estabilidade.

## Uso recomendado

Na raiz do projeto:

```bash
chmod +x start_system.sh
./start_system.sh
```

## Docker no MiniOS

O `docker-compose.yml` na raiz **não** define `build` para `web` nem `backend`: evita o BuildKit. Comando:

```bash
docker compose up -d
```

Não use `docker compose up --build` para forçar build desses serviços. GPU é opcional: ficheiro `docker-compose.gpu.yml` (ver `README.md`).

### Erro `failed to mount ... overlay ... invalid argument` ao subir contentores

Se aparecer **mesmo com** `docker compose up -d` (sem build), o problema **não é o repositório**: o motor do Docker (containerd) não consegue montar **overlay** ao preparar a raiz do contentor a partir das camadas da imagem. Isto é frequente em **MiniOS / live USB / VM** ou quando `/var/lib/docker` está num sistema de ficheiros pouco compatível.

**Opção 1 — Recomendada no MiniOS:** não use Docker para a ROSITA; use o arranque nativo (já instala dependências e trata do Ollama):

```bash
chmod +x start_system.sh
./start_system.sh
```

**Opção 2 — Corrigir o Docker com o driver `vfs`:** usa mais disco e é mais lento, mas costuma funcionar onde o overlay falha.

No repositório há um exemplo e um script (na raiz do clone):

```bash
cd ~/AGENTE_TCC
sudo ./scripts/enable-docker-vfs-minios.sh
```

O script grava a configuração a partir de `docker/minios-vfs-daemon.json`, faz cópia de segurança se já existir `daemon.json` e, se tiver **`jq`**, funde com a configuração antiga; caso contrário pede fusão manual. Reinicia o Docker via `systemctl`.

Se o Docker **recusar iniciar** ou o erro continuar, com o Docker parado pode ser necessário **apagar ou mover** `/var/lib/docker` (mistura de drivers) — **apaga imagens e contentores**; só faça se puder perder isso.

Depois: `docker compose up -d`.

**Manual (sem script):** pare o Docker, edite **`/etc/docker/daemon.json`** com `"storage-driver": "vfs"` (JSON válido; junte a outras chaves se existirem), arranque o Docker de novo.

**Opção 3 — Onde está o Docker:** confirme com `docker info | grep -E 'Docker Root Dir|Storage Driver'`. O diretório de dados não deve estar em **NFS**; **ext4** ou **xfs** local costuma ser o mais seguro.

Resumo: no MiniOS, **`./start_system.sh`** é o caminho mais simples; Docker só fica estável depois de corrigir o **storage driver** no host.

## Uso recomendado no MiniOS

Se o sistema for mais leve ou tiver pouca RAM, use um modelo menor:

```bash
ROSITA_OLLAMA_MODEL=llama3.2:3b ./start_system.sh --yes
```

## Modo somente validação

Para instalar e validar tudo sem iniciar os serviços ainda:

```bash
./start_system.sh --no-start --yes
```

## Opções suportadas

```bash
./start_system.sh --help
```

Opções principais:

- `--yes`: aprova automaticamente instalações necessárias;
- `--skip-browser`: não abre navegador automaticamente;
- `--no-start`: apenas valida e instala dependências.

## Endereços após a inicialização

- Backend: http://127.0.0.1:18500
- Web: http://127.0.0.1:18080
- Ollama local: http://127.0.0.1:11434
- ou servidor de IA externo, se configurado no `.env`

## Logs

Os logs agora ficam dentro da pasta do projeto:

- `logs/startup.log`
- `logs/backend.log`
- `logs/web.log`
- `logs/ollama.log`

## Encerramento dos serviços

Se estiverem em terminais separados, basta fechar os terminais.

Se estiverem em background:

```bash
pkill -f "app.py"
pkill -f "http.server 8080"
pkill -f "ollama serve"
```

## Deploy com Docker Compose / Coolify

Para publicar no servidor com containers:

```bash
cp .env.example .env
```

O padrão já usa o Ollama interno do `docker-compose`. Se preferir apontar para um servidor de IA externo, altere no arquivo `.env`:

```bash
ROSITA_OLLAMA_HOST=https://seu-servidor-ia.exemplo.com
```

Suba a stack (sem `--build`; por omissão **só CPU**, não exige GPU):

```bash
docker compose up -d
```

No Coolify, importe o projeto e selecione o `docker-compose.yml` da raiz do repositório.

Com **placa NVIDIA** e toolkit instalados, pode acrescentar `docker-compose.gpu.yml` (ver `README.md`). Sem GPU, **não** use esse ficheiro. Opcional: `NVIDIA_VISIBLE_DEVICES` no `.env` quando usar o override de GPU.

Após a primeira subida, use o frontend para baixar um modelo recomendado e ativá-lo manualmente, sem precisar entrar no container.
Nenhum modelo é baixado ou carregado automaticamente pelo projeto.

## Ajuste de portas

Você pode alterar as portas sem editar o código:

```bash
ROSITA_API_PORT=18501 ROSITA_WEB_PORT=18081 ./start_system.sh --yes
```

O script informa as portas efetivas no final da execução.
