import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    seriesList: [],
    currentSeries: null
  },
  mutations: {
    SET_SERIES_LIST(state, list) {
      state.seriesList = list
    },
    SET_CURRENT_SERIES(state, series) {
      state.currentSeries = series
    },
    ADD_SERIES(state, series) {
      state.seriesList.push(series)
    }
  },
  actions: {
    selectSeries({ commit }, series) {
      commit('SET_CURRENT_SERIES', series)
    },
    addSeries({ commit }, series) {
      commit('ADD_SERIES', series)
      commit('SET_CURRENT_SERIES', series)
    }
  },
  modules: {}
})