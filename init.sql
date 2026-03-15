-- Criar schema para o Disparador
CREATE SCHEMA IF NOT EXISTS disparador;

-- Tabela de histórico de disparos
CREATE TABLE IF NOT EXISTS disparador.disparos (
    id SERIAL PRIMARY KEY,
    nome_campanha VARCHAR(255) NOT NULL,
    instancia VARCHAR(100) NOT NULL,
    total_contatos INTEGER NOT NULL,
    contatos_enviados INTEGER DEFAULT 0,
    contatos_erro INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'em_andamento',
    mensagem TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finalizado_em TIMESTAMP,
    usuario VARCHAR(100)
);

-- Tabela de contatos
CREATE TABLE IF NOT EXISTS disparador.contatos (
    id SERIAL PRIMARY KEY,
    disparo_id INTEGER REFERENCES disparador.disparos(id) ON DELETE CASCADE,
    numero VARCHAR(20) NOT NULL,
    nome VARCHAR(255),
    variavel1 VARCHAR(255),
    variavel2 VARCHAR(255),
    variavel3 VARCHAR(255),
    variavel4 VARCHAR(255),
    variavel5 VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pendente',
    erro_mensagem TEXT,
    enviado_em TIMESTAMP,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de mensagens enviadas
CREATE TABLE IF NOT EXISTS disparador.mensagens (
    id SERIAL PRIMARY KEY,
    disparo_id INTEGER REFERENCES disparador.disparos(id) ON DELETE CASCADE,
    contato_id INTEGER REFERENCES disparador.contatos(id) ON DELETE CASCADE,
    instancia VARCHAR(100) NOT NULL,
    numero VARCHAR(20) NOT NULL,
    mensagem TEXT NOT NULL,
    tipo VARCHAR(50) DEFAULT 'texto',
    media_url TEXT,
    status VARCHAR(50) DEFAULT 'enviado',
    resposta_api TEXT,
    enviado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lido_em TIMESTAMP
);

-- Tabela de templates
CREATE TABLE IF NOT EXISTS disparador.templates (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    mensagem TEXT NOT NULL,
    variaveis TEXT[],
    tipo VARCHAR(50) DEFAULT 'texto',
    media_url TEXT,
    ativo BOOLEAN DEFAULT true,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de configurações
CREATE TABLE IF NOT EXISTS disparador.configuracoes (
    id SERIAL PRIMARY KEY,
    chave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT,
    tipo VARCHAR(50),
    descricao TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhor performance
CREATE INDEX idx_disparos_status ON disparador.disparos(status);
CREATE INDEX idx_disparos_criado_em ON disparador.disparos(criado_em);
CREATE INDEX idx_contatos_disparo_id ON disparador.contatos(disparo_id);
CREATE INDEX idx_contatos_numero ON disparador.contatos(numero);
CREATE INDEX idx_contatos_status ON disparador.contatos(status);
CREATE INDEX idx_mensagens_disparo_id ON disparador.mensagens(disparo_id);
CREATE INDEX idx_mensagens_numero ON disparador.mensagens(numero);
CREATE INDEX idx_mensagens_enviado_em ON disparador.mensagens(enviado_em);

-- Inserir configurações padrão
INSERT INTO disparador.configuracoes (chave, valor, tipo, descricao) VALUES
    ('delay_entre_mensagens', '5000', 'integer', 'Delay em milissegundos entre cada mensagem'),
    ('max_tentativas', '3', 'integer', 'Número máximo de tentativas de envio'),
    ('timeout_conexao', '30000', 'integer', 'Timeout de conexão em milissegundos'),
    ('salvar_historico', 'true', 'boolean', 'Salvar histórico de disparos no banco')
ON CONFLICT (chave) DO NOTHING;

-- Função para atualizar timestamp
CREATE OR REPLACE FUNCTION disparador.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para atualizar timestamp
CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON disparador.templates
    FOR EACH ROW EXECUTE FUNCTION disparador.update_updated_at_column();

CREATE TRIGGER update_configuracoes_updated_at BEFORE UPDATE ON disparador.configuracoes
    FOR EACH ROW EXECUTE FUNCTION disparador.update_updated_at_column();

-- Permissões
GRANT ALL PRIVILEGES ON SCHEMA disparador TO disparador_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA disparador TO disparador_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA disparador TO disparador_user;