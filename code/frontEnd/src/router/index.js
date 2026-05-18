import Vue from 'vue'
import VueRouter from 'vue-router'
import Workspace from '../views/Workspace.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    redirect: '/workspace'
  },
  {
    path: '/workspace',
    name: 'Workspace',
    component: Workspace
  }
]

const router = new VueRouter({
  mode: 'hash',
  base: process.env.BASE_URL,
  routes
})

export default router