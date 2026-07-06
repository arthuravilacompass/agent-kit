---
name: export-logs
description: Invoque para exportar logs de rede HTTP de uma sessão Flutter debug rodando, filtrados por intervalo de tempo, como JSON estruturado. Gatilhos em pt-BR — "exporta os logs de rede desse intervalo", "pega as requisições HTTP entre HH:MM:SS e HH:MM:SS", "captura o tráfego de rede desse teste".
---

# Export Logs — Export Flutter Network Logs by Time Range

Exporta logs de rede HTTP de uma sessão Flutter debug rodando, filtrados por um intervalo de tempo, como JSON estruturado.

## Script

O script `scripts/export_network_logs.py` deste plugin conecta ao Dart VM Service Protocol via WebSocket e busca o HTTP profile filtrado por horário — mecânica padrão Flutter/Dart, não muda entre projetos.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/export_network_logs.py" <url> <start-time> <end-time> [--output PATH]
```
- `<url>`: URL WS do VM service, URL do DevTools, ou `auto` (detecta de processos Flutter rodando via `--vm-service-uri`).
- `<start-time>` / `<end-time>`: `HH:MM:SS` ou `HH:MM:SS.mmm` (hora local, hoje).
- `--output`: path de saída (default: pasta de downloads do usuário, com timestamp).

## Usage

```
/export-logs <start-time> <end-time>
```

Horários usam formato `HH:MM:SS` ou `HH:MM:SS.mmm` (hora local, hoje).

**Exemplo:**
```
/export-logs 11:11:30 11:12:10
```

## Steps

### 1. Parse arguments

Extraia `<start-time>` e `<end-time>` dos argumentos.

Se algum estiver ausente ou não bater com `HH:MM:SS` / `HH:MM:SS.mmm`, pergunte ao usuário:
> "Informe horário de início e fim no formato HH:MM:SS. Exemplo: /export-logs 11:11:30 11:12:10"

### 2. Checar dependência websocket-client

Rode:
```bash
python3 -c "import websocket"
```

Se falhar, instale:
```bash
pip3 install websocket-client
```

Depois verifique o import de novo.

### 3. Rodar o script de export

Use `auto` como URL — o script detecta a sessão Flutter rodando a partir dos argumentos do processo (`--vm-service-uri`):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/export_network_logs.py" auto "<start-time>" "<end-time>"
```

Capture stdout e stderr. O script imprime progresso no stderr (buscando cada request).

### 4. Tratar erros

- **"No running Flutter debug session found"** → peça ao usuário pra colar a URL do DevTools do Chrome, e re-rode com essa URL no lugar de `auto`:
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/export_network_logs.py" "<devtools-url>" "<start-time>" "<end-time>"
  ```

- **"No requests found in the specified time range"** → o intervalo pode estar errado. Mostre ao usuário a contagem total de requests do output e sugira ampliar o intervalo.

- **Connection refused** → o app não está mais rodando. Peça pro usuário relançar.

### 5. Reportar resultados

Mostre ao usuário:
- Número de requests exportados
- Path completo do arquivo JSON de saída
- Uma tabela breve das requisições capturadas: método, URL, status code, duração

## Important

- Horários são interpretados como hora local de hoje. Intervalos que cruzam a meia-noite não são suportados.
- Detecção `auto` de URL lê `--vm-service-uri` dos argumentos do processo `dart` rodando.
- O app precisa estar rodando em modo debug (qualquer flavor/launch de debug).
- Nunca rode o script sem argumentos de horário.
- O JSON de saída pode ser aberto em qualquer editor ou viewer de HAR (Proxyman, Insomnia).
