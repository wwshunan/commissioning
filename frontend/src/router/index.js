import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '../views/Home.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    children: [
      {
        path: '/lattice/setting',
        name: 'LatticeSetting',
        component: () => import( '../views/Lattice.vue')
      },
      {
        path: '/log/check',
        name: 'LatticeCheck',
        component: () => import( '../views/LatticeCheck.vue')
      },
      {
        path: '/log/beam-time',
        name: 'UsageTime',
        component: () => import( '../views/UsageTime.vue')
      },	
      {
        path: '/commissioning/sequencer',
        name: 'UsageTime',
        component: () => import( '../views/Sequencer.vue')
      },		  
    ]
  },
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router
