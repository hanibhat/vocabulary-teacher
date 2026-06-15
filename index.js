const VOCABULARY_ENDPOINT = 'https://vocabulary-teacher.onrender.com/vocabulary'
const VOCABULARY_CACHE_STORAGE_KEY = 'vocabularyCache'
const ALL_CATEGORIES = '__all__'

function vocabularyApp() {
  return {
    query: '',
    randomCount: 10,
    selectedCategory: ALL_CATEGORIES,
    loading: false,
    error: '',
    settingsOpen: false,
    hasActiveShuffle: false,
    allCategories: [],
    allEntries: [],
    entries: [],

    init() {
      this.loadVocabulary()
    },

    get categoryEntries() {
      if (this.selectedCategory === ALL_CATEGORIES) {
        return this.allEntries
      }

      return this.allEntries.filter((entry) => entry.category === this.selectedCategory)
    },

    get filteredEntries() {
      const needle = this.normalizeText(this.query)

      if (!needle) {
        return this.entries
      }

      return this.entries.filter((entry) => {
        return this.normalizeText(entry.source).includes(needle)
      })
    },

    get availableEntryCount() {
      return this.categoryEntries.length
    },

    async loadVocabulary({ bypassCache = false } = {}) {
      this.error = ''
      this.loading = true

      const cachedVocabulary = bypassCache ? null : this.getCachedVocabulary()
      if (cachedVocabulary) {
        this.applyVocabulary(cachedVocabulary.data)
        this.loading = false
        return
      }

      try {
        const response = await fetch(VOCABULARY_ENDPOINT)

        if (!response.ok) {
          throw new Error(`Server antwortet mit ${response.status}`)
        }

        const vocabulary = await response.json()
        this.applyVocabulary(vocabulary)
        if (this.hasVocabularyContent(vocabulary)) {
          this.cacheVocabulary(vocabulary)
        } else {
          localStorage.removeItem(VOCABULARY_CACHE_STORAGE_KEY)
        }
      } catch (error) {
        this.clearVocabulary()
        this.error = `Vokabeln konnten nicht geladen werden. ${error.message}`
      } finally {
        this.loading = false
      }
    },

    refreshVocabulary() {
      localStorage.removeItem(VOCABULARY_CACHE_STORAGE_KEY)
      return this.loadVocabulary({ bypassCache: true })
    },

    getCachedVocabulary() {
      const rawCache = localStorage.getItem(VOCABULARY_CACHE_STORAGE_KEY)

      if (!rawCache) {
        return null
      }

      try {
        const cache = JSON.parse(rawCache)
        const expiresAt = Number(cache.expiresAt)

        if (!cache.data || !Number.isFinite(expiresAt) || Date.now() >= expiresAt) {
          localStorage.removeItem(VOCABULARY_CACHE_STORAGE_KEY)
          return null
        }

        return cache
      } catch (error) {
        localStorage.removeItem(VOCABULARY_CACHE_STORAGE_KEY)
        return null
      }
    },

    cacheVocabulary(vocabulary) {
      const expiresAt = this.getNextMidnightTimestamp()

      localStorage.setItem(
        VOCABULARY_CACHE_STORAGE_KEY,
        JSON.stringify({
          data: vocabulary,
          expiresAt,
        })
      )
    },

    hasVocabularyContent(vocabulary) {
      return Object.values(vocabulary || {}).some((entries) => {
        return Array.isArray(entries) && entries.length > 0
      })
    },

    getNextMidnightTimestamp() {
      const nextMidnight = new Date()
      nextMidnight.setHours(24, 0, 0, 0)
      return nextMidnight.getTime()
    },

    applyVocabulary(vocabulary) {
      const categories = Object.entries(vocabulary || {}).map(([name, entries], categoryIndex) => {
        return {
          id: this.createCategoryId(categoryIndex),
          name,
          entries: (Array.isArray(entries) ? entries : []).map((entry, index) => ({
            id: this.createEntryId(categoryIndex, index),
            category: name,
            source: entry.source || '',
            translation: entry.translation || '',
            sourceExample: entry.sourceExample || '',
            translationExample: entry.translationExample || '',
          })),
        }
      })

      this.allCategories = categories.filter((category) => category.entries.length)
      this.allEntries = this.allCategories.flatMap((category) => category.entries)
      this.selectedCategory = ALL_CATEGORIES
      this.entries = this.categoryEntries
      this.hasActiveShuffle = false
      this.query = ''
    },

    clearVocabulary() {
      this.allCategories = []
      this.allEntries = []
      this.entries = []
      this.selectedCategory = ALL_CATEGORIES
      this.hasActiveShuffle = false
    },

    selectCategory() {
      this.error = ''
      this.query = ''
      this.entries = this.categoryEntries
      this.hasActiveShuffle = false
    },

    chooseRandomEntries() {
      const count = Number.parseInt(this.randomCount, 10)

      if (!Number.isFinite(count) || count < 1) {
        this.error = 'Gib eine Zahl größer als 0 ein.'
        return
      }

      this.error = ''
      this.query = ''
      const availableEntries = this.categoryEntries
      this.entries = this.shuffleEntries(availableEntries).slice(0, Math.min(count, availableEntries.length))
      this.hasActiveShuffle = true
      this.settingsOpen = false
    },

    resetEntries() {
      this.error = ''
      this.query = ''
      this.entries = this.categoryEntries
      this.hasActiveShuffle = false
    },

    shuffleEntries(entries) {
      const shuffled = [...entries]

      for (let index = shuffled.length - 1; index > 0; index -= 1) {
        const randomIndex = Math.floor(Math.random() * (index + 1))
        const temp = shuffled[index]
        shuffled[index] = shuffled[randomIndex]
        shuffled[randomIndex] = temp
      }

      return shuffled
    },

    normalizeText(value) {
      return String(value || '').toLowerCase()
    },

    createCategoryId(index) {
      return `category-${index}`
    },

    createEntryId(categoryIndex, entryIndex) {
      return `entry-${categoryIndex}-${entryIndex}`
    },
  }
}
