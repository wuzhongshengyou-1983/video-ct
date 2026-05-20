import client from './client'

// --- Auth ---
export function login(data: { phone: string; password: string }) {
  return client.post('/auth/login', data)
}
export function getMe() {
  return client.get('/auth/me')
}

// --- Clients ---
export interface ClientQuery {
  page?: number
  page_size?: number
  q?: string
  track?: string
  level?: string
}
export function listClients(params?: ClientQuery) {
  return client.get('/consultant/clients', { params })
}
export function getClientDetail(clientId: string) {
  return client.get(`/consultant/clients/${clientId}`)
}
export function getClientDiagnoses(clientId: string) {
  return client.get(`/consultant/clients/${clientId}/diagnoses`)
}
export function getClientGaps(clientId: string) {
  return client.get(`/consultant/clients/${clientId}/gaps`)
}
export function saveConsultantNote(clientId: string, data: { note: string }) {
  return client.post(`/consultant/clients/${clientId}/notes`, data)
}

// --- Reviews ---
export function listReviews(params?: { page?: number; page_size?: number; status?: string }) {
  return client.get('/consultant/reviews', { params })
}
export function submitReview(diagnosisId: string, data: Record<string, unknown>) {
  return client.post(`/consultant/reviews/${diagnosisId}`, data)
}

// --- Meetings ---
export function listMeetings(params?: { page?: number; page_size?: number }) {
  return client.get('/consultant/meetings', { params })
}

// --- Client Persona & Positioning ---
export function getClientPersona(clientId: string) {
  return client.get(`/consultant/clients/${clientId}/persona`)
}
export function getClientPositioning(clientId: string) {
  return client.get(`/consultant/clients/${clientId}/positioning`)
}
export function getClientArchive(clientId: string) {
  return client.get(`/consultant/clients/${clientId}/archive`)
}

// --- Reviews ---
export function listReviews(params?: { page?: number; page_size?: number; status?: string }) {
  return client.get('/consultant/reviews', { params })
}
export function submitReview(diagnosisId: string, data: Record<string, unknown>) {
  return client.post(`/consultant/reviews/${diagnosisId}`, data)
}

// --- Meetings ---
export function listMeetings(params?: { page?: number; page_size?: number }) {
  return client.get('/consultant/meetings', { params })
}
export function createMeeting(data: {
  client_id: string
  title: string
  scheduled_at: string
  meeting_type?: string
  location?: string
  notes?: string
}) {
  return client.post('/consultant/meetings', data)
}

// --- Alerts ---
export function listAlerts(params?: { page?: number; page_size?: number }) {
  return client.get('/consultant/alerts', { params })
}
export function acknowledgeAlert(alertId: string) {
  return client.post(`/consultant/alerts/${alertId}/acknowledge`)
}
export function dismissAlert(alertId: string) {
  return client.post(`/consultant/alerts/${alertId}/dismiss`)
}

// --- Tickets ---
export function listTickets(params?: { page?: number; page_size?: number; status?: string }) {
  return client.get('/consultant/tickets', { params })
}
export function createTicket(data: {
  title: string
  description?: string
  client_id?: string
  priority?: string
}) {
  return client.post('/consultant/tickets', data)
}
