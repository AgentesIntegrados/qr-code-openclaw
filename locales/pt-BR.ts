export default {
  common: {
    loading: "Carregando...",
    error: "Erro",
    next: "Próximo Passo",
    cancel: "Cancelar",
    all: "Todas",
    selected: "selecionadas"
  },
  instances: {
    title: "Seleção de Instâncias",
    subtitle: "Escolha as instâncias para o disparo em massa",
    filters: {
      all: "Todas",
      baileys: "Baileys",
      business: "Business"
    },
    status: {
      error: {
        title: "Erro ao carregar instâncias",
        unknown: "Erro desconhecido",
        incomplete_config: "Configuração incompleta"
      }
    },
    selection: {
      count: "{selected} de {total} instâncias selecionadas",
      select_all: "Selecionar todas",
      deselect_all: "Desmarcar todas"
    },
    instance: {
      type: {
        baileys: "Baileys",
        business: "Business"
      }
    },
    buttons: {
      next: "Próximo Passo"
    },
    errors: {
      fetch: "Erro ao carregar instâncias. Por favor, tente novamente."
    },
    search_placeholder: "Digite para pesquisar instâncias..."
  },
  contacts: {
    title: "Entrada de Contatos",
    subtitle: "Adicione seus contatos para iniciar o disparo em massa",
    tabs: {
      manual: "Entrada Manual",
      csv: "Importar CSV"
    },
    upload: {
      title: "Clique para fazer upload do CSV ou arraste e solte aqui",
      button: "Baixar CSV de Exemplo"
    },
    manual: {
      placeholder: "Digite os contatos (um por linha)\n\nExemplo:\n5511999999999, Nome, Valor 1, Valor 2, Valor 3, Valor 4, Valor 5\n5511999999999, Nome, Valor 1, Valor 2, Valor 3, Valor 4, Valor 5"
    },
    status: {
      contacts_count: "{count} contatos inseridos"
    },
    buttons: {
      next: "Próximo Passo"
    }
  },
  message: {
    title: "Composição da Mensagem",
    subtitle: "Configure sua mensagem para o disparo em massa",
    form: {
      message: "Mensagem",
      message_placeholder: "Digite sua mensagem...\n\nVocê pode usar variáveis como:\n[name] - Nome do contato\n[value1] - Valor personalizado 1\n[value2] - Valor personalizado 2",
      delay: "Intervalo entre mensagens",
      delay_help: "Tempo de espera entre cada mensagem (em segundos)",
      media: {
        title: "Mídia",
        button: "Selecionar arquivo",
        selected: "Arquivo selecionado:",
        remove: "Remover",
        help: "Formatos suportados: jpg, jpeg, png, gif, pdf, mp4"
      }
    },
    preview: {
      title: "Pré-visualização",
      subtitle: "Veja como sua mensagem será exibida",
      sample_contact: "Contato de exemplo"
    },
    chatwoot: {
      title: "Configurações do Chatwoot",
      subtitle: "Configure as opções de integração",
      agents: {
        button: "Selecionar Agentes",
        title: "Atribuição de Agentes",
        subtitle: "Selecione os agentes para atribuição automática",
        empty: "Nenhum agente disponível",
        buttons: {
          cancel: "Cancelar",
          save: "Salvar Seleção"
        },
        count: "{count} Agente | {count} Agentes"
      },
      labels: {
        button: "Selecionar Marcadores",
        title: "Marcadores",
        subtitle: "Selecione os marcadores para atribuição automática",
        count: "{count} Marcador | {count} Marcadores",
        empty: "Nenhum marcador disponível",
        empty_subtitle: "Verifique a conexão com o banco de dados do Chatwoot",
        buttons: {
          cancel: "Cancelar",
          save: "Salvar Seleção"
        }
      }
    },
    typebot: {
      button: "Configurar Typebot",
      title: "Configuração do Typebot",
      subtitle: "Configure a integração com o Typebot"
    },
    status: {
      ready: "Pronto para iniciar",
      contacts_count: "{count} contatos serão processados"
    },
    buttons: {
      start: "Iniciar Disparo",
      cancel: "Cancelar"
    }
  },
  message_composition: {
    title: "Composição da Mensagem",
    subtitle: "Escreva sua mensagem e configure o disparo",
    form: {
      message: "Mensagem:",
      message_placeholder: "Digite sua mensagem aqui...",
      available_variables: "{count} variáveis disponíveis",
      available_variables_count: "Variáveis ({count})",
      add_template: "Adicionar Template",
      template_label: "Template",
      media: {
        title: "Enviar imagem ou vídeo",
        select_file: "Selecionar arquivo",
        file_selected: "Arquivo selecionado"
      },
      typebot: {
        title: "Configuração do Typebot",
        url: {
          label: "URL do Bot",
          placeholder: "https://bot.oriondesign.art.br",
          error: "Por favor, insira uma URL válida"
        },
        flow: {
          label: "ID do Fluxo",
          placeholder: "fluxo-tal-w1902a",
          error: "ID do Fluxo é obrigatório"
        },
        buttons: {
          cancel: "Cancelar",
          save: "Salvar Configuração"
        },
        button: "Iniciar Typebot",
        added: "Bot adicionado"
      },
      agents: {
        title: "Selecionar Agentes",
        button: "Selecionar Agentes",
        count: "{count} Agente | {count} Agentes",
        selected: "Agentes"
      },
      labels: {
        title: "Selecionar Marcadores",
        button: "Selecionar Marcadores",
        count: "{count} Marcador | {count} Marcadores",
        selected: "marcadores selecionados"
      },
      timing: {
        min_time: "Tempo Mínimo (segundos)",
        max_time: "Tempo Máximo (segundos)"
      }
    },
    errors: {
      invalid_url: "Por favor, insira uma URL válida para o bot",
      file_upload: "Erro ao fazer upload do arquivo",
      unsupported_format: "Formato de arquivo não suportado. Apenas PNG, JPG, JPEG, MP4 e PDF são permitidos.",
      template_limit: "Você pode adicionar no máximo 3 templates de mensagem"
    },
    buttons: {
      send: "Disparar Mensagens"
    },
    variables: {
      help_text: "Variáveis disponíveis (clique para inserir):"
    }
  },
  progress: {
    title: "Progresso do Disparo",
    status: {
      starting: "🚀 Iniciando disparo...",
      waiting: "⏸️ Esperando {seconds} segundos...",
      sending: "📱 Enviando mensagem para {phone}...",
      retry: "⚠️ Tentativa {attempt}/3 de enviar mensagem para {phone}...",
      media_success: "✅ Mídia enviada com sucesso para {phone}",
      message_success: "✅ Mensagem enviada com sucesso para {phone}",
      chatwoot_start: "🤖 Iniciando processo no Chatwoot...",
      chatwoot_sync: "⏳ Sincronizando com o chatwoot...",
      chatwoot_agent: "👤 Atribuindo conversa ao agente {name}...",
      chatwoot_labels: "🏷️ Atribuindo {count} marcador{plural}...",
      chatwoot_complete: "✅ Processo Chatwoot concluído",
      canceled: "🚫 Disparo cancelado",
      completed: "✨ Disparo finalizado",
      error: "❌ Erro ao iniciar disparo"
    },
    stats: {
      pending: "Pendentes",
      sent: "Enviadas",
      errors: "Erros",
      total: "Total"
    },
    summary: {
      title: "Resumo do Disparo",
      canceled_title: "Disparo Cancelado",
      total_messages: "Total de mensagens",
      sent_messages: "Mensagens enviadas com sucesso",
      error_messages: "Mensagens com erro",
      unsent_messages: "Mensagens não enviadas",
      success_rate: "Taxa de sucesso"
    },
    buttons: {
      cancel: "Cancelar Disparo",
      new: "Novo Disparo",
      download: "Baixar Relatório CSV"
    },
    report: {
      title: "RELATÓRIO DO DISPARO",
      instances: {
        title: "INSTÂNCIAS SELECIONADAS",
        type: {
          baileys: "📱 Baileys",
          business: "✓ Business"
        }
      },
      data: {
        title: "DADOS DO DISPARO",
        total_contacts: "Total de Contatos",
        variables_found: "Variáveis Encontradas"
      },
      content: {
        title: "CONTEÚDO",
        template: "Template",
        no_template: "Nenhum template definido"
      },
      media: {
        title: "MÍDIA",
        status: "Status",
        status_values: {
          yes: "Sim",
          no: "Não"
        },
        file: "Arquivo",
        type: "Tipo"
      },
      typebot: {
        title: "TYPEBOT",
        status: "Status",
        url: "URL",
        bot: "Bot"
      },
      timing: {
        title: "CONFIGURAÇÃO DE TEMPO",
        min: "Mínimo",
        max: "Máximo",
        seconds: "segundos"
      },
      csv: {
        filename: "relatorio-disparo",
        phone: "Número",
        status: "Status",
        instance: "Instância",
        template: "Template",
        message: "Mensagem",
        sent_at: "Enviado em",
        agent: "Agente",
        labels: "Marcadores"
      }
    }
  }
}