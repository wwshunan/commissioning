import Cookies from 'js-cookie'

const AccessTokenKey = 'ciads_access_token'
const RefreshTokenKey = 'ciads_refresh_token'

export function getAccessToken() {
  return Cookies.get(AccessTokenKey)
}

export function getRefreshToken() {
  return Cookies.get(RefreshTokenKey)
}

export function setToken(access_token, refresh_token) {
  Cookies.set(AccessTokenKey, access_token)
  Cookies.set(RefreshTokenKey, refresh_token)
}

export function setAccessToken(access_token) {
  Cookies.set(AccessTokenKey, access_token)
}

export function removeToken() {
  Cookies.remove(AccessTokenKey)
  Cookies.remove(RefreshTokenKey)
}

