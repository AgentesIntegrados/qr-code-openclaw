import { Pool } from 'pg'

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
})

export default pool

// Tipos para as tabelas
export interface Disparo {
  id?: number
  nome_campanha: string
  instancia: string
  total_contatos: number
  contatos_enviados?: number
  contatos_erro?: number
  status?: string
  mensagem?: string
  criado_em?: Date
  finalizado_em?: Date
  usuario?: string
}

export interface Contato {
  id?: number
  disparo_id: number
  numero: string
  nome?: string
  variavel1?: string
  variavel2?: string
  variavel3?: string
  variavel4?: string
  variavel5?: string
  status?: string
  erro_mensagem?: string
  enviado_em?: Date
  criado_em?: Date
}

export interface Mensagem {
  id?: number
  disparo_id: number
  contato_id: number
  instancia: string
  numero: string
  mensagem: string
  tipo?: string
  media_url?: string
  status?: string
  resposta_api?: string
  enviado_em?: Date
  lido_em?: Date
}

export interface Template {
  id?: number
  nome: string
  mensagem: string
  variaveis?: string[]
  tipo?: string
  media_url?: string
  ativo?: boolean
  criado_em?: Date
  atualizado_em?: Date
}

// Funções helper para operações no banco
export const db = {
  // Criar novo disparo
  async criarDisparo(disparo: Disparo): Promise<number> {
    const { rows } = await pool.query(
      `INSERT INTO disparador.disparos 
       (nome_campanha, instancia, total_contatos, mensagem, usuario, status) 
       VALUES ($1, $2, $3, $4, $5, 'iniciado') 
       RETURNING id`,
      [disparo.nome_campanha, disparo.instancia, disparo.total_contatos, disparo.mensagem, disparo.usuario]
    )
    return rows[0].id
  },

  // Atualizar status do disparo
  async atualizarDisparo(id: number, updates: Partial<Disparo>): Promise<void> {
    const campos = []
    const valores = []
    let contador = 1

    Object.entries(updates).forEach(([campo, valor]) => {
      if (valor !== undefined) {
        campos.push(`${campo} = $${contador}`)
        valores.push(valor)
        contador++
      }
    })

    valores.push(id)
    
    await pool.query(
      `UPDATE disparador.disparos SET ${campos.join(', ')} WHERE id = $${contador}`,
      valores
    )
  },

  // Adicionar contato
  async adicionarContato(contato: Contato): Promise<number> {
    const { rows } = await pool.query(
      `INSERT INTO disparador.contatos 
       (disparo_id, numero, nome, variavel1, variavel2, variavel3, variavel4, variavel5) 
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8) 
       RETURNING id`,
      [
        contato.disparo_id,
        contato.numero,
        contato.nome,
        contato.variavel1,
        contato.variavel2,
        contato.variavel3,
        contato.variavel4,
        contato.variavel5
      ]
    )
    return rows[0].id
  },

  // Registrar mensagem enviada
  async registrarMensagem(mensagem: Mensagem): Promise<void> {
    await pool.query(
      `INSERT INTO disparador.mensagens 
       (disparo_id, contato_id, instancia, numero, mensagem, tipo, media_url, status, resposta_api) 
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
      [
        mensagem.disparo_id,
        mensagem.contato_id,
        mensagem.instancia,
        mensagem.numero,
        mensagem.mensagem,
        mensagem.tipo || 'texto',
        mensagem.media_url,
        mensagem.status || 'enviado',
        mensagem.resposta_api
      ]
    )
  },

  // Atualizar status do contato
  async atualizarStatusContato(id: number, status: string, erro?: string): Promise<void> {
    await pool.query(
      `UPDATE disparador.contatos 
       SET status = $1, erro_mensagem = $2, enviado_em = CURRENT_TIMESTAMP 
       WHERE id = $3`,
      [status, erro, id]
    )
  },

  // Buscar disparos recentes
  async buscarDisparosRecentes(limite = 10): Promise<Disparo[]> {
    const { rows } = await pool.query(
      `SELECT * FROM disparador.disparos 
       ORDER BY criado_em DESC 
       LIMIT $1`,
      [limite]
    )
    return rows
  },

  // Buscar templates
  async buscarTemplates(): Promise<Template[]> {
    const { rows } = await pool.query(
      `SELECT * FROM disparador.templates 
       WHERE ativo = true 
       ORDER BY nome`
    )
    return rows
  },

  // Salvar template
  async salvarTemplate(template: Template): Promise<number> {
    const { rows } = await pool.query(
      `INSERT INTO disparador.templates 
       (nome, mensagem, variaveis, tipo, media_url) 
       VALUES ($1, $2, $3, $4, $5) 
       RETURNING id`,
      [
        template.nome,
        template.mensagem,
        template.variaveis,
        template.tipo || 'texto',
        template.media_url
      ]
    )
    return rows[0].id
  },

  // Estatísticas do disparo
  async obterEstatisticas(disparo_id: number): Promise<any> {
    const { rows } = await pool.query(
      `SELECT 
        d.*,
        COUNT(DISTINCT c.id) as total_contatos_processados,
        COUNT(DISTINCT CASE WHEN c.status = 'enviado' THEN c.id END) as sucesso,
        COUNT(DISTINCT CASE WHEN c.status = 'erro' THEN c.id END) as erro
       FROM disparador.disparos d
       LEFT JOIN disparador.contatos c ON d.id = c.disparo_id
       WHERE d.id = $1
       GROUP BY d.id`,
      [disparo_id]
    )
    return rows[0]
  }
}