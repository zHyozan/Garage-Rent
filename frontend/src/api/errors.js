const fields = { email: 'E-mail', username: 'Usuário', password: 'Senha', re_password: 'Confirmação da senha', start_at: 'Início', end_at: 'Fim' }

export function apiError(error, fallback = 'Não foi possível concluir. Tente novamente.') {
  if (!error.response) return 'Não foi possível conectar ao servidor. Verifique sua conexão e se o servidor está iniciado.'
  if (error.response.status >= 500) return 'O servidor está temporariamente indisponível. Tente novamente em instantes.'
  if (error.response.status === 429) return 'Muitas tentativas. Aguarde antes de tentar novamente.'
  const data = error.response.data
  if (!data || typeof data !== 'object') return fallback
  return Object.entries(data).flatMap(([field, messages]) => (Array.isArray(messages) ? messages : [messages])
    .filter((message) => typeof message === 'string')
    .map((message) => `${fields[field] ? `${fields[field]}: ` : ''}${message}`)).join(' ') || fallback
}
