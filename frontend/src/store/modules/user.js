import { login, logout, getInfo } from '@/api/user'
import { getAccessToken, getRefreshToken,
  setToken, removeToken, setAccessToken } from '@/utils/auth'
import { resetRouter } from '@/router'

const getDefaultState = () => {
  return {
    access_token: getAccessToken(),
    refresh_token: getRefreshToken(),
    name: '',
    avatar: '',
    roles: []
  }
}

const state = getDefaultState()

const mutations = {
  RESET_STATE: (state) => {
    Object.assign(state, getDefaultState())
  },
  SET_TOKEN: (state, {access_token, refresh_token}) => {
    state.access_token = access_token
    state.refresh_token = refresh_token
  },
  REFRESH_TOKEN: (state, access_token) => {
      state.access_token = access_token
  },
  SET_NAME: (state, name) => {
    state.name = name
  },
  SET_AVATAR: (state, avatar) => {
    state.avatar = avatar
  },
  SET_ROLES: (state, roles) => {
    state.roles = roles
  }
}

const actions = {
  // user login
  login({ commit }, userInfo) {
    const { email, password } = userInfo
    return new Promise((resolve, reject) => {
      login({ email: email.trim(), password: password }).then(response => {
        let { access_token, refresh_token } = response
        commit('SET_TOKEN', { access_token, refresh_token })
        setToken(access_token, refresh_token)
        resolve()
      }).catch(error => {
        reject(error)
      })
    })
  },

  // get user info
  getInfo({ commit, state }) {
    return new Promise((resolve, reject) => {
      getInfo(state.access_token).then(response => {
        const { roles, name, avatar } = response



        // roles must be a non-empty array
        if (!roles || roles.length <= 0) {
          reject('getInfo: roles must be a non-null array!')
        }

        commit('SET_ROLES', roles)
        commit('SET_NAME', name)
        commit('SET_AVATAR', avatar)
        resolve(roles)

      }).catch(error => {
        reject(error)
      })
    })
  },

  // user logout
  logout({ commit, state }) {
    return new Promise((resolve, reject) => {
      logout(state.token).then(() => {
        removeToken() // must remove  token  first
        resetRouter()
        commit('RESET_STATE')
        resolve()
      }).catch(error => {
        reject(error)
      })
    })
  },

  // remove token
  resetToken({ commit }) {
    return new Promise(resolve => {
      removeToken() // must remove  token  first
      commit('RESET_STATE')
      resolve()
    })
  },

  async refreshToken({ commit }, access_token) {
      try {
        commit('REFRESH_TOKEN', access_token);
        setAccessToken(access_token)
        return access_token
      } catch (error) {
        console.log(error)
    }
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}

