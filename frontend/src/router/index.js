import Vue from 'vue'
import VueRouter from 'vue-router'

Vue.use(VueRouter)

import Layout from '@/layout'

export const constantRoutes = [
  {
    path: '/login',
    component: () => import('@/views/login/index'),
    hidden: true
  },
  {
    path: '/register',
    component: () => import('@/views/register/index'),
    hidden: true
  },

  {
    path: '/404',
    component: () => import('@/views/404'),
    hidden: true
  },

  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [{
      path: 'dashboard',
      name: 'Dashboard',
      component: () => import('@/views/dashboard/index'),
      meta: { title: 'Dashboard', icon: 'dashboard' }
    }]
  },
]

/**
 * asyncRoutes
 * the routes that need to be dynamically loaded based on user roles
 */
export const asyncRoutes = [
  {
    path: '/commissioning',
    component: Layout,
    redirect: '/commissioning/phasescan',
    name: 'Commissioning',
    meta: {
      title: 'Commissioning',
      icon: 'nested'
    },
    children: [
      {
        path: 'phasescan',
        component: () => import('@/views/commissioning/phasescan/index'), // Parent router-view
        name: 'Phasescan',
        meta: { title: 'Phasescan', roles: ['admin', 'user'] },
      },
      {
        path: 'cavity-epeak',
        component: () => import('@/views/commissioning/cavity-epeak/index'), // Parent router-view
        name: 'Cavity Epeak',
        meta: { title: 'Cavity Epeak', roles: ['admin', 'user'] },
      },
	  {
		path: 'lattice',
        component: () => import('@/views/commissioning/lattice/index'), // Parent router-view
        name: 'Lattice',
        meta: { title: 'Lattice', roles: ['admin', 'user'] },
	  },
	  {
		path: 'orbitcorrection',
        component: () => import('@/views/commissioning/orbitcorrection/index'), // Parent router-view
        name: 'Orbit Correction',
        meta: { title: 'Orbit Correction', roles: ['admin', 'user'] },
	  },
	  {
        path: 'snapshot',
        component: () => import('@/views/commissioning/snapshot/index'), // Parent router-view
        name: 'Snapshot',
        meta: { title: 'Snapshot', roles: ['admin', 'user'] },
      },
	  {
        path: 'hebt-match',
        component: () => import('@/views/commissioning/hebt-match/index'), // Parent router-view
        name: 'HEBT match',
        meta: { title: 'HEBT match', roles: ['admin', 'user'] },
      },
	  {
        path: 'sequencer',
        component: () => import('@/views/commissioning/cafe-sequencer/index'), // Parent router-view
        name: 'Sequencer',
        meta: { title: 'HEBT match', roles: ['admin', 'user'] },
      },
	  {
        path: 'magnet-validation',
        component: () => import('@/views/commissioning/magnet-validation/index'), // Parent router-view
        name: 'Magnet Validation',
        meta: { title: 'Magnet Validation', roles: ['admin', 'user'] },
      },
	  {
        path: 'manual',
        component: () => import('@/views/commissioning/manual/index'), // Parent router-view
        name: 'Manual',
        meta: { title: 'Manual', roles: ['admin', 'user'] },
      },	
	  
    ]
  },

  {
    path: 'external-link',
    component: Layout,
    children: [
      {
        path: 'https://panjiachen.github.io/vue-element-admin-site/#/',
        meta: { title: 'External Link', icon: 'link' }
      }
    ]
  },

  // 404 page must be placed at the end !!!
  { path: '*', redirect: '/404', hidden: true }
]

const createRouter = () => new VueRouter({
  mode: 'history',
  scrollBehavior: () => ({ y: 0 }),
  routes: constantRoutes
})

const router = createRouter()

// Detail see: https://github.com/vuejs/vue-router/issues/1234#issuecomment-357941465
export function resetRouter() {
  const newRouter = createRouter()
  router.matcher = newRouter.matcher // reset router
}

export default router
//const routes = [
//  {
//    path: '/',
//    name: 'Home',
//    component: Home
//  },
//  {
//    path: '/about',
//    name: 'About',
//    // route level code-splitting
//    // this generates a separate chunk (about.[hash].js) for this route
//    // which is lazy-loaded when the route is visited.
//    component: () => import(/* webpackChunkName: "about" */ '../views/About.vue')
//  }
//]
//
//const router = new VueRouter({
//  mode: 'history',
//  base: process.env.BASE_URL,
//  routes
//})
//
//export default router
