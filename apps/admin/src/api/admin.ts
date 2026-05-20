import client from './client'

// --- Dashboard ---
export function getDashboard() {
  return client.get('/admin/dashboard')
}

// --- Users ---
export interface UserQuery {
  page?: number
  page_size?: number
  q?: string
  role?: string
}
export function listUsers(params?: UserQuery) {
  return client.get('/admin/users', { params })
}
export function getUserDetail(userId: string) {
  return client.get(`/admin/users/${userId}`)
}
export function updateUser(userId: string, data: Record<string, unknown>) {
  return client.patch(`/admin/users/${userId}`, data)
}

// --- Orders ---
export interface OrderQuery {
  page?: number
  page_size?: number
  q?: string
  status?: string
}
export function listOrders(params?: OrderQuery) {
  return client.get('/admin/orders', { params })
}

// --- Diagnoses ---
export interface DiagnosisQuery {
  page?: number
  page_size?: number
  q?: string
}
export function listDiagnoses(params?: DiagnosisQuery) {
  return client.get('/admin/diagnoses', { params })
}
export function getDiagnosisDetail(id: string) {
  return client.get(`/admin/diagnoses/${id}`)
}

// --- Products ---
export function listProducts() {
  return client.get('/subscriptions/products')
}
export function createProduct(data: Record<string, unknown>) {
  return client.post('/subscriptions/products', data)
}
export function updateProduct(id: string, data: Record<string, unknown>) {
  return client.patch(`/subscriptions/products/${id}`, data)
}
export function deleteProduct(id: string) {
  return client.delete(`/subscriptions/products/${id}`)
}

// --- Subscriptions ---
export interface SubQuery {
  page?: number
  page_size?: number
  status?: string
}
export function listSubscriptions(params?: SubQuery) {
  return client.get('/admin/subscriptions', { params })
}

// --- Coupons ---
export function listCoupons(params?: { page?: number; page_size?: number }) {
  return client.get('/admin/coupons', { params })
}
export function createCoupon(data: Record<string, unknown>) {
  return client.post('/admin/coupons', data)
}

// --- Referrers ---
export function listReferrers(params?: { page?: number; page_size?: number }) {
  return client.get('/admin/referrers', { params })
}
export function flagReferrer(id: string, data?: { reason?: string }) {
  return client.post(`/admin/referrers/${id}/flag`, data || {})
}
export function freezeReferrer(id: string) {
  return client.post(`/admin/referrers/${id}/freeze`)
}
export function unfreezeReferrer(id: string) {
  return client.post(`/admin/referrers/${id}/unfreeze`)
}

// --- Order actions ---
export function refundOrder(orderId: string) {
  return client.post(`/admin/orders/${orderId}/refund`)
}

// --- Diagnosis actions ---
export function rerunDiagnosis(diagnosisId: string) {
  return client.post(`/admin/diagnoses/${diagnosisId}/rerun`)
}

// --- Auth ---
export function login(data: { phone: string; password: string }) {
  return client.post('/auth/login', data)
}
export function getMe() {
  return client.get('/auth/me')
}
