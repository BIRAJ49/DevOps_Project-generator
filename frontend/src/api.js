const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL

const API_BASE_URL = (
  rawApiBaseUrl === undefined ? 'http://127.0.0.1:8000' : rawApiBaseUrl
).replace(/\/$/, '')

async function request(path, options = {}) {
  const { token, headers: inputHeaders, ...rest } = options
  const headers = new Headers(inputHeaders || {})

  if (rest.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers,
  })

  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const detail =
      typeof payload === 'object' && payload !== null
        ? payload.detail || payload.message || 'Request failed'
        : payload || 'Request failed'
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }

  return payload
}

function buildApiUrl(path) {
  return `${API_BASE_URL}${path}`
}

export { API_BASE_URL, buildApiUrl, request }
