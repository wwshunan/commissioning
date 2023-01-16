import axios from 'axios'
import { MessageBox, Message } from 'element-ui'
import store from '@/store'
import { getAccessToken, getRefreshToken } from '@/utils/auth'
import router from '@/router'


//axios.defaults.baseURL = "http://192.168.6.104:5000";
axios.defaults.baseURL = "http://127.0.0.1:5000";
// create an axios instance
const service = axios.create({
  //baseURL: 'http://192.168.6.104:5000', // url = base url + request url
  baseURL: 'http://127.0.0.1:5000', // url = base url + request url
  // withCredentials: true, // send cookies when cross-domain requests
  timeout: 80000 // request timeout
})

// request interceptor
service.interceptors.request.use(
  config => {
    // do something before request is sent
    let token
    if (config.url === "/admin/user/refresh-token") {
      if (store.getters.refresh_token) {
        token = getRefreshToken()
      } else {
        return Promise.reject(new Error("refresh token is empty"))
      }
    } else if (store.getters.access_token) {
      token = getAccessToken()
      // let each request carry token
      // ['X-Token'] is a custom headers key
      // please modify it according to the actual situation
    }
    config.headers['Authorization'] = 'Bearer ' + token
    return config
  },
    error => {
      // do something with request error
      console.log(error) // for debug
    return Promise.reject(error)
  }
)

// response interceptor
service.interceptors.response.use(
  /**
   * If you want to get http information such as headers or status
   * Please return  response => response
  */

  /**
   * Determine the request status by custom code
   * Here is just an example
   * You can also judge the status by HTTP Status Code
   */
  response => {
    const res = response.data
    // if the custom code is not 20000, it is judged as an error.
    if (res.code !== 20000) {
	  if (res.code !== 600) {
        Message({
          message: res.message || 'Error',
          type: 'error',
          duration: 5 * 1000
        })			
	  }


      // 50008: Illegal token; 50012: Other clients logged in; 50014: Token expired;
      if (res.code === 50008 || res.code === 50012 || res.code === 50014) {
        // to re-login
        MessageBox.confirm('You have been logged out, you can cancel to stay on this page, or log in again', 'Confirm logout', {
          confirmButtonText: 'Re-Login',
          cancelButtonText: 'Cancel',
          type: 'warning'
        }).then(() => {
          store.dispatch('user/resetToken').then(() => {
            location.reload()
          })
        })
      }
      return Promise.reject(new Error(res.message || 'Error'))
    } else {
      return res
    }
  },
  async error => {
    if (error.response === undefined || error.response.status !== 401) {
      Message({
        message: error.response.data.detail,
        type: 'error',
        duration: 5 * 1000
      })
      return Promise.reject(error)
    }
    if (error.config.url === '/admin/user/refresh-token') {
      //store.dispatch('user/refreshToken')
      try {
        await store.dispatch('user/resetToken')
        router.push('/login')
        Message({
          message: error.response.data.detail,
          type: 'error',
          duration: 5 * 1000
        })
      } catch(error)  {
        return Promise.reject(error)
      }
      return Promise.reject(error)
    }
    if (error.response.data.detail === "Token expired") {
        try {
          const refresh_token = getRefreshToken()
          const rs = await axios.get('/admin/user/refresh-token', {
            headers: {'Authorization': 'Bearer ' + refresh_token }
          })
          const { access_token } = rs.data
          store.dispatch('user/refreshToken', access_token);
          return service(error.config)
        } catch (_error) {
          console.log(_error)
        }
    } else {
      return Promise.reject(error)
    }
  }
)

export default service
