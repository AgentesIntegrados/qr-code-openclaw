# Padrões e Boas Práticas - PostgreSQL MCP 🐘

## 📋 Visão Geral

Este documento define os padrões e boas práticas para uso do PostgreSQL com o postgres-mcp, garantindo segurança, performance e prevenção de problemas de crescimento descontrolado.

## 🔐 Segurança

### 1. Credenciais e Acesso
- **NUNCA** commitar credenciais no git
- Usar sempre arquivo `.env` para configurações sensíveis
- Rotacionar senhas a cada 90 dias
- Usar conexões SSL quando possível

### 2. Permissões Mínimas
```sql
-- Criar usuário com permissões específicas
CREATE USER app_user WITH PASSWORD 'senha_forte';
GRANT CONNECT ON DATABASE app_db TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
```

### 3. Modo de Acesso
- Usar `ACCESS_MODE=readonly` para ambientes de produção
- Usar `ACCESS_MODE=unrestricted` apenas em desenvolvimento

## 📏 Limites e Thresholds

### Tamanhos Máximos Recomendados
- **Banco de dados individual**: 500MB (alerta em 400MB)
- **Tabela individual**: 100MB
- **Índice individual**: 50MB
- **Total de conexões**: 100 (alerta em 80)
- **Duração máxima de query**: 5 segundos

### Ações Automáticas
- **> 500MB**: Alerta crítico + análise de tabelas grandes
- **> 1GB**: Bloqueio preventivo + notificação urgente
- **> 100 conexões**: Análise de conexões por aplicação
- **Query > 5s**: Log e possível cancelamento

## 🧹 Manutenção Preventiva

### Rotinas Diárias (3:30 AM)
1. **VACUUM ANALYZE** em todas as tabelas
2. Limpeza de logs > 30 dias
3. Verificação de tabelas temporárias
4. Reset de estatísticas antigas

### Rotinas Semanais (Domingo 4:00 AM)
1. **REINDEX** em tabelas com bloat > 20%
2. Limpeza agressiva de dados temporários
3. Análise de índices não utilizados
4. Backup completo (se configurado)

### Monitoramento Contínuo (30 em 30 minutos)
1. Tamanho dos bancos
2. Número de conexões
3. Queries lentas
4. Cache hit ratio
5. Bloat em índices

## 🏗️ Padrões de Nomenclatura

### Bancos de Dados
- Produção: `prod_[nome]_db`
- Desenvolvimento: `dev_[nome]_db`
- Teste: `test_[nome]_db`

### Tabelas
- Usar snake_case: `user_accounts`, `order_items`
- Prefixos por tipo:
  - `tmp_` - temporárias (auto-limpeza)
  - `log_` - logs (rotação automática)
  - `archive_` - dados arquivados

### Índices
- Padrão: `idx_[tabela]_[colunas]`
- Exemplo: `idx_users_email`, `idx_orders_customer_id_date`

## 🚀 Performance

### Índices Essenciais
```sql
-- Sempre criar índices para:
-- 1. Chaves estrangeiras
CREATE INDEX idx_orders_customer_id ON orders(customer_id);

-- 2. Colunas usadas em WHERE frequentemente
CREATE INDEX idx_users_email ON users(email);

-- 3. Colunas usadas em ORDER BY
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
```

### Queries Otimizadas
```sql
-- BOM: Usar LIMIT em queries grandes
SELECT * FROM large_table LIMIT 1000;

-- BOM: Usar índices parciais quando apropriado
CREATE INDEX idx_orders_pending ON orders(created_at) 
WHERE status = 'pending';

-- EVITAR: SELECT * sem WHERE
-- EVITAR: JOINs sem índices
-- EVITAR: Subconsultas em loops
```

## 📊 Monitoramento

### Métricas Críticas
1. **Cache Hit Ratio**: Deve ser > 90%
2. **Conexões Idle**: Não deve exceder 50% do total
3. **Bloat**: Não deve exceder 20% em índices
4. **WAL Files**: Manter máximo de 10 arquivos

### Comandos Úteis
```bash
# Ver status atual
/root/check-postgres-mcp

# Monitoramento manual
/root/.claude/postgres-mcp/monitoring/pg-mcp-monitor.sh

# Limpeza manual
/root/.claude/postgres-mcp/monitoring/pg-mcp-cleanup.sh

# Simular limpeza (dry run)
/root/.claude/postgres-mcp/monitoring/pg-mcp-cleanup.sh --dry-run
```

## 🚨 Troubleshooting

### Banco Crescendo Rapidamente
1. Verificar tabelas de log/temporárias
2. Executar VACUUM FULL na tabela problemática
3. Verificar se há transações longas abertas
4. Revisar índices desnecessários

### Muitas Conexões
1. Identificar aplicações com pool mal configurado
2. Verificar conexões idle há muito tempo
3. Considerar pg_bouncer para pooling
4. Ajustar max_connections se necessário

### Performance Degradada
1. Verificar cache hit ratio
2. Analisar queries lentas
3. Verificar bloat em índices
4. Considerar ANALYZE nas tabelas afetadas

## 🔄 Integração com postgres-mcp

### Arquivo .env Padrão
```bash
# Configuração PostgreSQL MCP
DATABASE_URI=postgresql://user:password@localhost:5432/database
ACCESS_MODE=readonly  # ou unrestricted para dev
POOL_MIN_SIZE=1
POOL_MAX_SIZE=10
QUERY_TIMEOUT=300
```

### Verificar Integração
```bash
# No Claude, execute:
postgres_info

# Deve retornar status e configuração atual
```

## 📈 Crescimento Sustentável

### Estratégias de Prevenção
1. **Particionamento**: Para tabelas > 100MB
2. **Arquivamento**: Mover dados antigos para tabelas archive_
3. **Compressão**: Usar TOAST para campos grandes
4. **Limpeza Automática**: Scripts rodando via cron

### Exemplo de Particionamento
```sql
-- Particionar tabela de logs por mês
CREATE TABLE logs_2025_01 PARTITION OF logs
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

## 📝 Checklist de Configuração

- [ ] PostgreSQL instalado e configurado
- [ ] Usuário mcp_user criado com permissões adequadas
- [ ] Arquivo .env configurado no postgres-mcp
- [ ] Scripts de monitoramento instalados
- [ ] Cron jobs configurados
- [ ] Limites definidos nos scripts
- [ ] Dashboard acessível
- [ ] Alertas configurados (opcional)

## 🆘 Suporte

- Logs: `/var/log/postgres-mcp-monitoring/`
- Dashboard: `http://servidor:8090/`
- Documentação: `/root/.claude/postgres-mcp/POSTGRES-MCP-DOCS.md`

---

**Última atualização**: $(date)
**Versão**: 1.0