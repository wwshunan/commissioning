import request from '@/utils/request'

export function login(data) {
  return request({
    url: '/admin/user/login',
    method: 'post',
    data
  })
}

export function register(data) {
  return request({
    url: '/admin/user/register',
    method: 'post',
    data
  })
}

export function send_verify_code(data) {
  return request({
    url: '/admin/user/verify-code',
    method: 'post',
    data
  })
}

export function getInfo(token) {
  return request({
    url: '/admin/user/info',
    method: 'get',
    params: { token }
  })
}

export function logout() {
  return request({
    url: '/admin/user/logout',
    method: 'post'
  })
}
