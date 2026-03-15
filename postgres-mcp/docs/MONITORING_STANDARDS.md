# Padrões de Monitoramento PostgreSQL MCP 🐘

## 🎯 Objetivo
Prevenir problemas de crescimento descontrolado e manter a performance do PostgreSQL, similar ao que foi implementado para Docker.

## 📊 Sistema de Monitoramento

### 1. Scripts Principais

#### pg-mcp-monitor.sh
- **Função**: Monitoramento contínuo de saúde
- **Execução**: A cada 30 minutos via cron
- **Verifica**:
  - Tamanho dos bancos de dados (alerta se > 500MB)
  - Número de conexões (alerta se > 100)
  - Queries lentas (> 5 segundos)
  - Cache hit ratio (alerta se < 90%)
  - Bloat em índices (> 20%)
  - Integração com postgres-mcp

#### pg-mcp-cleanup.sh
- **Função**: Limpeza preventiva
- **Execução**: Diária às 3:30 AM
- **Limpa**:
  - Logs antigos (> 30 dias)
  - Tabelas temporárias abandonadas
  - Cache de queries antigas
  - Arquivos WAL desnecessários
  - Relatórios antigos do postgres-mcp

#### pg-mcp-auto-maintenance.sh
- **Função**: Configurar automação
- **Configura**: Todos os cron jobs necessários

### 2. Limiares de Alerta

```bash
MAX_DB_SIZE_MB=500         # Tamanho máximo por banco
MAX_CONNECTIONS=100        # Conexões simultâneas
MAX_QUERY_TIME_MS=5000     # Tempo máximo de query (5s)
CACHE_HIT_RATIO_MIN=0.90   # Taxa mínima de cache hit
BLOAT_THRESHOLD_PERCENT=20 # Bloat máximo em índices
```

### 3. Estrutura de Logs

```
/var/log/postgres-mcp-monitoring/
├── monitor.log           # Log contínuo de monitoramento
├── cleanup.log           # Log de limpezas diárias
├── cleanup-weekly.log    # Log de limpezas semanais
├── alerts.log           # Todos os alertas gerados
├── growth-history.csv   # Histórico de crescimento
├── performance-weekly.log # Análise semanal detalhada
└── report-*.txt         # Relatórios individuais
```

## 🔧 Manutenção Automática

### Cronograma

| Horário | Frequência | Ação |
|---------|------------|------|
| */30 * * * * | A cada 30 min | Monitor de saúde |
| 30 2 * * * | Diário | Backup de configurações |
| 30 3 * * * | Diário | Limpeza básica |
| 30 4 * * 0 | Domingos | Limpeza agressiva |
| 0 22 * * 5 | Sextas | Análise detalhada |

### Ações Preventivas

1. **VACUUM Automático**
   - Executado quando dead tuples > 20% das live tuples
   - VACUUM ANALYZE em todos os bancos

2. **REINDEX Automático**
   - Quando bloat > 20% em índices grandes
   - Reindexação de bancos problemáticos

3. **Limpeza de Temporários**
   - Remove tabelas com padrão tmp_*, temp_*
   - Limpa objetos órfãos

## 📈 Monitoramento de Crescimento

### Arquivo CSV de Histórico
```csv
timestamp,database,size_mb,connections
2025-05-31T00:00:00,mcp_db,14,5
```

### Alertas Automáticos
- Email/log quando banco > 500MB
- Notificação quando muitas conexões
- Aviso sobre queries lentas persistentes

## 🛡️ Proteções Implementadas

1. **Contra Crescimento Descontrolado**
   - Monitoramento de tamanho a cada 30 min
   - Alertas precoces antes de problemas
   - Limpeza automática de temporários

2. **Contra Performance Degradada**
   - Monitoramento de cache hit ratio
   - Detecção de queries lentas
   - VACUUM e REINDEX automáticos

3. **Contra Perda de Dados**
   - Backup diário de configurações
   - Modo dry-run para testes
   - Logs detalhados de todas ações

## 🚀 Comandos Úteis

### Verificação Manual
```bash
# Monitor completo
/root/.claude/postgres-mcp/monitoring/pg-mcp-monitor.sh

# Limpeza com dry-run
/root/.claude/postgres-mcp/monitoring/pg-mcp-cleanup.sh --dry-run

# Ver últimos alertas
tail -50 /var/log/postgres-mcp-monitoring/alerts.log

# Histórico de crescimento
cat /var/log/postgres-mcp-monitoring/growth-history.csv
```

### Manutenção de Emergência
```bash
# VACUUM forçado em todos os bancos
sudo -u postgres vacuumdb --all --analyze --verbose

# Terminar queries travadas
sudo -u postgres psql -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' 
AND query_start < now() - interval '1 hour';"

# Reset de estatísticas
sudo -u postgres psql -c "SELECT pg_stat_reset();"
```

## 📝 Integração com postgres-mcp

O sistema monitora automaticamente:
- Conexão do postgres-mcp ao banco
- Credenciais em .env
- Disponibilidade do serviço

Se houver problemas, alertas são gerados em:
`/var/log/postgres-mcp-monitoring/alerts.log`

## 🎛️ Otimizações Sugeridas

Com base na RAM disponível, o sistema sugere:
- `shared_buffers`: 25% da RAM
- `effective_cache_size`: 75% da RAM
- `maintenance_work_mem`: RAM/16

## ⚡ Performance Dashboard

Integrado com o dashboard Docker em:
- http://195.35.19.73:8090/postgresql/
- Métricas em tempo real
- Histórico de crescimento
- Alertas visuais

---

**Última atualização**: $(date)
**Sistema**: PostgreSQL MCP Monitoring v1.0