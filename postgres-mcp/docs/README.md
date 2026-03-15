# Documentação Legada do PostgreSQL MCP

Este diretório contém documentação histórica importante do projeto postgres-mcp, preservada para referência futura.

## Arquivos Preservados

### 1. POSTGRES-MCP-DOCS.md
- **Conteúdo**: Documentação técnica completa v0.3.0
- **Útil para**: Entender arquitetura interna, estrutura de módulos
- **480 linhas** de documentação detalhada

### 2. POSTGRESQL_MCP_STANDARDS.md  
- **Conteúdo**: Padrões e boas práticas PostgreSQL
- **Útil para**: Limites de segurança, thresholds, nomenclaturas
- **Inclui**: Checklist de configuração, limites de tamanho

### 3. MONITORING_STANDARDS.md
- **Conteúdo**: Sistema de monitoramento automatizado
- **Útil para**: Scripts de manutenção, comandos de emergência
- **Inclui**: Otimizações baseadas em RAM, estrutura de logs

## Quando Consultar

- **Problemas de performance**: Ver MONITORING_STANDARDS.md
- **Limites e configurações**: Ver POSTGRESQL_MCP_STANDARDS.md  
- **Arquitetura e módulos**: Ver POSTGRES-MCP-DOCS.md

## Nota

Estes documentos foram preservados da limpeza de 31/05/2025. A implementação atual usa uma versão simplificada, mas estes documentos contêm detalhes técnicos que podem ser úteis para implementações futuras ou resolução de problemas complexos.
