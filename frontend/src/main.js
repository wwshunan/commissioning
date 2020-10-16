import Vue from 'vue'
import App from './App.vue'
import './registerServiceWorker'
import router from './router'
import store from './store'
import '@fortawesome/fontawesome-free/css/all.css'
import '@fortawesome/fontawesome-free/js/all.js'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import VueSideBarMenu from 'vue-sidebar-menu'
import 'vue-sidebar-menu/dist/vue-sidebar-menu.css'
import 'vue-datetime/dist/vue-datetime.css'
import { BootstrapVue, IconsPlugin } from 'bootstrap-vue'
import FlashMessage from '@smartweb/vue-flash-message';

Vue.config.productionTip = false

Vue.use(VueSideBarMenu)
Vue.use(BootstrapVue)
Vue.use(IconsPlugin)
Vue.use(FlashMessage)

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
